from __future__ import annotations

import json
from typing import Tuple

from ..schemas import InstagramFindings, WebsiteFindings, ClubBrief, model_to_dict
from .llm_utils import call_openai_json


SYSTEM_PROMPT = (
    "Merge InstagramFindings + WebsiteFindings into ClubBrief: "
    "{overview, mission_values[], what_they_look_for[], sample_events[], keywords[], what_matters_most[5]}"
)


async def run(results: Tuple[InstagramFindings, WebsiteFindings]) -> ClubBrief:
    print("[SummarizerAgent] start: merging IG + Web findings")
    ig, web = results

    user_prompt = (
        "InstagramFindings:\n" + json.dumps(model_to_dict(ig), indent=2) + "\n\n"
        + "WebsiteFindings:\n" + json.dumps(model_to_dict(web), indent=2) + "\n\n"
        + "Fuse to a concise ClubBrief."
    )

    print("[SummarizerAgent] calling LLM to fuse findings...")
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
            print("[SummarizerAgent] LLM JSON parse failed, using fallback")

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

    print("[SummarizerAgent] using heuristic fallback")
    return ClubBrief(
        overview=overview,
        mission_values=mission_values,
        what_they_look_for=what_they_look_for,
        sample_events=sample_events,
        keywords=keywords,
        what_matters_most=what_matters_most,
    )
