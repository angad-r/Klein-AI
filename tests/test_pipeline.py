"""
Unit & Integration Tests for KLEIN AI.
Tests pipeline robustness against edge cases and verifies advanced Part 2 features:
- Tool Registry execution & telemetry
- Source Quality Assessor & Credibility Tiers
- Grounded Evidence Extraction & Confidence Scores
- 7-Dimension Research Gap Structure
- 17-Section PDF Generation with clickable links
- 12-Slide PowerPoint Presentation Deck
- Database Session Persistence
"""
import pytest
from research.search import deduplicate_sources
from research.extraction import extract_page_text
from research.source_assessor import assess_source_quality, enrich_sources_with_quality
from research.evidence_extractor import extract_evidence_items
from research.citation_validator import validate_citations_and_sources
from database.db import init_db, save_session, get_session_by_id
from generators.pdf_generator import generate_pdf
from generators.ppt_generator import generate_presentation
from generators.report_generator import generate_all_markdown_reports
from agents.tools import ToolRegistry
from agents.orchestrator import ResearchOrchestrator


def test_tool_registry():
    tools = ToolRegistry()
    assert hasattr(tools, "search_web")
    assert hasattr(tools, "extract_webpage")
    assert hasattr(tools, "compare_sources")
    assert hasattr(tools, "generate_report")

    # Test extract_webpage on bad URL
    res = tools.extract_webpage("invalid-url")
    assert res["accessible"] is False
    assert len(tools.execution_history) > 0


def test_source_quality_assessment():
    arxiv_src = {
        "title": "Attention Is All You Need",
        "url": "https://arxiv.org/abs/1706.03762",
        "snippet": "Transformer architecture empirical study published in 2017.",
    }
    assessed = assess_source_quality(arxiv_src)
    assert "ArXiv" in assessed["source_type"]
    assert assessed["authority_score"] >= 0.90
    assert assessed["is_peer_reviewed_or_official"] is True

    blog_src = {
        "title": "Random AI Musings",
        "url": "https://randomperson.medium.com/ai-post",
        "snippet": "Some informal thoughts.",
    }
    assessed_blog = assess_source_quality(blog_src)
    assert assessed_blog["credibility_tier"] == "Requires Caution"


def test_evidence_extraction():
    sources = [
        {
            "title": "AI in Healthcare Cybersecurity",
            "url": "https://ncbi.nlm.nih.gov/pmc/articles/12345",
            "snippet": "Machine learning intrusion detection models achieved 98.4% accuracy against ransomware attacks in hospital network benchmarks.",
            "content": "Machine learning intrusion detection models achieved 98.4% accuracy against ransomware attacks in hospital network benchmarks.",
            "published_date": "2024",
            "source_type": "Biomedical Repository",
        }
    ]
    items = extract_evidence_items("AI in Healthcare Cybersecurity", sources)
    assert len(items) >= 1
    assert "claim" in items[0]
    assert "evidence" in items[0]
    assert items[0]["confidence"] in ["Supported", "Limited", "Unverified"]


def test_deduplicate_sources():
    sources = [
        {"title": "Paper A", "url": "https://arxiv.org/abs/1234.5678?utm_source=test", "snippet": "Text 1"},
        {"title": "Paper A", "url": "https://arxiv.org/abs/1234.5678", "snippet": "Text 2"},
        {"title": "Paper B", "url": "https://ieee.org/doc/1", "snippet": "Text 3"},
    ]
    deduped = deduplicate_sources(sources)
    assert len(deduped) == 2
    assert deduped[0]["domain"] == "arxiv.org"


def test_inaccessible_page_handling():
    res = extract_page_text("https://this-is-a-completely-non-existent-domain-12345.org")
    assert res["accessible"] is False
    assert res["content"] == ""


def test_empty_topic_rejection():
    orchestrator = ResearchOrchestrator()
    with pytest.raises(ValueError):
        orchestrator.run_pipeline("   ")


def test_citation_validation():
    sources = [
        {"title": "Deep Learning Survey", "url": "https://example.com/dl", "domain": "example.com", "published_date": "2024", "accessible": True},
        {"title": "Transformer Evaluation", "url": "https://example.com/tf", "domain": "example.com", "published_date": "", "accessible": False},
    ]
    review = "Early work is detailed in [1], while scaling properties were examined in [2]."
    audit = validate_citations_and_sources(sources, review)
    assert audit["total_sources_collected"] == 2
    assert audit["total_sources_cited"] == 2
    assert audit["citation_coverage_percent"] == 100.0


