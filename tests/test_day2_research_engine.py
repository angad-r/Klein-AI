"""
Unit and Integration Test Suite for KLEIN AI - Day 2 Autonomous Web Research Engine.
Covers:
- Dynamic Query Generation (8-12 queries, diversity, domain terminology)
- Search API Integration (Tavily search, Tavily extract, timeouts, retries, fallbacks)
- Result Processing (Deduplication, URL normalization, domain diversity max 3/domain, ranking)
- Content Extraction (Tavily extract, BS4 fallback, length validation, error handling)
- 6-Dimension Source Quality Assessment (Relevance, Authority, Transparency, Recency, Methodology, Evidence; Relevance != Credibility)
- Structured Evidence Extraction (Claims, findings, methodology, datasets, sample sizes, numerical metrics, limitations)
- Cross-Source Research Analysis (Common findings, consensus, conflicting evidence preservation, methodological differences)
- Autonomous Research Loop (Bounded multi-round loop, subtopic coverage assessment, adaptive query deepening)
- Edge Cases & Integrity (Empty results zero fabrication, API failures, paywalls, malformed JSON)
- Deliverable Integrity (PDF and PPTX with enhanced Day 2 data structures)
"""
import sys
import os
import json
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import config
from agents.planner import plan_research
from research.search import (
    search_tavily,
    extract_tavily,
    deduplicate_sources,
    normalize_url,
    extract_domain,
    rank_and_prioritize_sources,
    AdaptiveResearchEngine,
)
from research.extraction import enrich_sources, extract_page_text
from research.source_assessor import assess_source_quality, enrich_sources_with_quality
from research.evidence_extractor import extract_evidence_items
from agents.analyst import analyze_sources
from agents.orchestrator import ResearchOrchestrator
from generators.pdf_generator import generate_pdf
from generators.ppt_generator import generate_presentation


# ==============================================================================
# 1. DYNAMIC QUERY GENERATION TESTS
# ==============================================================================

def test_dynamic_query_generation_count_and_diversity():
    """Verify that plan_research produces 8-12 diverse, non-generic queries with technical terminology."""
    topic = "Sparse Mixture of Experts in Large Language Models"
    plan = plan_research(topic, depth="Standard")

    queries = plan.get("search_queries", [])
    assert 8 <= len(queries) <= 12, f"Expected 8-12 queries, got {len(queries)}"

    # Specificity & terminology check: should not be bare generic queries
    for q in queries:
        assert len(q.split()) >= 3, f"Query '{q}' is too brief/generic"
        assert not q.lower().endswith("???"), "Malformed query punctuation"

    # Diverse perspective keywords across query set
    all_q_text = " ".join(queries).lower()
    perspectives = ["survey", "benchmark", "efficiency", "routing", "scaling", "ablation", "architecture"]
    matches = sum(1 for p in perspectives if p in all_q_text)
    assert matches >= 3, f"Expected query diversity covering multiple technical aspects, found {matches}"

    # Verify all 12 metadata fields exist in plan
    required_fields = [
        "academic_title", "domain", "research_context", "core_problem",
        "scope_and_motivation", "objectives", "research_questions",
        "subtopics", "technical_terminology", "search_strategy",
        "expected_evidence_requirements", "search_queries",
    ]
    for rf in required_fields:
        assert rf in plan, f"Missing required plan field: {rf}"


# ==============================================================================
# 2. SEARCH API INTEGRATION & ERROR HANDLING
# ==============================================================================

def test_search_tavily_success_and_metadata_preservation():
    """Verify search_tavily parses Tavily response and populates comprehensive metadata."""
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {
                "title": "Scaling MoE with 1-Bit Weights",
                "url": "https://arxiv.org/abs/2402.12345?utm_source=twitter",
                "content": "We evaluate sparse mixture of experts with extreme quantization across 60B parameters.",
                "score": 0.94,
                "published_date": "2024-03-15",
            }
        ]
    }

    with patch("research.search.TavilyClient", return_value=mock_client):
        results = search_tavily("MoE Quantization", "tvly-valid-mock-key", max_results=5)

    assert len(results) == 1
    src = results[0]
    assert src["title"] == "Scaling MoE with 1-Bit Weights"
    assert "utm_source" not in src["url"]  # Normalized URL
    assert src["domain"] == "arxiv.org"
    assert src["score"] == 0.94
    assert src["source_engine"] == "Tavily Search API"
    assert src["accessible"] is True


