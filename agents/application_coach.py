from __future__ import annotations

import json
from typing import List, Optional

from ..schemas import ClubBrief, ApplicationSuggestions, model_to_dict
from .llm_utils import call_openai_json


SYSTEM_PROMPT = (
    "You craft strategies for application forms. Return JSON: {club_rundown, "
    "values_alignment[{value, how_to_show_it}], question_strategies[{question, structure, do_donts[], example_answer≤150 words}]}"
)


async def run(brief: ClubBrief, questions: Optional[List[str]]) -> ApplicationSuggestions:
    print(f"[ApplicationCoachAgent] start questions_count={(len(questions) if questions else 0)}")
    user_prompt = (
        "ClubBrief:\n" + json.dumps(model_to_dict(brief), indent=2) + "\n\n"
        + "Application questions (if any):\n" + ("\n".join(questions or []) or "(none provided)") + "\n\n"
        + "Keep examples concise (≤150 words)."
    )

    print("[ApplicationCoachAgent] calling LLM for strategies...")
    data = call_openai_json(SYSTEM_PROMPT, user_prompt)
    if data:
        try:
            return ApplicationSuggestions(**data)
        except Exception:
            print("[ApplicationCoachAgent] LLM JSON parse failed, using fallback")

    # Fallback
    values_alignment = [
        {"value": v, "how_to_show_it": "Show measurable impact, teamwork, and initiative in relevant stories."}
        for v in (brief.mission_values or [])[:3]
    ]
    qs = questions or [
        "Why this club?",
        "Describe a relevant project.",
    ]
    question_strategies = []
    for q in qs:
        question_strategies.append(
            {
                "question": q,
                "structure": "Context → Action → Result → Reflection",
                "do_donts": ["Do quantify", "Do align with what_matters_most", "Don't be generic"],
                "example_answer": "I joined X to tackle Y. I led Z action, resulting in A% improvement. This taught me B, which aligns with C."
            }
        )

    print("[ApplicationCoachAgent] using heuristic fallback")
    return ApplicationSuggestions(
        club_rundown=brief.overview,
        values_alignment=values_alignment,
        question_strategies=question_strategies,
    )