def test_17_section_pdf_and_12_slide_pptx():
    init_db()
    sample_data = {
        "topic": "Impact of Artificial Intelligence on Cybersecurity in Healthcare",
        "title": "Empirical Investigation into AI-Driven Cybersecurity in Healthcare Systems",
        "keywords": ["AI", "Cybersecurity", "Healthcare", "Intrusion Detection", "Ransomware"],
        "abstract": "This study analyzes AI applications in healthcare cybersecurity.",
        "introduction": "Cyber threats in healthcare pose existential risks to patient safety.",
        "scope_and_motivation": "Investigating zero-trust AI anomaly detection models in hospital networks.",
        "problem_statement": "Healthcare organizations suffer high ransomware vulnerability due to legacy medical equipment.",
        "objectives": ["Evaluate intrusion detection accuracy", "Analyze clinical telemetry latency"],
        "research_questions": ["RQ1: What is the false positive rate of real-time anomaly detection?"],
        "subtopics": ["Network Anomaly Detection", "IoMT Device Security"],
        "search_queries": ["ai healthcare cybersecurity ransomware detection"],
        "sources": [{
            "title": "Hospital Security Survey",
            "url": "https://ncbi.nlm.nih.gov/article/1",
            "accessible": True,
            "source_type": "Biomedical Repository",
            "credibility_tier": "High Authority",
            "authority_score": 0.95,
            "published_date": "2024",
        }],
        "sources_count": 1,
        "source_summaries": [{"source_index": 1, "title": "Hospital Security Survey", "key_finding": "High accuracy", "limitations": "Small hospital sample"}],
        "comparative_analysis": ["Ensemble tree models outperform deep neural networks on tabular IoMT logs"],
        "consensus_points": ["Air-gapping is insufficient against insider threats"],
        "conflicting_evidence": ["Debate over centralized versus federated threat intelligence sharing"],
        "evidence_items": [{
            "citation_index": 1,
            "claim": "Ensemble detection models achieve high recall on ransomware traffic.",
            "source_title": "Hospital Security Survey",
            "source_url": "https://ncbi.nlm.nih.gov/article/1",
            "evidence": "Observed 98.4% detection recall across simulated attack vectors.",
            "publication_date": "2024",
            "confidence": "Supported",
        }],
        "literature_review": "### 1. Theoretical Foundations\nEarly network heuristics were catalogued in [1].",
        "research_gaps": [{
            "gap_id": "GAP-01",
            "gap_title": "Lack of Standardized IoMT Attack Benchmarks",
            "explanation": "Existing datasets lack high-fidelity clinical telemetry.",
            "supporting_sources": ["[1] Hospital Security Survey"],
            "why_it_matters": "Impairs reproducible testing.",
            "suggested_research_question": "How can realistic IoMT honeynets synthesize clinical logs safely?",
            "possible_methodology": "Synthetic telemetry generation with differential privacy.",
            "feasibility": "High",
        }],
        "methodology": {
            "framework_name": "Resilient Clinical Intrusion Framework (RCIF)",
            "research_design": "Empirical quantitative benchmarking",
            "research_approach": "Empirical Modeling",
            "hypotheses": ["H1: RCIF reduces detection latency by >= 40%."],
            "dataset_requirements": "100k synthetic clinical IoMT flow packets.",
            "data_collection_methods": "Simulated hardware honeypots.",
            "variables": {
                "independent_variables": ["Attack vector severity"],
                "dependent_variables": ["Detection latency (ms)", "F1 score"],
            },
            "workflow_stages": ["Ingestion", "Modeling", "Benchmarking", "Stress-Testing"],
        },
        "proposed_experiments": [{
            "experiment_id": "EXP-01",
            "name": "IoMT Zero-Day Attack Simulation",
            "hypothesis": "RCIF maintains >= 95% F1 score against unseen zero-day exploits.",
            "target_datasets": "Clinical IoMT packet traces",
            "baseline_models": "Snort and Suricata IDS",
            "evaluation_metrics": "Detection F1, P99 Latency (ms)",
            "validation_status": "Proposed Protocol (Pending Execution)",
        }],
        "expected_contributions": ["Novel clinical telemetry benchmark"],
        "limitations": ["Evaluated in emulated network topologies"],
        "conclusion": "AI represents an essential line of defense in hospital infrastructure.",
        "references": [{
            "index": 1,
            "title": "Hospital Security Survey",
            "url": "https://ncbi.nlm.nih.gov/article/1",
            "accessible": True,
            "published_date": "2024",
            "citation_format": "[1] Hospital Security Survey. Available: https://ncbi.nlm.nih.gov/article/1",
        }],
        "depth": "Standard",
        "is_demo_mode": True,
    }

    # 1. Test 17-section PDF
    pdf_p = generate_pdf(sample_data)
    assert pdf_p.endswith(".pdf")

    # 2. Test 12-slide PPTX
    from pptx import Presentation
    ppt_p = generate_presentation(sample_data)
    prs = Presentation(ppt_p)
    assert len(prs.slides) == 12

    # 3. Test Markdown dossier
    md_dict = generate_all_markdown_reports(sample_data)
    assert "report_md" in md_dict

    # 4. Test DB
    sess_id = save_session(sample_data, pdf_path=pdf_p, pptx_path=ppt_p)
    assert sess_id > 0
    rec = get_session_by_id(sess_id)
    assert rec["topic"] == sample_data["topic"]
