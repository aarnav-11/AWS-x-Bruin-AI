from __future__ import annotations

import json
import os
import re
from typing import Optional, Any, Dict


def _clean_json(text: str) -> str:
    if text is None:
        return ""
    t = text.strip()
    if t.startswith("{") and t.endswith("}"):
        return t
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        return t[start : end + 1]
    return t


def try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    cleaned = _clean_json(text)
    try:
        return json.loads(cleaned)
    except Exception:
        fixed = re.sub(r",\s*([}\]])", r"\1", cleaned)
        try:
            return json.loads(fixed)
        except Exception:
            return None


def _call_openai_json(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
    except Exception:
        return None
    mdl = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    print(f"[LLM] OpenAI call model={mdl} sys_chars={len(system_prompt)} user_chars={len(user_prompt)}")
    client = OpenAI(api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model=mdl,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content
        if not content:
            return None
        print(f"[LLM] OpenAI response chars={len(content)}")
        return try_parse_json(content)
    except Exception:
        print("[LLM] OpenAI call failed", flush=True)
        return None


def _call_gemini_json(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    try:
        import google.generativeai as genai
    except Exception:
        return None
    try:
        genai.configure(api_key=key)
        mdl = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        print(f"[LLM] Gemini call model={mdl} sys_chars={len(system_prompt)} user_chars={len(user_prompt)}")
        prompt = (
            "System:\n" + system_prompt + "\n\n" +
            "User:\n" + user_prompt + "\n\n" +
            "Return ONLY valid JSON."
        )
        m = genai.GenerativeModel(mdl)
        resp = m.generate_content(prompt)
        text = getattr(resp, "text", None)
        if text:
            print(f"[LLM] Gemini response chars={len(text)}")
            return try_parse_json(text)
        try:
            cand = resp.candidates[0]
            parts = getattr(cand, "content", None).parts if hasattr(cand, "content") else []
            combined = "\n".join(getattr(p, "text", "") for p in parts)
            print(f"[LLM] Gemini response (combined parts) chars={len(combined)}")
            return try_parse_json(combined)
        except Exception:
            return None
    except Exception:
        print("[LLM] Gemini call failed", flush=True)
        return None


def call_llm_json(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    provider = (os.getenv("LLM_PROVIDER") or "").lower().strip()
    if provider in {"gemini", "google"}:
        print("[LLM] Provider forced: gemini")
        return _call_gemini_json(system_prompt, user_prompt, model=model)
    if provider in {"bedrock", "aws"}:
        print("[LLM] Provider forced: bedrock")
        return _call_bedrock_json(system_prompt, user_prompt, model=model)
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        print("[LLM] Provider auto: gemini (key present)")
        return _call_gemini_json(system_prompt, user_prompt, model=model)
    if os.getenv("OPENAI_API_KEY"):
        print("[LLM] Provider auto: openai (key present)")
        return _call_openai_json(system_prompt, user_prompt, model=model)
    # Try AWS Bedrock via default credential chain
    if os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE"):
        print("[LLM] Provider auto: bedrock (aws creds present)")
        return _call_bedrock_json(system_prompt, user_prompt, model=model)
    print("[LLM] No provider available; returning None")
    return None


# Backward compatibility for existing imports
def call_openai_json(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return call_llm_json(system_prompt, user_prompt, model=model)


def _call_bedrock_json(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Call AWS Bedrock (Anthropic Claude) and return parsed JSON.

    Tries a sequence of candidate model IDs to handle throttling or unavailability.
    Requires AWS credentials (env, profile, or instance role) and region.
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except Exception:
        print("[LLM] boto3 not installed for Bedrock")
        return None

    region = (
        os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
        or "us-east-1"
    )

    # Build list of candidate models: env override > passed model > defaults
    env_primary = os.getenv("BEDROCK_MODEL_ID")
    env_candidates = [m.strip() for m in (os.getenv("BEDROCK_MODEL_CANDIDATES") or "").split(",") if m.strip()]
    defaults = [
        # Claude 3.5 Sonnet
        "anthropic.claude-3-5-sonnet-20240620-v1:0",
        # Claude 3.5 Haiku (example; adjust if your region uses a different suffix)
        "anthropic.claude-3-5-haiku-20241022-v1:0",
        # Claude 3 Haiku
        "anthropic.claude-3-haiku-20240307-v1:0",
    ]
    candidates = []
    for m in [model, env_primary, *env_candidates, *defaults]:
        if m and m not in candidates:
            candidates.append(m)

    anthropic_version = os.getenv("ANTHROPIC_VERSION", "bedrock-2023-05-31")

    client = boto3.client("bedrock-runtime", region_name=region)

    last_err = None
    for idx, model_id in enumerate(candidates, start=1):
        print(f"[LLM] Bedrock attempt {idx}/{len(candidates)} model={model_id} region={region} sys_chars={len(system_prompt)} user_chars={len(user_prompt)}")
        try:
            body = {
                "anthropic_version": anthropic_version,
                "system": system_prompt + "\nReturn ONLY valid JSON.",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt}
                        ],
                    }
                ],
                "max_tokens": 1024,
                "temperature": 0.2,
            }
            response = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
            raw = response.get("body")
            text_content = None
            if raw is not None:
                data = json.loads(raw.read().decode("utf-8"))
                parts = []
                for item in data.get("content", []) or []:
                    t = item.get("text")
                    if t:
                        parts.append(t)
                text_content = "\n".join(parts)
            if not text_content:
                print("[LLM] Bedrock empty response content; trying next model")
                last_err = "empty_response"
                continue
            print(f"[LLM] Bedrock response chars={len(text_content)}")
            parsed = try_parse_json(text_content)
            if parsed is not None:
                return parsed
            print("[LLM] Bedrock JSON parse failed; trying next model")
            last_err = "json_parse_failed"
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            msg = e.response.get("Error", {}).get("Message")
            print(f"[LLM] Bedrock ClientError code={code} msg={msg}; trying next model")
            last_err = code or str(e)
            # On throttling or other errors, just try next candidate
            continue
        except Exception as e:
            print(f"[LLM] Bedrock call failed: {e}; trying next model")
            last_err = str(e)
            continue

    print(f"[LLM] Bedrock exhausted candidates; last_err={last_err}")
    return None
