"""
Central Research Orchestrator for Klein AI — ResearchMate AI.
Features intelligent multi-agent decision-making:
- Tool Calling via ToolRegistry
- Adaptive secondary search if source count is insufficient
- Source Quality Assessment & Credibility Scoring
- Evidence-Based Claim Extraction (grounded passages & confidence)
- Conflict Detection & Consensus Reporting
- Complete 17-section structured academic compilation
"""
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List

import config
from agents.tools import ToolRegistry
from agents.planner import plan_research
from research.source_assessor import enrich_sources_with_quality
from research.evidence_extractor import extract_evidence_items
from research.citation_validator import validate_citations_and_sources

logger = logging.getLogger("KleinAI.Orchestrator")


class ResearchOrchestrator:
    """
    Intelligent Autonomous Orchestrator controlling the end-to-end research lifecycle.
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        tavily_api_key: Optional[str] = None,
        depth: str = "Standard",
        status_callback: Optional[Callable[[str, float], None]] = None,
        activity_log_callback: Optional[Callable[[str, str], None]] = None,
    ):
        self.gemini_key = gemini_api_key or config.GEMINI_API_KEY
        self.tavily_key = tavily_api_key or config.TAVILY_API_KEY
        self.depth = depth
        self.status_cb = status_callback
        self.log_cb = activity_log_callback
        self.logs: List[Dict[str, str]] = []
        self.is_demo = config.is_demo_mode(self.gemini_key, self.tavily_key)
        self.tools = ToolRegistry(gemini_key=self.gemini_key, tavily_key=self.tavily_key)

    def _log(self, stage: str, message: str, progress: float):
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "stage": stage,
            "message": message,
            "progress": progress,
        }
        self.logs.append(entry)
        logger.info(f"[{entry['time']}][{stage}] {message}")
        if self.status_cb:
            self.status_cb(message, progress)
        if self.log_cb:
            self.log_cb(stage, message)

    def run_pipeline(self, topic: str) -> Dict[str, Any]:
        """
        Executes the intelligent autonomous research pipeline.
        """
        topic = topic.strip()
        if not topic:
            raise ValueError("Research topic cannot be empty.")

        start_time = time.time()
        self._log("INIT", f"Initializing Klein AI Autonomous Orchestrator for: '{topic}'", 0.05)

        # -------------------------------------------------------------
        # STAGE 1: Research Planning & Query Generation
        # -------------------------------------------------------------
        self._log("PLANNER", "Formulating research objectives, questions (RQ1-RQ4), and search queries...", 0.12)
        plan_data = plan_research(
            topic=topic,
            depth=self.depth,
            gemini_key=self.gemini_key,
        )

        initial_queries = plan_data.get("search_queries", [])
        self._log("PLANNER", f"Formulated {len(initial_queries)} initial queries across thematic pillars.", 0.20)

        # -------------------------------------------------------------
        # STAGE 2: Web Search & Adaptive Deepening
        # -------------------------------------------------------------
        self._log("RESEARCHER", f"Dispatching Tavily Web Search (Depth: {self.depth})...", 0.28)
        raw_sources = []
        for q in initial_queries:
            results = self.tools.search_web(q, max_results=config.SEARCH_DEPTH_CONFIG[self.depth]["results_per_query"])
            raw_sources.extend(results)

        # Remove duplicate URLs
        from research.search import deduplicate_sources
        unique_sources = deduplicate_sources(raw_sources)
        self._log("RESEARCHER", f"Discovered {len(unique_sources)} unique candidate sources.", 0.38)

        # INTELLIGENT DECISION: If source count is low (< 4), trigger adaptive secondary queries
        if len(unique_sources) < 4:
            self._log("ADAPTIVE_SEARCH", "Source count below threshold (<4). Formulating secondary deepening queries...", 0.42)
            deepening_queries = [
                f"{topic} empirical evaluation benchmark study",
                f"{topic} state of the art survey paper arXiv",
            ]
            for dq in deepening_queries:
                extra = self.tools.search_web(dq, max_results=3)
                unique_sources.extend(extra)
            unique_sources = deduplicate_sources(unique_sources)
            self._log("ADAPTIVE_SEARCH", f"Expanded evidence pool to {len(unique_sources)} unique sources.", 0.45)

        # -------------------------------------------------------------
        # STAGE 3: Web Content Extraction & Quality Assessment
        # -------------------------------------------------------------
        self._log("EXTRACTION", "Extracting webpage bodies via BeautifulSoup and auditing accessibility...", 0.50)
        max_extract = config.SEARCH_DEPTH_CONFIG[self.depth]["max_extract"]
        inaccessible_count = 0

        for idx, src in enumerate(unique_sources[:max_extract], 1):
            url = src.get("url", "")
            if url:
                parsed = self.tools.extract_webpage(url)
                if parsed.get("accessible"):
                    src["content"] = parsed["content"]
                    src["accessible"] = True
                else:
                    inaccessible_count += 1
                    src["accessible"] = False

        if inaccessible_count > 0:
            self._log("EXTRACTION", f"Note: {inaccessible_count} sources had restricted access; preserved abstract snippets.", 0.55)

        # Quality assessment
        assessed_sources = enrich_sources_with_quality(unique_sources)
        self._log("SOURCE_ASSESSOR", f"Assessed source credibility tiers: {len(assessed_sources)} sources classified.", 0.60)

        # -------------------------------------------------------------
        # STAGE 4: Source Analysis, Comparative Matrix & Evidence Extraction
        # -------------------------------------------------------------
        self._log("ANALYST", "Comparing findings, isolating consensus points, and identifying conflicting evidence...", 0.66)
        analysis_data = self.tools.compare_sources(assessed_sources, topic=topic)

        self._log("EVIDENCE_ENGINE", "Extracting grounded claims and anchoring passages to empirical sources...", 0.72)
        evidence_items = extract_evidence_items(topic=topic, sources=assessed_sources, gemini_key=self.gemini_key)

        # -------------------------------------------------------------
        # STAGE 5: Thematic Literature Review
        # -------------------------------------------------------------
        self._log("LITERATURE_REVIEW", "Synthesizing thematic academic review with exact in-text citations...", 0.78)
        lit_data = {
            "topic": topic,
            "analysis": analysis_data,
            "sources": assessed_sources,
        }
        literature_review_text = self.tools.generate_literature_review(lit_data)

        # -------------------------------------------------------------
        # STAGE 6: Research Gap Discovery (7 Dimensions)
        # -------------------------------------------------------------
        self._log("GAP_FINDER", "Analyzing repeated limitations & contradictory findings for research gaps...", 0.84)
        gap_data = {
            "topic": topic,
            "analysis": analysis_data,
        }
        research_gaps = self.tools.identify_research_gaps(gap_data)

        # -------------------------------------------------------------
        # STAGE 7: Methodology & Proposed Validation Suite
        # -------------------------------------------------------------
        self._log("METHODOLOGY", "Designing proposed architecture, independent/dependent variables, and experiments...", 0.89)
        method_data = {
            "topic": topic,
            "gaps": research_gaps,
        }
        methodology_data = self.tools.propose_methodology(method_data)

        # -------------------------------------------------------------
        # STAGE 8: Citation Audit & Integrity Verification
        # -------------------------------------------------------------
        self._log("CITATION_VALIDATOR", "Auditing citations against collected sources and checking URL coverage...", 0.93)
        citation_audit = validate_citations_and_sources(
            sources=assessed_sources,
            literature_review_text=literature_review_text,
        )

        elapsed = round(time.time() - start_time, 2)
        self._log("COMPLETE", f"Autonomous research completed in {elapsed}s across {len(assessed_sources)} sources.", 0.96)

        # Generate Keywords
        keywords = [
            topic,
            plan_data.get("domain", "Computational Systems"),
            "Empirical Benchmarking",
            "State-of-the-Art Evaluation",
            "Scalability Analysis",
            "Algorithmic Modularity",
        ]

        title = plan_data.get("academic_title", f"Autonomous Systematic Investigation into {topic}")
        problem_statement = (
            f"Despite accelerating developments in {topic}, the field is hindered by fragmented benchmark reporting, "
            f"inconsistent baseline standardization, and unresolved trade-offs between computational overhead and empirical robustness. "
            f"Without a unified systematic synthesis and rigorous empirical validation protocols, deploying such systems in mission-critical "
            f"and high-concurrency environments remains fraught with performance unpredictability."
        )

        abstract = (
            f"This paper presents an autonomous systematic inquiry into {topic}. "
            f"Drawing from {len(assessed_sources)} public academic, institutional, and technical sources, we synthesize foundational paradigms, "
            f"cross-compare contemporary benchmarks, and isolate key points of scholarly consensus alongside conflicting empirical claims. "
            f"We identify {len(research_gaps)} critical unaddressed research gaps—including scalability degradation and evaluation deficits—and "
            f"propose the {methodology_data.get('framework_name', 'Decoupled Adaptive Framework')}. Furthermore, we articulate a comprehensive suite "
            f"of proposed validation experiments with testable hypotheses, datasets, baselines, and quantitative metrics to guide future empirical validation."
        )

        intro = (
            f"In recent years, {topic} has captured significant attention across scholarly inquiry and industrial research. "
            f"As underlying computational models expand in scale and complexity, researchers face intricate system-level trade-offs that "
            f"challenge conventional assumptions. Although empirical advancements continue to proliferate, the absence of unified synthesis "
            f"obscures true state-of-the-art limitations. This study addresses this challenge by establishing an evidence-grounded review of "
            f"contemporary literature, isolating critical research gaps, and establishing a formalized methodological roadmap complete with testable hypotheses."
        )

        conclusion = (
            f"This autonomous investigation into {topic} provides a rigorous synthesis of empirical breakthroughs and persistent systemic bottlenecks. "
            f"By grounding our analysis in {len(assessed_sources)} public sources, we delineated core areas of scholarly agreement alongside active debates "
            f"regarding scalability and out-of-distribution robustness. The proposed methodology and associated experimental validation suite offer an "
            f"actionable empirical blueprint for future research cohorts to validate architectural enhancements. Continued investigation along these "
            f"structured trajectories is vital for realizing dependable, high-efficiency systems in {topic}."
        )

        return {
            "topic": topic,
            "title": title,
            "keywords": keywords,
            "abstract": abstract,
            "introduction": intro,
            "domain": plan_data.get("domain", "Computational Systems"),
            "scope_and_motivation": plan_data.get("scope_and_motivation", ""),
            "problem_statement": problem_statement,
            "objectives": plan_data.get("objectives", []),
            "research_questions": plan_data.get("research_questions", []),
            "subtopics": plan_data.get("subtopics", []),
            "search_queries": initial_queries,
            "sources": assessed_sources,
            "sources_count": len(assessed_sources),
            "source_summaries": analysis_data.get("source_summaries", []),
            "comparative_analysis": analysis_data.get("comparative_analysis", []),
            "consensus_points": analysis_data.get("consensus_points", []),
            "conflicting_evidence": analysis_data.get("conflicting_evidence", []),
            "evidence_items": evidence_items,
            "literature_review": literature_review_text,
            "research_gaps": research_gaps,
            "methodology": methodology_data,
            "proposed_experiments": methodology_data.get("proposed_experiments", []),
            "expected_contributions": methodology_data.get("expected_contributions", []),
            "limitations": methodology_data.get("expected_limitations", methodology_data.get("limitations", [])),
            "citation_audit": citation_audit,
            "references": citation_audit.get("all_citations", []),
            "conclusion": conclusion,
            "depth": self.depth,
            "is_demo_mode": self.is_demo,
            "execution_time_seconds": elapsed,
            "activity_logs": self.logs,
            "tool_history": self.tools.execution_history,
        }
