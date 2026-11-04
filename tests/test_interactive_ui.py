"""
Automated UI, Widget, Button, and Interactive Element Testing Suite for Klein AI (ResearchMate AI).
Tests every interactive element, button response, state transition, and file export.
"""
import sys
import os
import json
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import config
from database.db import init_db, save_session, get_all_sessions, get_session_by_id, delete_session, clear_all_sessions
from agents.orchestrator import ResearchOrchestrator
from agents.planner import plan_research
from agents.tools import ToolRegistry
from research.citation_validator import validate_citations_and_sources
from generators.pdf_generator import generate_pdf
from generators.ppt_generator import generate_presentation
from generators.report_generator import generate_all_markdown_reports


@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure clean database for testing."""
    init_db()
    yield
    # Cleanup


def test_widget_keys_uniqueness_in_app():
    """Verify that every explicitly assigned widget key in app.py is unique."""
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    import re
    # Match patterns like key="xyz" or key='xyz'
    keys = re.findall(r'key=[\'"]([^\'"]+)[\'"]', content)
    # Check for duplicate static keys
    seen = set()
    duplicates = []
    for k in keys:
        if k in seen:
            duplicates.append(k)
        seen.add(k)

    assert not duplicates, f"Found duplicate widget keys in app.py: {duplicates}"


def test_button_start_research_empty_topic_validation():
    """Verify that empty research topic is properly caught and raises ValueError or warning."""
    orch = ResearchOrchestrator(depth="Quick")
    with pytest.raises(ValueError, match="cannot be empty"):
        orch.run_pipeline("   ")


def test_button_start_research_special_characters_and_multiline():
    """Verify that topics with HTML tags, quotes, and multiline inputs execute safely without crashing."""
    orch = ResearchOrchestrator(depth="Quick")
    tricky_topic = """<script>alert('xss')</script> "AI & Healthcare" -- Section 10:
