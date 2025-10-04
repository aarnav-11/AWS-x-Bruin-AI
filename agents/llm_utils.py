from __future__ import annotations

import json
import os
import re
from typing import Optional, Any, Dict


def _clean_json(text: str) -> str:
    # Extract the first {...} block heuristically
    if text.strip().startswith("{") and text.strip().endswith("}"):
        return text.strip()
    # Try to find a JSON object in the text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    cleaned = _clean_json(text)
    try:
        return json.loads(cleaned)
    except Exception:
        # Basic fixes: remove trailing commas
        fixed = re.sub(r",\s*([}\]])", r"\1", cleaned)
        try:
            return json.loads(fixed)
        except Exception:
            return None


def call_openai_json(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except Exception:
        return None

    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content
        if not content:
            return None
        return try_parse_json(content)
    except Exception:
        return None

