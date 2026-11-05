"""
Shared LLM utility for KLEIN AI agent modules.
Handles google-genai Client calls, model selection, temperature settings, and JSON extraction.
"""
import json
import re
import logging
from typing import Optional, Any, Tuple
from google import genai
from google.genai import types
import config

logger = logging.getLogger("KleinAI.LLM")


def call_gemini(
    prompt: str,
    api_key: Optional[str] = None,
    system_instruction: Optional[str] = None,
    temperature: float = 0.25,
    model: Optional[str] = None,
) -> str:
    """Invokes Gemini using official google-genai SDK with the specified or configured model."""
    key = api_key or config.GEMINI_API_KEY
    if not key:
        raise ValueError("Gemini API key is not configured.")

    client = genai.Client(api_key=key)
    selected_model = model or config.GEMINI_MODEL

    # Dynamically ordered models starting with the user's selected model
    models_to_try = [selected_model]
    for fallback in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    last_err = None

    for m_name in models_to_try:
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
            # Sanitize exception message to ensure API key is never exposed
            err_msg = str(e)
            if key and key in err_msg:
                err_msg = err_msg.replace(key, "[REDACTED_API_KEY]")
            logger.warning(f"Error on model {m_name}: {err_msg}")
            last_err = err_msg
            # Fast fail on credential failure rather than hammering fallbacks
            if "API_KEY" in err_msg or "PERMISSION_DENIED" in err_msg or "INVALID_ARGUMENT" in err_msg:
                break

    raise RuntimeError(f"All Gemini models failed: {last_err}")


def verify_gemini_connection(api_key: str, model: Optional[str] = None) -> Tuple[bool, str]:
    """Tests live Gemini connectivity with a minimal ping without leaking credentials."""
    if not api_key or len(api_key.strip()) < 5:
        return False, "Gemini API key is missing or too short."
    try:
        target_model = model or config.GEMINI_MODEL
        client = genai.Client(api_key=api_key.strip())
        resp = client.models.generate_content(
            model=target_model,
            contents="Respond with the single word 'READY'.",
        )
        if resp and resp.text:
            return True, f"Connected to {target_model} successfully."
        return False, "Empty response received from Gemini."
    except Exception as e:
        err_str = str(e)
        if api_key in err_str:
            err_str = err_str.replace(api_key, "[REDACTED]")
        if "API_KEY_INVALID" in err_str or "400" in err_str:
            return False, "Invalid API key: Google rejected the credential."
        if "PERMISSION_DENIED" in err_str or "403" in err_str:
            return False, "Permission denied: Key lacks Generative Language API permissions."
        if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
            return False, "Quota exceeded: Rate limit or daily token quota reached."
        return False, f"Connection error: {err_str[:120]}"


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