Quantum & Biometric Vulnerabilities! @2026"""
    
    report = orch.run_pipeline(tricky_topic)
    assert report is not None
    assert "sources" in report
    assert len(report["sources"]) > 0
    assert "abstract" in report
    assert "methodology" in report


def test_button_start_research_very_long_topic():
    """Verify system stability when topic exceeds normal sentence length."""
    orch = ResearchOrchestrator(depth="Quick")
    long_topic = "Impact of Autonomous Artificial Intelligence Systems on Cybersecurity in Cloud Hospital Databases " * 5
    report = orch.run_pipeline(long_topic)
    assert report is not None
    assert report.get("sources_count", 0) > 0


def test_history_buttons_save_load_delete_clear():
    """Verify database CRUD buttons: Save Session, Load Session, Delete Session, and Clear All History."""
    clear_all_sessions()
    assert len(get_all_sessions()) == 0

    dummy_report = {
        "topic": "Neural Network Pruning",
        "title": "Autonomous Investigation into Neural Pruning",
        "sources_count": 5,
        "is_demo_mode": True,
        "research_gaps": [{"gap_id": "GAP-01", "gap_title": "Edge Pruning", "feasibility": "High"}],
        "references": [{"title": "Pruning 101", "url": "https://arxiv.org/abs/dummy"}]
    }

    # 1. Test Save Session
    sess_id = save_session(dummy_report, depth="Quick", pdf_path="dummy.pdf", pptx_path="dummy.pptx")
    assert sess_id > 0

    # 2. Test Get All Sessions
    all_sess = get_all_sessions()
    assert len(all_sess) == 1
    assert all_sess[0]["id"] == sess_id

    # 3. Test Get Session By ID (Load Session button action)
    loaded = get_session_by_id(sess_id)
    assert loaded is not None
    assert loaded["report_data"]["topic"] == "Neural Network Pruning"

    # 4. Test Delete Session button action
    delete_session(sess_id)
    assert len(get_all_sessions()) == 0

    # 5. Test Clear All Sessions button action with multiple entries
    save_session(dummy_report, depth="Quick")
    save_session(dummy_report, depth="Standard")
    assert len(get_all_sessions()) == 2
    clear_all_sessions()
    assert len(get_all_sessions()) == 0


def test_modular_button_refresh_plan():
    """Test button action: '🔄 Refresh Plan'."""
    topic = "Impact of AI on Cybersecurity in Healthcare"
    plan = plan_research(topic, depth="Standard")
    assert "objectives" in plan
    assert len(plan["objectives"]) >= 2
    assert "search_queries" in plan
    assert len(plan["search_queries"]) >= 3


def test_modular_button_resynthesize_literature():
    """Test button action: '🔄 Re-synthesize Review'."""
    tools = ToolRegistry()
    lit_input = {
        "topic": "AI in Medical Cybersecurity",
        "sources": [
            {"title": "Hospital IoT Security", "content": "Ransomware attacks increased 40% in healthcare.", "url": "https://nih.gov/test", "source_type": "Journal"}
        ],
        "analysis": {
            "source_summaries": ["Hospital IoT is vulnerable"],
            "comparative_analysis": [{"theme": "Vulnerabilities", "consensus": "High"}],
            "consensus_points": ["IoT needs zero trust"],
            "conflicting_evidence": []
        }
    }
    lit_text = tools.generate_literature_review(lit_input)
    assert isinstance(lit_text, str)
    assert len(lit_text) > 100
    assert "[Source 1]" in lit_text or "literature" in lit_text.lower()


def test_modular_button_reevaluate_gaps():
    """Test button action: '🔄 Re-evaluate Gaps'."""
    tools = ToolRegistry()
    gap_input = {
        "topic": "AI in Medical Cybersecurity",
        "analysis": {
            "comparative_analysis": [{"theme": "Scalability"}],
            "conflicting_evidence": ["High latency vs Low compute"]
        }
    }
    gaps = tools.identify_research_gaps(gap_input)
    assert isinstance(gaps, list)
    assert len(gaps) >= 1
    assert "gap_id" in gaps[0]


def test_modular_button_regenerate_methodology():
    """Test button action: '🔄 Re-synthesize Methodology'."""
    tools = ToolRegistry()
    meth_input = {
        "topic": "AI in Medical Cybersecurity",
        "gaps": [{"gap_id": "GAP-01", "gap_title": "Real-time edge latency"}]
    }
    meth = tools.propose_methodology(meth_input)
    assert isinstance(meth, dict)
    assert "framework_name" in meth
    assert "proposed_experiments" in meth
    assert len(meth["proposed_experiments"]) >= 1


def test_modular_button_revalidate_citations():
    """Test button action: '🛡️ Re-audit Citations'."""
    sources = [
        {"title": "Paper A", "url": "https://nih.gov/paper-a", "accessible": True},
        {"title": "Paper B", "url": "https://arxiv.org/abs/paper-b", "accessible": True}
    ]
    lit_text = "Recent findings by [Source 1] show intrusion detection accuracy, while [Source 2] highlights limits."
    audit = validate_citations_and_sources(sources=sources, literature_review_text=lit_text)
    assert "citation_coverage_percent" in audit
    assert audit["total_sources_collected"] == 2
    assert audit["total_sources_cited"] == 2


def test_download_buttons_file_integrity():
    """Verify that download button files (PDF, PPTX, MD suite, JSON session) are generated and non-empty."""
    orch = ResearchOrchestrator(depth="Quick")
    report = orch.run_pipeline("Cloud Computing Security")

    # 1. PDF Download Data
    pdf_path = generate_pdf(report)
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 1000
    with open(pdf_path, "rb") as f:
        header = f.read(4)
        assert header == b"%PDF", f"Invalid PDF header: {header}"

    # 2. PPTX Download Data
    pptx_path = generate_presentation(report)
    assert os.path.exists(pptx_path)
    assert os.path.getsize(pptx_path) > 1000
    with open(pptx_path, "rb") as f:
        header = f.read(4)
        assert header == b"PK\x03\x04", f"Invalid PPTX zip header: {header}"

    # 3. Markdown Dossier Suite Data
    md_files = generate_all_markdown_reports(report)
    assert len(md_files) == 5
    for key, path in md_files.items():
        assert os.path.exists(path), f"Missing markdown file for {key}"
        assert os.path.getsize(path) > 50, f"Empty markdown file for {key}"

    # 4. JSON Session Export Data
    json_str = json.dumps(report, indent=2)
    assert len(json_str) > 500
    parsed = json.loads(json_str)
    assert parsed["topic"] == "Cloud Computing Security"
    assert "methodology" in parsed
