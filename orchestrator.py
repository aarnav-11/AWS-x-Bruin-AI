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
from .agents import instagram_agent, website_agent, summarizer_agent, resume_tailor, application_coach, interview_coach


try:
    from strands.multiagent import swarm  # type: ignore
except Exception:
    async def swarm(tasks):  # type: ignore
        return await asyncio.gather(*tasks)


async def run_clubapply(input_data: InputSpec) -> FinalReport:
    ig_task = instagram_agent.run(input_data.instagramUrl, is_online=input_data.isOnline)
    web_task = website_agent.run(input_data.websiteUrl, is_online=input_data.isOnline)

    ig_res: Optional[InstagramFindings]
    web_res: Optional[WebsiteFindings]

    ig_res, web_res = await swarm([ig_task, web_task])

    summary = await summarizer_agent.run((ig_res, web_res))

    resume = await resume_tailor.run(
        summary, input_data.resumePath, input_data.clubName, input_data.schoolName
    )
    application = await application_coach.run(summary, input_data.applicationQuestions)
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
    return report