def test_search_tavily_retries_and_timeout_handling():
    """Verify search_tavily catches transient errors and retries before failing gracefully."""
    mock_client = MagicMock()
    mock_client.search.side_effect = [Exception("503 Service Unavailable"), Exception("Gateway Timeout")]

    with patch("research.search.TavilyClient", return_value=mock_client):
        with pytest.raises(RuntimeError, match="Tavily search failed"):
            search_tavily("Quantum error mitigation", "tvly-key", max_results=3)

    assert mock_client.search.call_count == 3


def test_extract_tavily_batch_execution():
    """Verify extract_tavily invokes client.extract and handles parsed documents."""
    mock_client = MagicMock()
    mock_client.extract.return_value = {
        "results": [
            {
                "url": "https://nature.com/articles/moe-analysis",
                "raw_content": "Extracted full paper text explaining mixture of experts routing dynamics and gating entropy.",
            }
        ],
        "failed_results": [
            {"url": "https://forbidden-paywall.com/paper", "error": "HTTP 403 Forbidden"}
        ]
    }

    with patch("research.search.TavilyClient", return_value=mock_client):
        data = extract_tavily(["https://nature.com/articles/moe-analysis", "https://forbidden-paywall.com/paper"], "tvly-key")

    assert "https://nature.com/articles/moe-analysis" in data
    assert data["https://nature.com/articles/moe-analysis"]["accessible"] is True
    assert "routing dynamics" in data["https://nature.com/articles/moe-analysis"]["content"]


# ==============================================================================
# 3. RESULT PROCESSING: DEDUPLICATION, NORMALIZATION & DOMAIN DIVERSITY
# ==============================================================================

def test_url_normalization_strips_tracking():
    """Verify tracking parameters (utm, fbclid, ref) are stripped."""
    u1 = "https://example.com/paper?utm_source=feed&utm_medium=rss&id=42#abstract"
    norm = normalize_url(u1)
    assert "utm_source" not in norm
    assert "utm_medium" not in norm
    assert "id=42" in norm


def test_domain_diversity_enforces_max_three_sources():
    """Verify that no single domain supplies more than 3 results."""
    sources = [
        {"url": f"https://medium.com/article-{i}", "title": f"Medium Post {i}", "snippet": "Text"}
        for i in range(7)
    ] + [
        {"url": "https://arxiv.org/abs/1", "title": "Arxiv 1", "snippet": "Text"},
        {"url": "https://nature.com/article", "title": "Nature 1", "snippet": "Text"},
    ]

    deduped = deduplicate_sources(sources, max_per_domain=3)
    domain_counts = {}
    for s in deduped:
        d = s.get("domain", extract_domain(s.get("url", "")))
        domain_counts[d] = domain_counts.get(d, 0) + 1

    assert domain_counts.get("medium.com") == 3, f"Expected Medium capped at 3, got {domain_counts.get('medium.com')}"
    assert len(deduped) == 5


def test_composite_result_ranking():
    """Verify rank_and_prioritize_sources prioritizes academic domains, content depth, and recency."""
    sources = [
        {"title": "Blog Post", "url": "https://myblog.com/ai", "domain": "myblog.com", "content": "Short text", "published_date": "2020-01-01", "score": 0.4},
        {"title": "Nature Benchmark", "url": "https://nature.com/articles/s41586", "domain": "nature.com", "content": "Detailed comprehensive empirical study " * 50, "published_date": "2024-05-10", "score": 0.85},
        {"title": "ArXiv Paper", "url": "https://arxiv.org/abs/2401.999", "domain": "arxiv.org", "content": "Mathematical formal proofs and empirical metrics " * 40, "published_date": "2024-02-01", "score": 0.80},
    ]

    ranked = rank_and_prioritize_sources(sources)
    assert ranked[0]["domain"] == "nature.com"
    assert ranked[1]["domain"] == "arxiv.org"
    assert ranked[2]["domain"] == "myblog.com"


# ==============================================================================
# 4. SOURCE EXTRACTION & BEAUTIFUL SOUP FALLBACK
# ==============================================================================

