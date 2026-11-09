"""
Regression and Verification Tests for Gemini Model Selection, Propagation,
Discovery, 404 Handling, and Connection Diagnostics in KLEIN AI.
"""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import config
from agents.llm_utils import (
    call_gemini,
    verify_gemini_connection,
    discover_available_models,
)
from agents.orchestrator import ResearchOrchestrator
from agents.tools import ToolRegistry
from agents.planner import plan_research


def test_default_and_alternative_models():
    """Verify that gemini-3.8-flash is default and gemini-3.5-flash-lite is the supported alternative."""
    assert config.DEFAULT_GEMINI_MODEL == "gemini-3.8-flash"
    assert config.ALTERNATIVE_GEMINI_MODEL == "gemini-3.5-flash-lite"
    assert "gemini-3.8-flash" in config.SUPPORTED_GEMINI_MODELS
    assert "gemini-3.5-flash-lite" in config.SUPPORTED_GEMINI_MODELS

    # Ensure no stale 2.5 models exist in the supported models list
    for m in config.SUPPORTED_GEMINI_MODELS:
        assert "2.5" not in m, f"Deprecated model found in catalog: {m}"


def test_stale_model_sanitization(monkeypatch):
    """Verify that any stale 2.5 model in environment is automatically sanitized to DEFAULT_GEMINI_MODEL."""
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    assert config.get_gemini_model() == "gemini-3.8-flash"


def test_model_propagation_through_orchestrator_and_tools():
    """Verify chosen model propagates to orchestrator, tools, and agent workflows."""
    test_model = "gemini-3.5-flash-lite"
    orch = ResearchOrchestrator(model=test_model)
    assert orch.model == test_model
    assert orch.tools.model == test_model

    tools = ToolRegistry(model=test_model)
    assert tools.model == test_model


def test_discover_available_models_filters_text_generation():
    """Verify discover_available_models queries client.models.list() and filters text models."""
    mock_m1 = MagicMock()
    mock_m1.name = "models/gemini-3.8-flash"
    mock_m1.supported_actions = ["generateContent"]

    mock_m2 = MagicMock()
    mock_m2.name = "models/gemini-3.5-flash-lite"
    mock_m2.supported_actions = ["generateContent"]

    mock_m3 = MagicMock()
    mock_m3.name = "models/text-embedding-004"
    mock_m3.supported_actions = ["embedContent"]

    mock_m4 = MagicMock()
    mock_m4.name = "models/gemini-2.5-flash"
    mock_m4.supported_actions = ["generateContent"]

    mock_client = MagicMock()
    mock_client.models.list.return_value = [mock_m1, mock_m2, mock_m3, mock_m4]

    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        discovered = discover_available_models(api_key="mock_test_key_12345")

    assert "gemini-3.8-flash" in discovered
    assert "gemini-3.5-flash-lite" in discovered
    assert "text-embedding-004" not in discovered
    assert "gemini-2.5-flash" not in discovered  # 2.5 excluded
    # Preferred model is ordered first
    assert discovered[0] == "gemini-3.8-flash"


def test_verify_gemini_connection_success():
    """Verify connection succeeds only when real generate_content returns text."""
    mock_resp = MagicMock()
    mock_resp.text = "READY"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        ok, msg = verify_gemini_connection("mock_key_valid_123", model="gemini-3.8-flash")

    assert ok is True
    assert "gemini-3.8-flash" in msg
    assert "successfully" in msg


def test_verify_gemini_connection_404_handling():
    """Verify graceful 404 handling that identifies unavailable model and offers tested alternative without mutating choice."""
    def mock_generate(model, contents, **kwargs):
        if "2.5" in model:
            raise Exception("404 NOT_FOUND: This model models/gemini-2.5-flash is no longer available to new users.")
        # Working alternative
        resp = MagicMock()
        resp.text = "READY"
        return resp

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = mock_generate

    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        ok, msg = verify_gemini_connection("mock_key_valid_123", model="gemini-2.5-flash")

    assert ok is False
    assert "404" in msg
    assert "no longer available" in msg
    assert "gemini-3.8-flash" in msg or "gemini-3.5-flash-lite" in msg
    assert "Please select" in msg


def test_call_gemini_404_error_raises_without_silent_fallback():
    """Verify call_gemini raises descriptive 404 error and does not silently fall back to deprecated 2.5 models."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("404 NOT_FOUND: Model not found.")

    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        with pytest.raises(RuntimeError) as exc_info:
            call_gemini("Test prompt", api_key="mock_key_123", model="gemini-custom-model")

    err = str(exc_info.value)
    assert "404" in err
    assert "Suggested working alternative" in err


def test_connection_diagnostics_various_errors():
    """Verify diagnostics for missing key, invalid key, 403 permission, and 429 quota."""
    # 1. Missing key
    ok, msg = verify_gemini_connection("")
    assert ok is False
    assert "missing" in msg.lower()

    # 2. Invalid key (400)
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API_KEY_INVALID: Google rejected the key.")
    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        ok, msg = verify_gemini_connection("mock_invalid_key")
        assert ok is False
        assert "Invalid API key" in msg

    # 3. Permission denied (403)
    mock_client.models.generate_content.side_effect = Exception("403 PERMISSION_DENIED: Generative Language API not enabled.")
    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        ok, msg = verify_gemini_connection("mock_key_noperm")
        assert ok is False
        assert "Permission denied" in msg

    # 4. Quota exceeded (429)
    mock_client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED: Rate limit reached.")
    with patch("agents.llm_utils.genai.Client", return_value=mock_client):
        ok, msg = verify_gemini_connection("mock_key_quota")
        assert ok is False
        assert "Quota exceeded" in msg


def test_model_propagation_to_planner():
    """Verify model parameter propagates down to call_gemini in plan_research."""
    with patch("agents.planner.call_gemini", return_value='{"academic_title": "Test Plan", "search_queries": ["q1", "q2", "q3", "q4"]}') as mock_call:
        with patch("config.is_gemini_available", return_value=True):
            plan_research("Quantum Computing", depth="Quick", gemini_key="mock_key", model="gemini-3.5-flash-lite")
            assert mock_call.called
            _, kwargs = mock_call.call_args
            assert kwargs.get("model") == "gemini-3.5-flash-lite"
