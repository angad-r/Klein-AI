"""
Shared LLM utility for KLEIN AI agent modules.
Handles google-genai Client calls, model selection, temperature settings, and JSON extraction.
"""
import json
import re
import time
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Optional, Any, Tuple, List, Callable
from google import genai
from google.genai import types
import config

logger = logging.getLogger("KleinAI.LLM")

__all__ = [
    "discover_available_models",
    "call_gemini",
    "verify_gemini_connection",
    "extract_json_from_text",
    "get_llm_usage_stats",
    "reset_llm_usage_stats",
    "LLM_USAGE_STATS",
]

# Telemetry tracking for LLM API calls
LLM_USAGE_STATS = {
    "total_calls": 0,
    "successful_calls": 0,
    "failed_calls": 0,
    "total_prompt_chars": 0,
    "total_completion_chars": 0,
    "models_used": {},
}


def get_llm_usage_stats() -> dict:
    """Returns copy of accumulated LLM API usage metrics."""
    return dict(LLM_USAGE_STATS)


def reset_llm_usage_stats() -> None:
    """Resets accumulated LLM usage metrics."""
    global LLM_USAGE_STATS
    LLM_USAGE_STATS = {
        "total_calls": 0,
        "successful_calls": 0,
        "failed_calls": 0,
        "total_prompt_chars": 0,
        "total_completion_chars": 0,
        "models_used": {},
    }


def discover_available_models(api_key: Optional[str] = None) -> List[str]:
    """
    Discovers available Gemini models using client.models.list(),
    filtering for models supporting text generation.
    Returns normalized model IDs without 'models/' prefix.
    Appearance in the list is NOT proof of access; models must be verified.
    """
    key = api_key or config.get_gemini_api_key()
    if not key or len(key.strip()) < 5:
        return list(config.SUPPORTED_GEMINI_MODELS)

    try:
        client = genai.Client(api_key=key.strip())
        discovered = []
        for m in client.models.list():
            # Check if model supports text generation
            actions = getattr(m, "supported_actions", None) or []
            if actions and "generateContent" not in actions:
                continue

            raw_name = getattr(m, "name", "") or ""
            name = raw_name[7:] if raw_name.startswith("models/") else raw_name

            # Keep only text generation gemini models, excluding embeddings/imagen/aqa/vision-only
            if name.startswith("gemini-") and not any(x in name for x in ["embedding", "imagen", "aqa", "recontext", "vision"]):
                # Exclude deprecated 2.5 models
                if "2.5" not in name and name not in discovered:
                    discovered.append(name)

        if discovered:
            # Order with preferred models first
            preferred = [config.DEFAULT_GEMINI_MODEL, config.ALTERNATIVE_GEMINI_MODEL, "gemini-1.5-flash", "gemini-1.5-pro"]
            ordered = [p for p in preferred if p in discovered]
            ordered.extend([d for d in discovered if d not in ordered])
            return ordered
    except Exception as e:
        err_msg = str(e)
        if key in err_msg:
            err_msg = err_msg.replace(key, "[REDACTED]")
        logger.warning(f"Gemini model discovery error: {err_msg}")

    return list(config.SUPPORTED_GEMINI_MODELS)


