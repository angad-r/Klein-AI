"""
Test Suite for KLEIN AI Foundation Repairs & Integrity Verification.
Covers:
1. Gemini API connectivity verification (missing, invalid keys)
2. Tavily API connectivity verification (missing, invalid keys)
3. Web search failure handling & zero source fabrication prevention
4. Empty search results handling & citation integrity
5. Source deduplication & domain normalization
6. Citation integrity audit coverage calculation
7. 17-Section PDF generation integrity
8. 12-Slide PowerPoint generation integrity
9. SQLite session persistence and round-trip retrieval
10. Model selection propagation in orchestrator
11. Secure .env persistence
"""
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import config
from agents.llm_utils import verify_gemini_connection
from research.search import verify_tavily_connection, deduplicate_sources
from research.citation_validator import validate_citations_and_sources
from agents.orchestrator import ResearchOrchestrator
from database.db import init_db, save_session, get_session_by_id
from generators.pdf_generator import generate_pdf
from generators.ppt_generator import generate_presentation
from pptx import Presentation


def test_gemini_verification_missing_key():
    ok, msg = verify_gemini_connection("")
    assert ok is False
    assert "missing" in msg.lower()


def test_gemini_verification_invalid_key():
    ok, msg = verify_gemini_connection("AIzaSyINVALID_KEY_TESTING_12345")
    assert ok is False
    # Verify raw key is NOT printed in the error message for security
    assert "AIzaSyINVALID_KEY_TESTING_12345" not in msg


def test_tavily_verification_missing_key():
    ok, msg = verify_tavily_connection("")
    assert ok is False
    assert "missing" in msg.lower()


def test_tavily_verification_invalid_key():
    ok, msg = verify_tavily_connection("tvly-INVALID_TAVILY_KEY_99999")
    assert ok is False
    # Verify raw key is NOT printed in the error message
    assert "tvly-INVALID_TAVILY_KEY_99999" not in msg


def test_search_failure_prevents_fabrication():
    """Verify that when web search yields 0 sources, orchestrator NEVER fabricates fake arXiv/IEEE papers."""
    orch = ResearchOrchestrator(depth="Quick")
    # Simulate complete search outage or 0 results
    orch.tools.search_web = lambda q, **kwargs: []

    report = orch.run_pipeline("Theoretical Graph Isomorphism Complexity")

    # Critical assertions:
    assert report["search_failed"] is True
    assert "search_warning" in report
    assert report["sources_count"] == 0
    assert report["sources"] == []
    assert report["evidence_items"] == []
    assert report["references"] == []
    assert "10.1145" not in report.get("literature_review", "")
    assert "arXiv:230" not in report.get("literature_review", "")


def test_empty_sources_citation_validator():
    """Verify citation validator safely handles zero collected sources."""
    audit = validate_citations_and_sources([], "Some literature review text.")
    assert audit["total_sources_collected"] == 0
    assert audit["total_sources_cited"] == 0
    assert audit["integrity_status"] == "NO_SOURCES_COLLECTED"


def test_source_deduplication_and_normalization():
    sources = [
        {"title": "Paper 1", "url": "https://arxiv.org/abs/2401.0001?utm_campaign=share", "snippet": "Text A"},
        {"title": "Paper 1 Duplicate", "url": "https://arxiv.org/abs/2401.0001", "snippet": "Text B"},
        {"title": "Paper 2", "url": "https://nature.com/articles/s41586", "snippet": "Text C"},
    ]
    deduped = deduplicate_sources(sources)
    assert len(deduped) == 2
    assert deduped[0]["domain"] == "arxiv.org"
    assert deduped[1]["domain"] == "nature.com"


