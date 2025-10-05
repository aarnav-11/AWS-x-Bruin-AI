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
pip install "strands-agents[openai]" requests beautifulsoup4 pdfplumber pydantic google-generativeai
# Optional extras for semantic search:
# pip install chromadb sentence-transformers

# If using OpenAI models:
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini  # optional

# If using Gemini models:
export GEMINI_API_KEY=your_gemini_api_key   # or GOOGLE_API_KEY
export GEMINI_MODEL=gemini-1.5-flash        # optional
export LLM_PROVIDER=gemini                  # forces Gemini over OpenAI

# If using AWS Bedrock (Claude 3.5 Sonnet)
export AWS_DEFAULT_REGION=us-east-1
# Use either env vars or an AWS profile with proper Bedrock permissions
# Optional override model ID (check availability in your region):
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
export LLM_PROVIDER=bedrock
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
- Uses `strands.multiagent.swarm` when available; otherwise falls back to `asyncio.gather`.
- If no API key is present, agents fall back to simple heuristics.
- Provider is selected via `LLM_PROVIDER` (gemini/openai) or auto-detected by available keys.

### Common Import Error (ModuleNotFoundError)
If you see `ModuleNotFoundError: No module named 'clubapply_strands'`, run from the parent folder of the package or install in editable mode:
- `cd ~/Desktop` then `python3 -m clubapply_strands --club ...`
- or `pip install -e .` then use `clubapply-strands --club ...`