def test_beautifulsoup_fallback_extraction():
    """Verify BS4 cleanly strips scripts/styles and parses readable body paragraphs."""
    sample_html = """
    <html>
        <head><script>alert('noise');</script><style>.bad{color:red;}</style></head>
        <body>
            <nav>Navigation links</nav>
            <main>
                <h1>Autonomous Systems Benchmark</h1>
                <p>We present an empirical benchmark evaluating autonomous agent multi-step coordination.</p>
                <p>Experimental results on 500 tasks show a 34.2% reduction in hallucination rates.</p>
            </main>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.content = sample_html.encode("utf-8")

    with patch("requests.get", return_value=mock_resp):
        res = extract_page_text("https://example.org/study")

    assert res["accessible"] is True
    assert "Autonomous Systems Benchmark" in res["content"]
    assert "reduction in hallucination rates" in res["content"]
    assert "alert('noise')" not in res["content"]
    assert "Navigation links" not in res["content"]


def test_short_content_rejection_or_marking():
    """Verify that sources with less than 100 characters of meaningful content are marked appropriately."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.content = b"<html><body><p>Access denied.</p></body></html>"

    with patch("requests.get", return_value=mock_resp):
        res = extract_page_text("https://example.com/short")

    assert res["accessible"] is False or len(res["content"]) < 100


# ==============================================================================
# 5. SOURCE QUALITY ASSESSMENT: 6 DIMENSIONS & RELEVANCE != CREDIBILITY
# ==============================================================================

def test_source_quality_six_dimensions():
    """Verify source assessment generates all 6 dimensions between 0.0 and 1.0."""
    source = {
        "title": "Genome Sequencing Advances in Crop Disease Resistance",
        "url": "https://nature.com/articles/crop-genetics-2024",
        "domain": "nature.com",
        "content": "Empirical genetic sequencing on 1200 plant specimens yields 98.4% diagnostic sensitivity. We describe our PCR methodology and cross-validation partition.",
        "published_date": "2024-04-12",
    }
    assessed = assess_source_quality(source, topic="crop disease detection")

    dims = assessed.get("quality_dimensions", {})
    for d in ["relevance", "authority", "transparency", "recency", "methodology", "evidence_availability"]:
        assert d in dims, f"Dimension {d} missing"
        assert 0.0 <= dims[d] <= 1.0, f"Dimension {d} value {dims[d]} out of bounds"

    assert assessed["source_category"] == "Academic Publication"
    assert assessed["peer_reviewed_verified"] is True
    assert assessed["authority_score"] >= 0.85


def test_relevance_vs_credibility_separation():
    """Verify an authentic academic paper on an off-topic subject receives high authority but low relevance."""
    off_topic_paper = {
        "title": "Quantum Hall Effect in Graphene Nanoribbons",
        "url": "https://science.org/doi/10.1126/science.12345",
        "domain": "science.org",
        "content": "We measure transverse conductivity in bilayer graphene under 14 Tesla magnetic fields at 4 Kelvin.",
        "published_date": "2024-01-15",
    }
    assessed = assess_source_quality(off_topic_paper, topic="Early crop disease detection using computer vision")

    dims = assessed.get("quality_dimensions", {})
    # Science.org has top tier authority:
    assert dims["authority"] >= 0.90
    # But relevance to crop computer vision must be significantly lower than authority:
    assert dims["relevance"] <= 0.55
    # Confirms Relevance != Credibility
    assert dims["relevance"] < dims["authority"]


# ==============================================================================
# 6. STRUCTURED EVIDENCE EXTRACTION
# ==============================================================================

def test_evidence_extraction_structured_fields():
    """Verify extract_evidence_items extracts findings, methodology, datasets, and numerical metrics."""
    sources = [
        {
            "citation_index": 1,
            "title": "Vision Transformers in Foliar Disease Segmentation",
            "url": "https://frontiersin.org/articles/foliar-vit",
            "published_date": "2024-03-20",
            "source_type": "Academic Publication",
            "content": (
                "We trained a Swin-Transformer backbone on the PlantVillage dataset comprising 54,306 images across 14 crop species. "
                "Our proposed model achieved an F1-score of 97.4% and an inference latency of 12.3ms on edge Jetson Orin. "
                "However, accuracy degraded by 8.2% under severe motion blur and variable illumination field conditions."
            ),
        }
    ]

    items = extract_evidence_items("Early crop disease detection", sources)
    assert len(items) >= 1
    ev = items[0]
    assert ev["citation_index"] == 1
    assert "claim" in ev
    assert "supporting_passage" in ev or "evidence" in ev
    assert ev["confidence"] in ["Supported", "Limited", "Unverified"]
    # Check numerical metric capturing
    assert any(char.isdigit() for char in ev.get("numerical_results", "") + ev.get("evidence", ""))


