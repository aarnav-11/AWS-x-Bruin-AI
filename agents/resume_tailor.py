from __future__ import annotations

from typing import Optional

from ..schemas import ClubBrief, ResumeSuggestions
from ..tools.pdf_reader import read_pdf_text
from .llm_utils import call_openai_json


SYSTEM_PROMPT = (
    "You are a strict resume reviewer. Given ClubBrief and resume text, "
    "Return JSON: {top5_fixes[], tailored_bullets[], format_warnings[], ATS_suggestions[]}"
)


async def run(brief: ClubBrief, resume_path: str, club_name: Optional[str] = None, school_name: Optional[str] = None) -> ResumeSuggestions:
    resume_text = read_pdf_text(resume_path, max_pages=3)

    sys = SYSTEM_PROMPT.replace("You are a strict resume reviewer.", f"You are a strict resume reviewer for {club_name or 'the club'} at {school_name or 'the school'}.")
    user_prompt = (
        "ClubBrief:\n" + brief.json(indent=2) + "\n\n" +
        "Resume text (first pages):\n" + resume_text[:8000] + "\n\n" +
        "Provide concrete bullet suggestions tailored to the club's keywords and what_matters_most."
    )

    data = call_openai_json(sys, user_prompt)
    if data:
        try:
            # Ensure capped lengths
            data["top5_fixes"] = (data.get("top5_fixes") or [])[:5]
            data["tailored_bullets"] = (data.get("tailored_bullets") or [])[:8]
            return ResumeSuggestions(**data)
        except Exception:
            pass

    # Fallback
    bullets = []
    for kw in (brief.keywords or [])[:5]:
        bullets.append(f"Drove a {kw}-focused project delivering measurable outcomes (e.g., metrics, quality, time).")
    top5 = [
        "Quantify impact in each bullet (numbers, %).",
        "Front-load action verbs and outcomes.",
        "Prioritize club-relevant projects near top.",
        "Tighten formatting to one page (10–11pt).",
        "Ensure consistent tense and punctuation.",
    ]
    return ResumeSuggestions(
        top5_fixes=top5,
        tailored_bullets=bullets,
        format_warnings=["Check margins, alignment, and consistent section headers."],
        ATS_suggestions=["Use standard headings; avoid images/tables that break parsing."]
    )

