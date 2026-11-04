"""
Shared LLM utility for Klein AI agent modules.
Handles google-genai Client calls, model fallbacks, temperature settings, and JSON extraction.
"""
import json
import re
import logging
from typing import Optional, Any
from google import genai
from google.genai import types
import config

logger = logging.getLogger("KleinAI.LLM")

FALLBACK_MODELS = [
    config.GEMINI_MODEL,
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
]


def call_gemini(
    prompt: str,
    api_key: Optional[str] = None,
    system_instruction: Optional[str] = None,
    temperature: float = 0.25,
) -> str:
    """Invokes Gemini using official google-genai SDK."""
    key = api_key or config.GEMINI_API_KEY
    if not key:
        raise ValueError("Gemini API key is not configured.")

    client = genai.Client(api_key=key)
    last_err = None

    for m_name in FALLBACK_MODELS:
        try:
            cfg = types.GenerateContentConfig(temperature=temperature)
            if system_instruction:
                cfg.system_instruction = system_instruction

            resp = client.models.generate_content(
                model=m_name,
                contents=prompt,
                config=cfg,
            )
            if resp and resp.text:
                return resp.text.strip()
        except Exception as e:
            logger.warning(f"Error on model {m_name}: {e}. Retrying fallback model...")
            last_err = e

    raise RuntimeError(f"All Gemini models failed: {last_err}")


def extract_json_from_text(text: str) -> Optional[Any]:
    """Extracts JSON structure from text or markdown code blocks."""
    if not text:
        return None
    try:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        clean = match.group(1) if match else text
        return json.loads(clean.strip())
    except Exception:
        return None