# ==============================================================================
# 7. CROSS-SOURCE ANALYSIS & CONFLICT PRESERVATION
# ==============================================================================

def test_cross_source_conflicting_evidence_preserved():
    """Verify conflicting findings are preserved as opposing viewpoints rather than collapsed into false consensus."""
    sources = [
        {
            "citation_index": 1,
            "title": "Edge ViT for Agriculture",
            "content": "Vision Transformers consistently outperform standard ResNet CNNs by 4.5% mAP in real orchard drone surveys.",
        },
        {
            "citation_index": 2,
            "title": "CNN Efficiency under Constrained Hardware",
            "content": "Standard CNN architectures with depthwise separable convolutions demonstrate superior latency-accuracy trade-offs over ViTs on battery-constrained field sensors.",
        },
    ]

    analysis = analyze_sources("Crop Disease AI Architectures", sources)
    assert "common_findings" in analysis
    assert "conflicting_evidence" in analysis
    assert "comparative_analysis" in analysis

    conflicts = analysis["conflicting_evidence"]
    assert len(conflicts) >= 1
    # Check that opposing positions are retained
    c0 = conflicts[0]
    if isinstance(c0, dict):
        assert "position_a" in c0
        assert "position_b" in c0


# ==============================================================================
# 8. AUTONOMOUS RESEARCH LOOP & BOUNDEDNESS
# ==============================================================================

def test_autonomous_loop_terminates_within_bounds():
    """Verify orchestrator runs multi-round loop and terminates within max_rounds."""
    orch = ResearchOrchestrator(depth="Quick")

    # Mock tool search returning controlled sources
    round_counter = [0]
    def mock_search(query, **kwargs):
        round_counter[0] += 1
        return [
            {
                "title": f"Source for {query[:20]}",
                "url": f"https://sciencedirect.com/article/{round_counter[0]}",
                "content": "Detailed empirical data and benchmarks on algorithmic efficiency and latency in field conditions. " * 5,
                "score": 0.88,
            }
        ]

    orch.tools.search_web = mock_search

    report = orch.run_pipeline("Autonomous Robotics Trajectory Optimization")
    assert report is not None
    assert report["sources_count"] > 0
    assert report["search_rounds_completed"] <= config.SEARCH_DEPTH_CONFIG["Quick"]["max_rounds"]
    assert "search_coverage_score" in report


# ==============================================================================
# 9. EDGE CASES & RESEARCH INTEGRITY
# ==============================================================================

def test_empty_search_zero_fabrication():
    """Verify that if search yields 0 sources, orchestrator produces ZERO synthetic citations or paper titles."""
    orch = ResearchOrchestrator(depth="Quick")
    orch.tools.search_web = lambda q, **kwargs: []

    report = orch.run_pipeline("Completely Obscure Theoretical Niche Concept 99999")
    assert report["search_failed"] is True
    assert report["sources_count"] == 0
    assert report["sources"] == []
    assert report["evidence_items"] == []
    assert report["references"] == []
    assert "10.1145" not in report.get("literature_review", "")
    assert "arxiv.org" not in report.get("literature_review", "").lower()


def test_malformed_gemini_json_fallback():
    """Verify that when Gemini returns malformed or non-JSON text, planner and analyst recover gracefully."""
    with patch("agents.planner.call_gemini", return_value="Here is your research plan:\nNot a json string at all!"):
        plan = plan_research("Zero-Knowledge Proofs in Distributed Ledgers", depth="Quick")
        assert len(plan["search_queries"]) >= 4
        assert len(plan["objectives"]) >= 3


# ==============================================================================
# 10. ARTIFACT GENERATOR BACKWARD COMPATIBILITY
# ==============================================================================