def call_gemini(
    prompt: str,
    api_key: Optional[str] = None,
    system_instruction: Optional[str] = None,
    temperature: float = 0.25,
    model: Optional[str] = None,
) -> str:
    """
    Invokes Gemini using official google-genai SDK with the specified working model.
    Never silently falls back to deprecated Gemini 2.5 models.
    """
    key = api_key or config.get_gemini_api_key()
    if not key:
        raise ValueError("Gemini API key is not configured.")

    client = genai.Client(api_key=key.strip())
    selected_model = model or config.get_gemini_model()

    # Sanitize any deprecated 2.5 model request
    if "2.5" in selected_model:
        selected_model = config.DEFAULT_GEMINI_MODEL

    LLM_USAGE_STATS["total_calls"] += 1
    LLM_USAGE_STATS["total_prompt_chars"] += len(prompt)

    try:
        cfg = types.GenerateContentConfig(temperature=temperature)
        if system_instruction:
            cfg.system_instruction = system_instruction

        resp = client.models.generate_content(
            model=selected_model,
            contents=prompt,
            config=cfg,
        )
        if resp and resp.text:
            result_text = resp.text.strip()
            LLM_USAGE_STATS["successful_calls"] += 1
            LLM_USAGE_STATS["total_completion_chars"] += len(result_text)
            LLM_USAGE_STATS["models_used"][selected_model] = LLM_USAGE_STATS["models_used"].get(selected_model, 0) + 1
            return result_text
        raise RuntimeError(f"Model '{selected_model}' returned an empty completion.")

    except Exception as e:
        err_msg = str(e)
        if key and key in err_msg:
            err_msg = err_msg.replace(key, "[REDACTED_API_KEY]")
        logger.warning(f"Error executing Gemini request on {selected_model}: {err_msg}")
        LLM_USAGE_STATS["failed_calls"] += 1

        # Check for model 404 / deprecation error
        if "404" in err_msg or "NOT_FOUND" in err_msg or "not found" in err_msg.lower() or "no longer available" in err_msg.lower():
            raise RuntimeError(
                f"Model '{selected_model}' is no longer available (404 NOT_FOUND). "
                f"Suggested working alternative: '{config.ALTERNATIVE_GEMINI_MODEL}' or '{config.DEFAULT_GEMINI_MODEL}'. "
                f"Please switch the model in the sidebar."
            )

        raise RuntimeError(f"Gemini API call on model '{selected_model}' failed: {err_msg}")


