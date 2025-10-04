from __future__ import annotations

from typing import List, Optional, Any
from pydantic import BaseModel, Field


class InputSpec(BaseModel):
    clubName: str = Field(..., description="Club name")
    schoolName: str = Field(..., description="School name")
    instagramUrl: Optional[str] = Field(None, description="Public Instagram URL")
    websiteUrl: Optional[str] = Field(None, description="Club website URL")
    resumePath: str = Field(..., description="Local PDF resume path")
    applicationQuestions: Optional[List[str]] = Field(
        default=None, description="Optional list of application questions"
    )
    isOnline: bool = Field(
        default=True,
        description="If True, fetch live content (Instagram/Website). If False, run heuristics only.",
    )


class InstagramFindings(BaseModel):
    mission_signals: List[str] = []
    recurring_events: List[str] = []
    recent_highlights: List[str] = []
    tone: Optional[str] = None
    notable_people: List[str] = []
    keywords: List[str] = []
    warnings: List[str] = []


class WebsiteFindings(BaseModel):
    about: Optional[str] = None
    mission_values: List[str] = []
    how_to_join: Optional[str] = None
    events: List[str] = []
    criteria: List[str] = []
    links: List[str] = []
    keywords: List[str] = []
    warnings: List[str] = []


class ClubBrief(BaseModel):
    overview: str
    mission_values: List[str]
    what_they_look_for: List[str]
    sample_events: List[str]
    keywords: List[str]
    what_matters_most: List[str] = Field(
        ..., description="Top 5 items that matter most"
    )


class ResumeSuggestions(BaseModel):
    top5_fixes: List[str]
    tailored_bullets: List[str]
    format_warnings: List[str]
    ATS_suggestions: List[str]


class ApplicationSuggestions(BaseModel):
    club_rundown: str
    values_alignment: List[dict]
    question_strategies: List[dict]


class InterviewPrep(BaseModel):
    similar_experiences_summary: str
    likely_questions: List[str]
    stories_to_prepare: List[str]
    quick_pitch_template: str
    followup_questions: List[str]
    links: List[str]


class FinalReport(BaseModel):
    input: InputSpec
    instagram: InstagramFindings
    website: WebsiteFindings
    brief: ClubBrief
    resume: ResumeSuggestions
    application: ApplicationSuggestions
    interview: InterviewPrep
    version: str = Field(default="0.1.0")
    timestamp: Optional[str] = None


def model_to_dict(model: Any) -> dict:
    # Support Pydantic v1 and v2
    if hasattr(model, "dict"):
        return model.dict()
    if hasattr(model, "model_dump"):
        return model.model_dump()
    raise TypeError("Unsupported model type")