def test_reportlab_pdf_and_pptx_with_day2_structures(tmp_path):
    """Verify that ReportLab PDF and PowerPoint deck compile seamlessly with Day 2 data structures."""
    report_data = {
        "topic": "Reinforcement Learning from Human Feedback",
        "title": "Systematic Analysis of RLHF Scaling Dynamics",
        "domain": "Artificial Intelligence & Alignment",
        "abstract": "We analyze reward model over-optimization and policy drift across multiple contemporary benchmark datasets.",
        "introduction": "Reinforcement learning from human feedback represents a cornerstone alignment methodology.",
        "literature_review": "Foundational theoretical treatises [1] established preference pair optimization.",
        "conclusion": "Future research must address reward collapse under out-of-distribution prompts.",
        "keywords": ["RLHF", "Alignment", "Reward Models", "PPO", "DPO"],
        "sources": [
            {
                "citation_index": 1,
                "title": "Direct Preference Optimization: Your Language Model is Secretly a Reward Model",
                "url": "https://arxiv.org/abs/2305.18290",
                "domain": "arxiv.org",
                "source_type": "Academic Publication",
                "authority_score": 0.88,
                "content": "DPO formulates preference learning implicitly without training a separate reward network.",
            }
        ],
        "sources_count": 1,
        "evidence_items": [
            {
                "citation_index": 1,
                "claim": "DPO reduces computational overhead by eliminating explicit reward model inference.",
                "evidence": "Implicit reward formulation matches PPO performance with 40% fewer training steps.",
                "confidence": "Supported",
                "methodology": "Implicit Policy Optimization",
                "dataset": "Anthropic HH-RLHF",
                "numerical_results": "40% step reduction",
                "limitations": "Susceptible to reference model degradation",
                "source_title": "Direct Preference Optimization",
                "source_url": "https://arxiv.org/abs/2305.18290",
            }
        ],
        "research_gaps": [
            {
                "gap_id": "GAP-01",
                "gap_title": "Length-Bias in Implicit Preference Loss",
                "feasibility": "High",
                "explanation": "DPO models exhibit length bias, favoring verbose answers over concise accuracy.",
                "supporting_sources": ["[1]"],
                "why_it_matters": "Increases generation latency and memory pressure.",
                "suggested_research_question": "How to constrain sequence length in loss formulation?",
                "possible_methodology": "Length-regularized Bradley-Terry objectives.",
            }
        ],
        "proposed_experiments": [
            {
                "experiment_id": "EXP-01",
                "name": "Length-Constrained Policy Evaluation",
                "validation_status": "PROPOSED PROTOCOL",
                "hypothesis": "Adding length regularization prevents token bloating without sacrificing win rates.",
                "target_datasets": "AlpacaEval 2.0",
                "baseline_models": "Standard DPO-7B",
                "evaluation_metrics": "Win-rate, Average Sequence Length",
            }
        ],
        "methodology": {
            "framework_name": "Length-Regularized Preference Alignment (LRPA)",
            "research_design": "Comparative Empirical Benchmark",
            "research_approach": "Quantitative Offline Alignment",
            "hypotheses": ["H1: Regularization eliminates length exploitation."],
            "variables": {
                "independent_variables": ["Length penalty coefficient"],
                "dependent_variables": ["Win-rate", "Sequence length"],
            },
            "workflow_stages": ["Data Tokenization", "Policy Gradient Optimization", "AlpacaEval Evaluation"],
            "dataset_requirements": "Paired preference datasets with controlled length distributions.",
            "data_collection_methods": "Standardized human and LLM-as-a-judge evaluations.",
        },
        "references": [
            {"index": 1, "title": "Direct Preference Optimization", "url": "https://arxiv.org/abs/2305.18290", "accessible": True}
        ],
        "citation_audit": {
            "total_sources_collected": 1,
            "total_sources_cited": 1,
            "citation_coverage_percent": 100.0,
            "integrity_status": "PASS",
        },
    }

    pdf_file = tmp_path / "test_day2_report.pdf"
    pptx_file = tmp_path / "test_day2_deck.pptx"

    out_pdf = generate_pdf(report_data, output_path=str(pdf_file))
    out_pptx = generate_presentation(report_data, output_path=str(pptx_file))

    assert Path(out_pdf).exists()
    assert Path(out_pdf).stat().st_size > 5000
    assert Path(out_pptx).exists()
    assert Path(out_pptx).stat().st_size > 10000
