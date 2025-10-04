# ClubApply Strands

Multi-agent CLI using Strands Agents to help students apply to university clubs.

## Features
- Scrapes Instagram and website (1–2 layers).
- Fuses signals into a ClubBrief.
- Tailors resume suggestions to the club.
- Coaches application answers and interview prep.
- Outputs a structured JSON report to `clubapply_strands/out/`.

## Install

Python 3.11+

```
pip install "strands-agents[openai]" requests beautifulsoup4 pdfplumber pydantic
# Optional extras for semantic search:
# pip install chromadb sentence-transformers

# If using OpenAI models:
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini  # optional
```

## CLI Usage

```
python -m clubapply_strands.main \
  --club "Data Science Union" \
  --school "UCLA" \
  --instagram "https://instagram.com/ucla_dsu" \
  --website "https://dsu.ucla.edu" \
  --resume "./resume.pdf" \
  --questions '["Why DSU?", "What project would you lead?"]' \
  --online 
```

Add `--chat` to enter an interactive InterviewCoach session after the report is generated.

## Notes
- The code uses `strands.multiagent.swarm` if available; otherwise falls back to `asyncio.gather`.
- If `OPENAI_API_KEY` is unset, agents fall back to simple heuristics.
- Network failures are handled gracefully and recorded as warnings in the report.

