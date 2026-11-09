"""
Tests for optimized Gemini connection verification:
- Minimal verification prompt
- Token limit (max_output_tokens=20)
- Thinking level set to LOW
- Bounded retries (at most 1 retry for transient network errors, never indefinitely)
- Fast-fail on auth errors (400/401/403) and 404 model unavailable
- Explicit timeouts and elapsed time tracking
- Safe key redaction
- Status callback streaming
"""
import pytest
from unittest.mock import MagicMock, patch
from concurrent.futures import TimeoutError as FuturesTimeoutError
from google.genai import types
import config
from agents.llm_utils import verify_gemini_connection


def test_gemini_verification_success():
    """Verify successful verification sets prompt, max_tokens=20, thinking_level=LOW, and records elapsed time."""
    mock_resp = MagicMock()
    mock_resp.text = "KLEIN AI CONNECTED"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    status_events = []
    def on_status(msg):
        status_events.append(msg)

    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        ok, msg = verify_gemini_connection(
            "AIzaSyValidMockKeyForTesting12345",
            model="gemini-3.8-flash",
            status_callback=on_status,
        )

    assert ok is True
    assert "Connected successfully" in msg
    assert "gemini-3.8-flash" in msg
    assert "Elapsed:" in msg
    assert "Connecting..." in status_events
    assert "Sending verification request..." in status_events
    assert "Connected successfully." in status_events

    # Verify generate_content call arguments
    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert call_kwargs.get("contents") == "Reply with exactly: KLEIN AI CONNECTED"
    gen_cfg = call_kwargs.get("config")
    assert gen_cfg is not None
    assert gen_cfg.max_output_tokens == 20
    assert gen_cfg.thinking_config.thinking_level == types.ThinkingLevel.LOW


def test_gemini_verification_transient_retry_success():
    """Verify that a transient network failure triggers at most one retry and succeeds on the second attempt."""
    mock_resp = MagicMock()
    mock_resp.text = "KLEIN AI CONNECTED"

    mock_client = MagicMock()
    # First attempt fails with transient connection error, second attempt succeeds
    mock_client.models.generate_content.side_effect = [
        ConnectionError("connection reset by peer"),
        mock_resp,
    ]

    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        with patch("time.sleep", return_value=None):
            ok, msg = verify_gemini_connection(
                "AIzaSyValidMockKeyForTesting12345",
                model="gemini-3.8-flash",
            )

    assert ok is True
    assert "Connected successfully" in msg
    assert mock_client.models.generate_content.call_count == 2


def test_gemini_verification_transient_retry_exhausted():
    """Verify that repeated transient failures stop after 1 retry (max 2 total attempts) and never retry indefinitely."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = ConnectionError("503 Service Unavailable: connection reset")

    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        with patch("time.sleep", return_value=None):
            ok, msg = verify_gemini_connection(
                "AIzaSyValidMockKeyForTesting12345",
                model="gemini-3.8-flash",
            )

    assert ok is False
    assert mock_client.models.generate_content.call_count == 2
    assert "Connection error" in msg or "Timed out" in msg


def test_gemini_verification_timeout_handling():
    """Verify that request timeout returns clear 'Timed out.' status without hanging."""
    status_events = []
    def on_status(msg):
        status_events.append(msg)

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = FuturesTimeoutError("Request timed out")

    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        with patch("time.sleep", return_value=None):
            ok, msg = verify_gemini_connection(
                "AIzaSyValidMockKeyForTesting12345",
                model="gemini-3.8-flash",
                timeout=0.01,
                status_callback=on_status,
            )

    assert ok is False
    assert "Timed out" in msg
    assert "Timed out." in status_events
    assert "Elapsed:" in msg


def test_gemini_verification_auth_failure_fast_fail():
    """Verify authentication errors (API_KEY_INVALID, 400, 401, 403) fail fast with 0 retries."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("400 INVALID_ARGUMENT: API_KEY_INVALID")

    status_events = []
    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        ok, msg = verify_gemini_connection(
            "AIzaSyInvalidKeyTest12345",
            model="gemini-3.8-flash",
            status_callback=lambda m: status_events.append(m),
        )

    assert ok is False
    assert "Authentication failed" in msg
    assert "Authentication failed." in status_events
    # Zero retries: must execute exactly once
    assert mock_client.models.generate_content.call_count == 1


def test_gemini_verification_model_404_fast_fail():
    """Verify 404 model not found fails fast with 0 retries and suggests working alternative."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("404 NOT_FOUND: Model models/gemini-custom is no longer available.")

    status_events = []
    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        ok, msg = verify_gemini_connection(
            "AIzaSyValidMockKeyForTesting12345",
            model="gemini-custom",
            status_callback=lambda m: status_events.append(m),
        )

    assert ok is False
    assert "Model unavailable" in msg
    assert "Model unavailable." in status_events
    assert "404" in msg
    assert config.ALTERNATIVE_GEMINI_MODEL in msg
    # Zero retries: must execute exactly once
    assert mock_client.models.generate_content.call_count == 1


def test_gemini_verification_key_redaction():
    """Verify raw API key is never leaked in returned messages even when returned by exception string."""
    raw_key = "AIzaSySecretApiKeyDoNotExpose9999"
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception(f"HTTP 500 internal error with key {raw_key}")

    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        with patch("time.sleep", return_value=None):
            ok, msg = verify_gemini_connection(raw_key, model="gemini-3.8-flash")

    assert ok is False
    assert raw_key not in msg
    assert "[REDACTED]" in msg


def test_gemini_verification_missing_key():
    """Verify missing or too-short key immediately fails without making network calls."""
    ok, msg = verify_gemini_connection("")
    assert ok is False
    assert "Authentication failed" in msg
    assert "missing" in msg.lower() or "too short" in msg.lower()
