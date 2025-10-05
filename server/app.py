from __future__ import annotations

import os
import tempfile
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..schemas import (
    InputSpec,
    InstagramFindings,
    WebsiteFindings,
    ClubBrief,
    FinalReport,
    model_to_dict,
)
from ..agents import instagram_agent, website_agent, summarizer_agent, resume_tailor, application_coach, interview_coach
from ..orchestrator import run_clubapply
from ..agents.llm_utils import call_llm_json


app = FastAPI(title="ClubApply Strands API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/upload/resume")
async def upload_resume(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1] or ".pdf"
    fd, path = tempfile.mkstemp(prefix="resume_", suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"resume_path": path, "name": file.filename}


class InstagramReq(BaseModel):
    profile_url: str
    online: Optional[bool] = True


@app.post("/agents/instagram-analyzer")
async def instagram_analyzer(req: InstagramReq):
    res = await instagram_agent.run(req.profile_url, is_online=bool(req.online))
    return model_to_dict(res)


class WebsiteReq(BaseModel):
    website_url: str
    online: Optional[bool] = True


@app.post("/agents/website-analyzer")
async def website_analyzer(req: WebsiteReq):
    res = await website_agent.run(req.website_url, is_online=bool(req.online))
    return model_to_dict(res)


class SummarizerReq(BaseModel):
    instagram: Optional[Dict[str, Any]] = None
    website: Optional[Dict[str, Any]] = None
    content: Optional[str] = None


@app.post("/agents/summarizer")
async def summarizer(req: SummarizerReq):
    # If IG/Web provided, use the core summarizer_agent
    if req.instagram is not None and req.website is not None:
        ig = InstagramFindings(**req.instagram)
        web = WebsiteFindings(**req.website)
        brief = await summarizer_agent.run((ig, web))
        return model_to_dict(brief)
    # Otherwise, accept raw content and summarize via LLM
    if req.content:
        system = (
            "Summarize the content into: {overview, mission_values[], what_they_look_for[], "
            "sample_events[], keywords[], what_matters_most[5]} as JSON."
        )
        data = call_llm_json(system, req.content)
        if data:
            try:
                return ClubBrief(**data).dict()
            except Exception:
                pass
        # Fallback minimal brief
        return ClubBrief(
            overview=req.content[:400],
            mission_values=[],
            what_they_look_for=["initiative", "teamwork", "communication"],
            sample_events=[],
            keywords=[],
            what_matters_most=["commitment", "impact", "fit", "quality", "follow-through"],
        ).dict()
    return {"error": "Provide instagram+website or content"}


class ResumeTailorReq(BaseModel):
    resume_path: str
    job_description: Optional[str] = None
    club_name: Optional[str] = None
    school_name: Optional[str] = None


@app.post("/agents/resume-tailor")
async def resume_tailor_ep(req: ResumeTailorReq):
    # Build a lightweight brief from job description if provided
    if req.job_description:
        brief = ClubBrief(
            overview=req.job_description[:400],
            mission_values=[],
            what_they_look_for=["initiative", "relevant experience", "teamwork"],
            sample_events=[],
            keywords=[],
            what_matters_most=["commitment", "impact", "fit", "quality", "follow-through"],
        )
    else:
        brief = ClubBrief(
            overview="Tailored resume suggestions",
            mission_values=[],
            what_they_look_for=["initiative", "relevant experience", "teamwork"],
            sample_events=[],
            keywords=[],
            what_matters_most=["commitment", "impact", "fit", "quality", "follow-through"],
        )
    res = await resume_tailor.run(
        brief, req.resume_path, req.club_name or "Club", req.school_name or "School"
    )
    return model_to_dict(res)


class InterviewCoachReq(BaseModel):
    club_name: str
    school_name: str
    job_description: Optional[str] = None


@app.post("/agents/interview-coach")
async def interview_coach_ep(req: InterviewCoachReq):
    brief = ClubBrief(
        overview=req.job_description or f"Interview prep for {req.club_name} at {req.school_name}",
        mission_values=[],
        what_they_look_for=["initiative", "teamwork", "communication"],
        sample_events=[],
        keywords=[],
        what_matters_most=["commitment", "impact", "fit", "quality", "follow-through"],
    )
    res = await interview_coach.run(brief)
    return model_to_dict(res)


class ApplicationCoachReq(BaseModel):
    job_description: Optional[str] = None
    questions: Optional[List[str]] = None
    # Optional signals to enrich the brief
    website_url: Optional[str] = None
    instagram_url: Optional[str] = None
    # Optional resume path to tailor suggestions; if omitted, generic edits are returned
    resume_path: Optional[str] = None
    club_name: Optional[str] = None
    school_name: Optional[str] = None


@app.post("/agents/application-coach")
async def application_coach_ep(req: ApplicationCoachReq):
    # Try to enrich the brief using website/instagram if available
    web_findings: Optional[WebsiteFindings] = None
    ig_findings: Optional[InstagramFindings] = None

    # Heuristically parse a website URL from job_description if not explicitly provided
    website_url = req.website_url
    if not website_url and req.job_description:
        import re as _re
        m = _re.search(r"https?://[^\s]+", req.job_description)
        if m:
            website_url = m.group(0)

    if website_url:
        try:
            web_findings = await website_agent.run(website_url, is_online=True)
        except Exception:
            web_findings = None
    if req.instagram_url:
        try:
            ig_findings = await instagram_agent.run(req.instagram_url, is_online=True)
        except Exception:
            ig_findings = None

    if web_findings or ig_findings:
        # Use summarizer to create a better ClubBrief
        ig_model = ig_findings or InstagramFindings()
        web_model = web_findings or WebsiteFindings()
        brief = await summarizer_agent.run((ig_model, web_model))
    else:
        # Minimal brief from provided description
        brief = ClubBrief(
            overview=req.job_description or "Application strategies",
            mission_values=[],
            what_they_look_for=["initiative", "teamwork", "communication"],
            sample_events=[],
            keywords=[],
            what_matters_most=["commitment", "impact", "fit", "quality", "follow-through"],
        )

    # Application strategies
    app_suggestions = await application_coach.run(brief, req.questions or [])

    # Resume edits (generic if resume_path not supplied)
    resume_suggestions = await resume_tailor.run(
        brief,
        req.resume_path or "__NO_FILE__",
        req.club_name or "Club",
        req.school_name or "School",
    )

    # Compose response ensuring the three requested sections are explicit
    resp = {
        "club": {
            "overview": brief.overview,
            "mission_values": brief.mission_values,
            "what_matters_most": brief.what_matters_most,
        },
        "answers": [
            {
                "question": qs.get("question"),
                "structure": qs.get("structure"),
                "do_donts": qs.get("do_donts"),
                "example_answer": qs.get("example_answer"),
            }
            for qs in (app_suggestions.question_strategies or [])
        ],
        "resume": model_to_dict(resume_suggestions),
        # include original application suggestions for compatibility with existing UI
        "application": model_to_dict(app_suggestions),
        "brief": model_to_dict(brief),
    }
    return resp


@app.post("/clubapply/run")
async def clubapply_run(spec: InputSpec):
    report = await run_clubapply(spec)
    return model_to_dict(report)
