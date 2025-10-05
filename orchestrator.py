from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from .schemas import (
    InputSpec,
    FinalReport,
    InstagramFindings,
    WebsiteFindings,
)
from .agents import (
    instagram_agent,
    website_agent,
    summarizer_agent,
    resume_tailor,
    application_coach,
    interview_coach,
)


async def _run_swarm(tasks):
    """Robustly resolve Strands swarm across layouts, else fallback to asyncio.gather."""
    # Preferred: function export
    try:
        from strands.multiagent.swarm import swarm as s  # type: ignore
        if callable(s):
            return await s(tasks)
        if hasattr(s, "swarm") and callable(s.swarm):  # submodule exposing .swarm
            return await s.swarm(tasks)
    except Exception:
        pass
    # Alternative: module import then attribute
    try:
        from strands.multiagent import swarm as s2  # type: ignore
        if callable(s2):
            return await s2(tasks)
        if hasattr(s2, "swarm") and callable(s2.swarm):
            return await s2.swarm(tasks)
    except Exception:
        pass
    # Fallback: asyncio
    return await asyncio.gather(*tasks)


async def run_clubapply(input_data: InputSpec) -> FinalReport:
    print("[Orchestrator] Launching IG + Web tasks in parallel")
    ig_task = instagram_agent.run(input_data.instagramUrl, is_online=input_data.isOnline)
    web_task = website_agent.run(input_data.websiteUrl, is_online=input_data.isOnline)

    ig_res: Optional[InstagramFindings]
    web_res: Optional[WebsiteFindings]

    ig_res, web_res = await _run_swarm([ig_task, web_task])
    print("[Orchestrator] Received IG + Web outputs")

    print("[Orchestrator] Running summarizer agent")
    summary = await summarizer_agent.run((ig_res, web_res))

    print("[Orchestrator] Running resume tailor agent")
    resume = await resume_tailor.run(
        summary, input_data.resumePath, input_data.clubName, input_data.schoolName
    )
    print("[Orchestrator] Running application coach agent")
    application = await application_coach.run(summary, input_data.applicationQuestions)
    print("[Orchestrator] Running interview coach agent")
    interview = await interview_coach.run(summary)

    ts = datetime.utcnow().isoformat()
    report = FinalReport(
        input=input_data,
        instagram=ig_res,
        website=web_res,
        brief=summary,
        resume=resume,
        application=application,
        interview=interview,
        timestamp=ts,
    )
    print("[Orchestrator] Aggregation complete, returning FinalReport")
    return report