def verify_gemini_connection(
    api_key: str,
    model: Optional[str] = None,
    timeout: Optional[float] = None,
    status_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[bool, str]:
    """
    Verifies live Gemini connectivity with an optimized generate_content request.
    Does not assume model access from listing alone.
    Uses minimal verification prompt, max_output_tokens=20, thinking_level=LOW,
    explicit HTTP timeouts (20-30s), bounded retries (at most 1 retry for transient network errors),
    and streaming status messages.
    """
    start_time = time.perf_counter()
    timeout_val = float(timeout if timeout is not None else getattr(config, "GEMINI_VERIFICATION_TIMEOUT_SECONDS", 25.0))

    def report_status(status_text: str) -> None:
        if status_callback:
            try:
                status_callback(status_text)
            except Exception:
                pass

    if not api_key or len(api_key.strip()) < 5:
        elapsed = time.perf_counter() - start_time
        report_status("Authentication failed.")
        return False, f"Authentication failed: Gemini API key is missing or too short. (Elapsed: {elapsed:.2f}s)"

    clean_key = api_key.strip()
    target_model = model or config.get_gemini_model()

    report_status("Connecting...")

    # Build client with explicit HTTP timeout
    http_timeout_ms = max(int(timeout_val * 1000), 1000)
    try:
        client = genai.Client(
            api_key=clean_key,
            http_options=types.HttpOptions(timeout=http_timeout_ms),
        )
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        err_msg = str(e).replace(clean_key, "[REDACTED]")
        report_status("Authentication failed.")
        return False, f"Authentication failed: Client initialization error: {err_msg} (Elapsed: {elapsed:.2f}s)"

    # Build optimized GenerateContentConfig: max_output_tokens=20 and thinking_level=LOW
    try:
        gen_cfg = types.GenerateContentConfig(
            max_output_tokens=20,
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
        )
    except Exception:
        gen_cfg = types.GenerateContentConfig(max_output_tokens=20)

    prompt = "Reply with exactly: KLEIN AI CONNECTED"

    max_attempts = 2  # 1 initial attempt + at most 1 retry for transient errors
    for attempt in range(max_attempts):
        report_status("Sending verification request...")

        try:
            # Enforce hard request execution timeout via ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    client.models.generate_content,
                    model=target_model,
                    contents=prompt,
                    config=gen_cfg,
                )
                resp = future.result(timeout=timeout_val)

            if resp and resp.text:
                elapsed = time.perf_counter() - start_time
                report_status("Connected successfully.")
                return True, f"Connected successfully to {target_model} (Elapsed: {elapsed:.2f}s)."

            elapsed = time.perf_counter() - start_time
            return False, f"Empty response received from {target_model} (Elapsed: {elapsed:.2f}s)."

        except (FuturesTimeoutError, TimeoutError) as e:
            if attempt < max_attempts - 1:
                logger.warning("Verification request timed out. Retrying once...")
                time.sleep(1.0)
                continue
            elapsed = time.perf_counter() - start_time
            report_status("Timed out.")
            return False, f"Timed out: Verification request exceeded {timeout_val:.0f}s limit (Elapsed: {elapsed:.2f}s)."

        except Exception as e:
            err_str = str(e)
            if clean_key in err_str:
                err_str = err_str.replace(clean_key, "[REDACTED]")

            # 1. Model unavailable / 404 (Non-transient: Fast fail, never retry)
            if any(x in err_str for x in ["404", "NOT_FOUND"]) or "not found" in err_str.lower() or "no longer available" in err_str.lower():
                elapsed = time.perf_counter() - start_time
                report_status("Model unavailable.")
                return False, (
                    f"Model unavailable: Model '{target_model}' is no longer available (404 NOT_FOUND). "
                    f"Suggested alternative: '{config.ALTERNATIVE_GEMINI_MODEL}' or '{config.DEFAULT_GEMINI_MODEL}'. "
                    f"Please select '{config.ALTERNATIVE_GEMINI_MODEL}' in the model selector. (Elapsed: {elapsed:.2f}s)"
                )

            # 2. Authentication failure (Non-transient: Fast fail, never retry)
            if any(x in err_str for x in ["API_KEY_INVALID", "INVALID_ARGUMENT", "400", "401"]) or "invalid api key" in err_str.lower() or "api key not valid" in err_str.lower():
                elapsed = time.perf_counter() - start_time
                report_status("Authentication failed.")
                return False, f"Authentication failed: Invalid API key: Google rejected the credential. (Elapsed: {elapsed:.2f}s)"

            if "403" in err_str or "PERMISSION_DENIED" in err_str:
                elapsed = time.perf_counter() - start_time
                report_status("Authentication failed.")
                return False, f"Authentication failed: Permission denied: Key lacks Generative Language API permissions. (Elapsed: {elapsed:.2f}s)"

            # 3. Quota exhausted (Non-transient: Fast fail, never retry)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                elapsed = time.perf_counter() - start_time
                return False, f"Quota exceeded: Rate limit or daily token quota reached. (Elapsed: {elapsed:.2f}s)"

            # 4. Timeout error strings (Transient: retry once)
            is_timeout_str = "timed out" in err_str.lower() or "timeout" in err_str.lower() or "504" in err_str or "408" in err_str
            if is_timeout_str:
                if attempt < max_attempts - 1:
                    logger.warning(f"Verification request timed out ({err_str[:60]}). Retrying once...")
                    time.sleep(1.0)
                    continue
                elapsed = time.perf_counter() - start_time
                report_status("Timed out.")
                return False, f"Timed out: Verification request timed out (Elapsed: {elapsed:.2f}s)."

            # 5. Transient connection / network / 5xx error (Retry once)
            is_transient_net = any(t in err_str.lower() for t in ["connection reset", "remotedisconnected", "connection error", "500", "502", "503", "socket"])
            if is_transient_net and attempt < max_attempts - 1:
                logger.warning(f"Transient error on {target_model} ({err_str[:60]}). Retrying once...")
                time.sleep(1.0)
                continue

            # Otherwise, terminal error
            elapsed = time.perf_counter() - start_time
            return False, f"Connection error on model '{target_model}': {err_str[:120]} (Elapsed: {elapsed:.2f}s)"

    elapsed = time.perf_counter() - start_time
    report_status("Timed out.")
    return False, f"Timed out: Verification request exceeded limit after retry (Elapsed: {elapsed:.2f}s)."


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
