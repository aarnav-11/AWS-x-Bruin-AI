from __future__ import annotations

from typing import Optional

from ..schemas import InstagramFindings
from ..tools.fetch_url import fetch_html, extract_visible_text
from .llm_utils import call_openai_json


SYSTEM_PROMPT = (
    "You extract public, high-signal info from a club’s Instagram HTML.\n"
    "Return JSON: {mission_signals[], recurring_events[], recent_highlights[], tone, "
    "notable_people[], keywords[], warnings[]}"
)


async def run(instagram_url: Optional[str], is_online: bool = True) -> InstagramFindings:
    print(f"[InstagramAgent] start url={instagram_url} online={is_online}")
    if not instagram_url:
        return InstagramFindings(warnings=["No Instagram URL provided."])

    html = ""
    if is_online:
        print("[InstagramAgent] fetching HTML...")
        html = fetch_html(instagram_url)
    text = extract_visible_text(html) if html else ""

    user_prompt = (
        f"URL: {instagram_url}\n\n"
        f"HTML/Text (truncated):\n{text[:6000]}\n\n"
        "Focus on mission signals, recruiting hints, and events."
    )

    print("[InstagramAgent] calling LLM for JSON parse...")
    data = call_openai_json(SYSTEM_PROMPT, user_prompt)
    if data:
        try:
            return InstagramFindings(**data)
        except Exception:
            print("[InstagramAgent] LLM JSON parse failed, using fallback")

    # Heuristic fallback
    print("[InstagramAgent] using heuristic fallback")
    mission_signals = []
    keywords = []
    warnings = []
    if "FETCH_ERROR" in html:
        warnings.append("Failed to fetch Instagram page.")
    if text:
        tl = text.lower()
        if any(k in tl for k in ["apply", "recruit", "join", "deadline"]):
            mission_signals.append("Recruiting or application-related posts detected.")
        if "board" in tl or "officer" in tl:
            keywords.append("leadership")
        if "workshop" in tl or "info session" in tl or "infosession" in tl:
            keywords.append("workshops")

    return InstagramFindings(
        mission_signals=mission_signals or [
            "Public-facing community updates and event promotions"
        ],
        recurring_events=[],
        recent_highlights=[],
        tone="student club; community-oriented",
        notable_people=[],
        keywords=list(set(keywords)),
        warnings=warnings,
    )