def test_citation_integrity_verification():
    sources = [
        {"title": "Quantum Computing Basics", "url": "https://ibm.com/quantum", "accessible": True},
        {"title": "Superconducting Qubits", "url": "https://nature.com/articles/qc", "accessible": True},
    ]
    review_both = "Fundamental physics are described in [1], whereas gate fidelities appear in [2]."
    audit = validate_citations_and_sources(sources, review_both)
    assert audit["total_sources_collected"] == 2
    assert audit["total_sources_cited"] == 2
    assert audit["citation_coverage_percent"] == 100.0

    review_one = "Only fundamental physics are described in [1]."
    audit_one = validate_citations_and_sources(sources, review_one)
    assert audit_one["total_sources_cited"] == 1
    assert audit_one["citation_coverage_percent"] == 50.0
    uncited = [c for c in audit_one["all_citations"] if not c["cited_in_review"]]
    assert len(uncited) == 1


def test_pdf_generation_integrity():
    sample_report = {
        "topic": "Edge AI Inference",
        "title": "Empirical Benchmark of Edge AI Inference",
        "keywords": ["Edge AI", "Quantization", "Embedded Systems"],
        "abstract": "This study analyzes low-power tensor processing units.",
        "introduction": "Deploying transformers on microcontroller units requires extreme compression.",
        "scope_and_motivation": "Evaluating 4-bit INT quantization.",
        "problem_statement": "Memory bandwidth constraints throttle transformer decoders.",
        "objectives": ["Measure latency", "Evaluate energy consumption"],
        "research_questions": ["RQ1: What is the energy tradeoff?"],
        "subtopics": ["Quantization", "Model Pruning"],
        "search_queries": ["edge ai quantization latency"],
        "sources": [{
            "title": "Edge Benchmark Paper",
            "url": "https://example.org/edge",
            "accessible": True,
            "source_type": "Conference",
            "credibility_tier": "High Authority",
            "authority_score": 0.9,
            "published_date": "2024",
        }],
        "sources_count": 1,
        "source_summaries": [{"source_index": 1, "title": "Edge Benchmark Paper", "key_finding": "3x speedup", "limitations": "FPGA only"}],
        "comparative_analysis": ["INT4 achieves 3x speedup over FP16"],
        "consensus_points": ["Quantization-aware training preserves accuracy"],
        "conflicting_evidence": ["Post-training quantization degradation variance"],
        "evidence_items": [{
            "citation_index": 1,
            "claim": "INT4 achieves 3x speedup.",
            "source_title": "Edge Benchmark Paper",
            "source_url": "https://example.org/edge",
            "evidence": "3.1x faster token generation observed on Cortex-M55.",
            "publication_date": "2024",
            "confidence": "Supported",
        }],
        "literature_review": "Quantization foundations were established in [1].",
        "research_gaps": [{
            "gap_id": "GAP-01",
            "gap_title": "Lack of Real-Time Edge Telemetry",
            "explanation": "Existing benchmarks measure desktop GPUs.",
            "supporting_sources": ["[1] Edge Benchmark Paper"],
            "why_it_matters": "Obscures battery drain in wearable devices.",
            "suggested_research_question": "How to profile milliwatt-level inference continuously?",
            "possible_methodology": "Hardware current-shunt measurement rig.",
            "feasibility": "High",
        }],
        "methodology": {
            "framework_name": "EdgeQuant-Bench",
            "research_design": "Empirical hardware profiling",
            "research_approach": "Empirical Measurement",
            "hypotheses": ["H1: INT4 reduces wattage by 60% with <1% perplexity drop."],
            "dataset_requirements": "TinyStories dataset",
            "data_collection_methods": "Keysight oscilloscope logging",
            "variables": {
                "independent_variables": ["Quantization bitwidth"],
                "dependent_variables": ["Power consumption (mW)", "Inference latency (ms)"],
            },
            "workflow_stages": ["Quantization", "Flash deployment", "Power logging"],
        },
        "proposed_experiments": [{
            "experiment_id": "EXP-01",
            "name": "Microcontroller Latency Benchmark",
            "hypothesis": "Sub-10ms per token generation on ARM Cortex-M55.",
            "target_datasets": "TinyStories test split",
            "baseline_models": "PyTorch Mobile FP32",
            "evaluation_metrics": "Latency (ms/token), SRAM footprint (KB)",
            "validation_status": "Proposed Protocol (Pending Execution)",
        }],
        "expected_contributions": ["Open-source embedded telemetry suite"],
        "limitations": ["Limited to ARM architectures"],
        "conclusion": "Sub-byte quantization enables autonomous edge inference.",
        "references": [{
            "index": 1,
            "title": "Edge Benchmark Paper",
            "url": "https://example.org/edge",
            "accessible": True,
            "published_date": "2024",
            "citation_format": "[1] Edge Benchmark Paper. Available: https://example.org/edge",
        }],
        "depth": "Standard",
        "is_demo_mode": False,
    }

    pdf_path = generate_pdf(sample_report)
    assert os.path.exists(pdf_path)
    assert pdf_path.endswith(".pdf")
    assert os.path.getsize(pdf_path) > 1000


