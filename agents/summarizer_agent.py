from __future__ import annotations

from typing import Tuple

from ..schemas import InstagramFindings, WebsiteFindings, ClubBrief
from .llm_utils import call_openai_json


SYSTEM_PROMPT = (
    "Merge InstagramFindings + WebsiteFindings into ClubBrief: "
    "{overview, mission_values[], what_they_look_for[], sample_events[], keywords[], what_matters_most[5]}"
)


async def run(results: Tuple[InstagramFindings, WebsiteFindings]) -> ClubBrief:
    ig, web = results

    user_prompt = (
        "InstagramFindings:\n" + ig.json(indent=2) + "\n\n" +
        "WebsiteFindings:\n" + web.json(indent=2) + "\n\n" +
        "Fuse to a concise ClubBrief."
    )

    data = call_openai_json(SYSTEM_PROMPT, user_prompt)
    if data:
        try:
            # Ensure exactly 5 items in what_matters_most if possible
            wmm = data.get("what_matters_most", [])
            if len(wmm) > 5:
                data["what_matters_most"] = wmm[:5]
            elif len(wmm) < 5:
                data["what_matters_most"] = wmm + ["impact", "initiative", "teamwork", "quality", "fit"][: 5 - len(wmm)]
            return ClubBrief(**data)
        except Exception:
            pass

    # Fallback deterministic merge
    keywords = list({*(ig.keywords or []), *(web.keywords or [])})
    overview = "A student organization with public outreach and events."
    mission_values = (web.mission_values or [])[:3]
    what_they_look_for = [
        "Demonstrated initiative",
        "Interest in the club's domain",
        "Team collaboration",
    ]
    sample_events = (web.events or [])[:5]
    what_matters_most = [
        "commitment",
        "relevant experience",
        "teamwork",
        "communication",
        "fit with mission",
    ]

    return ClubBrief(
        overview=overview,
        mission_values=mission_values,
        what_they_look_for=what_they_look_for,
        sample_events=sample_events,
        keywords=keywords,
        what_matters_most=what_matters_most,
    )