def test_pptx_generation_integrity():
    sample_report = {
        "topic": "Edge AI Inference",
        "title": "Empirical Benchmark of Edge AI Inference",
        "abstract": "This study analyzes low-power tensor processing units.",
        "introduction": "Deploying transformers on microcontroller units.",
        "problem_statement": "Memory bandwidth constraints throttle decoders.",
        "objectives": ["Measure latency", "Evaluate energy consumption"],
        "research_questions": ["RQ1: What is the energy tradeoff?"],
        "subtopics": ["Quantization", "Model Pruning"],
        "search_queries": ["edge ai quantization latency"],
        "comparative_analysis": ["INT4 achieves 3x speedup"],
        "consensus_points": ["Quantization preserves accuracy"],
        "conflicting_evidence": ["Variance across models"],
        "research_gaps": [{"gap_title": "Lack of Edge Telemetry", "feasibility": "High"}],
        "methodology": {
            "research_design": "Empirical benchmarking",
            "research_approach": "Empirical",
            "hypotheses": ["H1: INT4 reduces wattage."],
            "workflow_stages": ["Stage 1", "Stage 2"],
        },
        "proposed_experiments": [{"name": "Microcontroller Benchmark", "baseline_models": "PyTorch Mobile"}],
        "expected_contributions": ["Open-source telemetry suite"],
        "limitations": ["ARM only"],
        "references": [{"index": 1, "title": "Edge Benchmark", "url": "https://example.org"}],
    }

    ppt_path = generate_presentation(sample_report)
    assert os.path.exists(ppt_path)
    prs = Presentation(ppt_path)
    assert len(prs.slides) == 12


def test_sqlite_persistence():
    init_db()
    test_report = {
        "topic": "Federated Learning Privacy",
        "title": "Differential Privacy in Federated Learning",
        "sources_count": 3,
        "is_demo_mode": False,
        "abstract": "Testing SQLite persistence.",
        "research_gaps": [],
        "references": [],
    }
    sess_id = save_session(test_report, depth="Comprehensive", pdf_path="test.pdf", pptx_path="test.pptx")
    assert sess_id > 0

    record = get_session_by_id(sess_id)
    assert record is not None
    assert record["topic"] == "Federated Learning Privacy"
    assert record["depth"] == "Comprehensive"


def test_model_selection_propagation():
    orch = ResearchOrchestrator(model="gemini-1.5-pro")
    assert orch.model == "gemini-1.5-pro"


def test_save_api_keys_to_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_env_path = Path(tmpdir) / ".env"
        orig_env_file = config.ENV_FILE
        try:
            config.ENV_FILE = test_env_path
            saved = config.save_api_keys_to_env("test_gem_key_123", "test_tav_key_456")
            assert saved is True
            assert test_env_path.exists()
            content = test_env_path.read_text(encoding="utf-8")
            assert "test_gem_key_123" in content
            assert "test_tav_key_456" in content
        finally:
            config.ENV_FILE = orig_env_file
