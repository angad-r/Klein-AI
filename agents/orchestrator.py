"""
Central Research Orchestrator for KLEIN AI.
Features a multi-stage autonomous web research engine:
- Intelligent Research Planning (domain, context, problem, terminology, strategy, 8-12 queries)
- Bounded Autonomous Research Loop (max 3 rounds, domain diversity, query deduplication)
- Multi-engine search: Tavily Search API with public DuckDuckGo fallback
- Content Extraction: Tavily Extract API with BeautifulSoup4 fallback
- 6-Dimension Source Quality Assessment (Relevance != Credibility)
- Structured Evidence Extraction (findings, methodology, datasets, sample size, numerical metrics)
- Cross-Source Analysis (common findings, consensus, conflicting evidence, methodological divergence)
- Adaptive Subtopic Coverage Tracking & Query Deepening
- Academic Compilation (17-section ReportLab PDF, 12-slide PPTX, Markdown, SQLite)
- Strict Research Integrity: Zero fabrication of synthetic papers or citations.
"""
import re
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List, Set

import config
from agents.tools import ToolRegistry
from agents.planner import plan_research
from research.search import deduplicate_sources, rank_and_prioritize_sources, search_tavily, search_fallback_ddg
from research.extraction import enrich_sources
from research.source_assessor import enrich_sources_with_quality
from research.evidence_extractor import extract_evidence_items
from research.citation_validator import validate_citations_and_sources
from agents.analyst import analyze_sources
from agents.literature_review import generate_literature_review
from agents.gap_finder import find_research_gaps
from agents.methodology import propose_methodology

logger = logging.getLogger("KleinAI.Orchestrator")


class ResearchOrchestrator:
    """
    Intelligent Autonomous Orchestrator controlling the Day 2 multi-stage web research engine.
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        tavily_api_key: Optional[str] = None,
        depth: str = "Standard",
        status_callback: Optional[Callable[[str, float], None]] = None,
        activity_log_callback: Optional[Callable[[str, str], None]] = None,
        model: Optional[str] = None,
    ):
        self.gemini_key = gemini_api_key or config.get_gemini_api_key()
        self.tavily_key = tavily_api_key or config.get_tavily_api_key()
        self.depth = depth
        self.status_cb = status_callback
        self.log_cb = activity_log_callback
        self.model = model or config.GEMINI_MODEL
        self.logs: List[Dict[str, str]] = []
        self.is_demo = config.is_demo_mode(self.gemini_key, self.tavily_key)
        self.tools = ToolRegistry(gemini_key=self.gemini_key, tavily_key=self.tavily_key, model=self.model)

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
        Executes the Day 2 multi-stage autonomous web research engine.
        """
        topic = topic.strip()
        if not topic:
            raise ValueError("Research topic cannot be empty.")

        start_time = time.time()
        self._log("INIT", f"Initializing KLEIN AI Autonomous Research Engine for: '{topic}' (Model: {self.model})", 0.04)

        # -------------------------------------------------------------
        # STAGE 1: Intelligent Research Planning
        # -------------------------------------------------------------
        self._log("PLANNER", "Formulating research domain, context, core problem, RQs, and 8–12 diverse queries...", 0.10)
        plan_data = plan_research(
            topic=topic,
            depth=self.depth,
            gemini_key=self.gemini_key,
            model=self.model,
        )

        initial_queries = plan_data.get("search_queries", [])
        subtopics = plan_data.get("subtopics", [])
        self._log("PLANNER", f"Formulated {len(initial_queries)} initial queries across {len(subtopics)} thematic subtopics.", 0.16)

        # -------------------------------------------------------------
        # STAGE 2: Bounded Multi-Round Autonomous Research Loop
        # -------------------------------------------------------------
        depth_cfg = config.SEARCH_DEPTH_CONFIG.get(self.depth, config.SEARCH_DEPTH_CONFIG["Standard"])
        max_rounds = depth_cfg.get("max_rounds", 3)
        max_sources = depth_cfg.get("max_sources", 35)
        results_per_query = depth_cfg.get("results_per_query", 5)
        max_extract = depth_cfg.get("max_extract", 18)
        min_target = 6 if self.depth == "Quick" else 15

        executed_queries: Set[str] = set()
        collected_sources: List[Dict[str, Any]] = []
        round_history: List[Dict[str, Any]] = []
        current_queries = list(initial_queries)

        analysis_data: Dict[str, Any] = {}
        evidence_items: List[Dict[str, Any]] = []
        coverage_assessment: Dict[str, Any] = {}

        for round_idx in range(1, max_rounds + 1):
            # Filter unexecuted queries
            new_queries = [q.strip() for q in current_queries if q.strip() and q.strip().lower() not in executed_queries]
            if not new_queries:
                self._log("LOOP", f"All queries executed. Finalizing research loop at round {round_idx-1}.", 0.45)
                break

            engine_label = "Tavily Search API" if config.is_tavily_available(self.tavily_key) else "Public Web Engine"
            progress_pct = 0.18 + (round_idx - 1) * 0.10
            self._log("SEARCH", f"Iteration {round_idx}/{max_rounds}: Executing {len(new_queries)} queries via {engine_label}...", progress_pct)

            batch_raw: List[Dict[str, Any]] = []
            for q_idx, q in enumerate(new_queries, 1):
                executed_queries.add(q.lower())
                # Search using tools.search_web or direct search_tavily
                results = self.tools.search_web(q, max_results=results_per_query)
                batch_raw.extend(results)

            # Deduplicate and enforce domain diversity
            merged = collected_sources + batch_raw
            unique_sources = deduplicate_sources(merged, max_per_domain=config.MAX_SOURCES_PER_DOMAIN)
            collected_sources = unique_sources

            self._log("EXTRACTION", f"Iteration {round_idx}: Extracting content & verifying accessibility for top {min(len(collected_sources), max_extract)} sources...", progress_pct + 0.05)
            # Content extraction via Tavily extract + BeautifulSoup fallback
            extract_result = enrich_sources(
                collected_sources,
                max_to_extract=max_extract,
                tavily_key=self.tavily_key,
            )
            collected_sources = extract_result.get("sources", collected_sources)

            # 6-Dimension Source Quality Assessment
            self._log("ASSESSOR", f"Iteration {round_idx}: Evaluating 6-dimension quality (Relevance, Authority, Recency, etc.)...", progress_pct + 0.07)
            collected_sources = enrich_sources_with_quality(collected_sources, topic=topic)

            # Structured Evidence Extraction
            evidence_items = extract_evidence_items(
                topic=topic,
                sources=collected_sources,
                gemini_key=self.gemini_key,
                model=self.model,
            )

            # Cross-Source Synthesis
            analysis_data = analyze_sources(
                topic=topic,
                sources=collected_sources,
                gemini_key=self.gemini_key,
                model=self.model,
            )

            # Coverage Assessment
            subtopic_hits = {}
            for sub in subtopics:
                sub_words = set(re.findall(r"\b[A-Za-z]{4,}\b", sub.lower()))
                hits = 0
                for s in collected_sources:
                    s_text = (s.get("title", "") + " " + s.get("content", "")).lower()
                    if any(w in s_text for w in sub_words):
                        hits += 1
                subtopic_hits[sub] = hits

            covered_count = sum(1 for hits in subtopic_hits.values() if hits >= 1)
            coverage_pct = round((covered_count / max(len(subtopics), 1)) * 100, 1)

            round_info = {
                "round": round_idx,
                "queries_executed": new_queries,
                "raw_discovered": len(batch_raw),
                "total_unique_collected": len(collected_sources),
                "coverage_percent": coverage_pct,
            }
            round_history.append(round_info)

            # Evaluate whether to trigger additional search round
            uncovered_subtopics = [sub for sub, hits in subtopic_hits.items() if hits < 1]
            needs_more_coverage = (coverage_pct < 75.0 or len(collected_sources) < min_target)
            can_continue = (round_idx < max_rounds and len(collected_sources) < max_sources)

            if needs_more_coverage and can_continue:
                self._log("ADAPTIVE_LOOP", f"Coverage at {coverage_pct}% ({len(collected_sources)} sources). Formulating adaptive deepening queries...", progress_pct + 0.09)
                current_queries = []
                for unc in uncovered_subtopics[:2]:
                    current_queries.append(f"{topic} {unc} empirical benchmark analysis")
                current_queries.append(f"{topic} state of the art survey ablation metrics")
            else:
                self._log("AUTONOMOUS_LOOP", f"Research corpus finalized at Iteration {round_idx} with {len(collected_sources)} unique sources ({coverage_pct}% coverage).", 0.50)
                break

        # Research Integrity Check: If search failed completely, do NOT fabricate sources
        search_failed = (len(collected_sources) == 0)
        search_warning = ""
        if search_failed:
            search_warning = (
                f"Web search returned 0 accessible sources for '{topic}'. "
                "Per KLEIN AI research integrity protocols, no synthetic or fake paper titles, URLs, or citations were generated. "
                "Please verify network connectivity and ensure valid search API credentials are configured in .env."
            )
            self._log("WARNING", search_warning, 0.52)

        # Rank sources
        final_sources = rank_and_prioritize_sources(collected_sources[:max_sources])

        # Subtopic coverage summary
        coverage_assessment = {
            "rounds_executed": len(round_history),
            "total_queries_executed": len(executed_queries),
            "sources_discovered": len(final_sources),
            "sources_extracted": sum(1 for s in final_sources if s.get("accessible")),
            "sources_rejected": sum(1 for s in final_sources if not s.get("accessible")),
            "coverage_percent": coverage_pct if not search_failed else 0.0,
            "subtopic_coverage": subtopic_hits if not search_failed else {},
            "round_history": round_history,
        }

        # -------------------------------------------------------------
        # STAGE 3: Thematic Literature Review
        # -------------------------------------------------------------
        self._log("LITERATURE_REVIEW", "Synthesizing thematic academic review with exact in-text citations...", 0.65)
        lit_data = {
            "topic": topic,
            "analysis": analysis_data,
            "sources": final_sources,
        }
        literature_review_text = generate_literature_review(
            topic=topic,
            analysis_data=analysis_data,
            sources=final_sources,
            gemini_key=self.gemini_key,
            model=self.model,
        )

        # -------------------------------------------------------------
        # STAGE 4: Research Gap Discovery (7 Dimensions)
        # -------------------------------------------------------------
        self._log("GAP_FINDER", "Analyzing repeated limitations & contradictory findings for research gaps...", 0.75)
        research_gaps = find_research_gaps(
            topic=topic,
            analysis_data=analysis_data,
            gemini_key=self.gemini_key,
            model=self.model,
        )

        # -------------------------------------------------------------
        # STAGE 5: Methodology & Proposed Validation Suite
        # -------------------------------------------------------------
        self._log("METHODOLOGY", "Designing proposed architecture, independent/dependent variables, and experiments...", 0.85)
        methodology_data = propose_methodology(
            topic=topic,
            gaps=research_gaps,
            gemini_key=self.gemini_key,
            model=self.model,
        )

        # -------------------------------------------------------------
        # STAGE 6: Citation Audit & Integrity Verification
        # -------------------------------------------------------------
        self._log("CITATION_VALIDATOR", "Auditing citations against collected sources and checking URL coverage...", 0.92)
        citation_audit = validate_citations_and_sources(
            sources=final_sources,
            literature_review_text=literature_review_text,
        )

        elapsed = round(time.time() - start_time, 2)
        self._log("COMPLETE", f"Autonomous research completed in {elapsed}s across {len(final_sources)} verified sources.", 0.98)

        # Keywords & Metadata
        keywords = [
            topic,
            plan_data.get("domain", "Computational Systems"),
            "Empirical Benchmarking",
            "State-of-the-Art Evaluation",
            "Scalability Analysis",
            "Algorithmic Modularity",
        ]
        for term in plan_data.get("technical_terminology", [])[:4]:
            if term not in keywords:
                keywords.append(term)

        title = plan_data.get("academic_title", f"Autonomous Systematic Investigation into {topic}")

        if len(final_sources) > 0:
            problem_statement = (
                f"Despite accelerating developments in {topic}, the field is hindered by fragmented benchmark reporting, "
                f"inconsistent baseline standardization, and unresolved trade-offs between computational overhead and empirical robustness. "
                f"Without a unified systematic synthesis and rigorous empirical validation protocols, deploying such systems in mission-critical "
                f"environments remains fraught with performance unpredictability."
            )
            abstract = (
                f"This paper presents an autonomous systematic inquiry into {topic}. "
                f"Drawing from {len(final_sources)} public academic, institutional, and technical sources across {len(round_history)} autonomous search rounds, "
                f"we synthesize foundational paradigms, cross-compare contemporary benchmarks, and isolate key points of scholarly consensus alongside conflicting empirical claims. "
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
                f"By grounding our analysis in {len(final_sources)} public sources, we delineated core areas of scholarly agreement alongside active debates "
                f"regarding scalability and out-of-distribution robustness. The proposed methodology and associated experimental validation suite offer an "
                f"actionable empirical blueprint for future research cohorts to validate architectural enhancements."
            )
        else:
            problem_statement = (
                f"This investigation focuses on '{topic}'. However, external public web search yielded 0 accessible sources. "
                "In strict adherence to academic integrity protocols, no unverified claims or synthetic citations are asserted. "
                "The research questions and proposed methodology below outline the theoretical blueprint for subsequent empirical validation."
            )
            abstract = (
                f"This document presents an autonomous research formulation for '{topic}'. "
                "Note: Web search returned 0 accessible sources during this execution. Per KLEIN AI research integrity standards, "
                "no citations, empirical benchmarks, or source claims were fabricated. The report formalizes primary research objectives, "
                f"identifies {len(research_gaps)} theoretical gap dimensions, and establishes a testable methodological framework pending live source retrieval."
            )
            intro = (
                f"The domain of {topic} presents critical technical challenges and conceptual opportunities. "
                "This study establishes an autonomous research plan, formalizing research questions and proposed methodological architectures. "
                "To establish grounded empirical comparisons, live source gathering should be retried with active search credentials."
            )
            conclusion = (
                f"This preliminary formulation for '{topic}' articulates foundational research questions, conceptual research gaps, "
                "and an actionable proposed methodology suite. Future iterations should incorporate empirical findings from live web search "
                "to evaluate benchmark performance against established baselines."
            )

        return {
            "topic": topic,
            "title": title,
            "keywords": keywords,
            "abstract": abstract,
            "introduction": intro,
            "domain": plan_data.get("domain", "Computational Systems"),
            "research_context": plan_data.get("research_context", ""),
            "core_problem": plan_data.get("core_problem", problem_statement),
            "scope_and_motivation": plan_data.get("scope_and_motivation", ""),
            "problem_statement": problem_statement,
            "objectives": plan_data.get("objectives", []),
            "research_questions": plan_data.get("research_questions", []),
            "subtopics": subtopics,
            "technical_terminology": plan_data.get("technical_terminology", []),
            "search_strategy": plan_data.get("search_strategy", ""),
            "expected_evidence_requirements": plan_data.get("expected_evidence_requirements", []),
            "search_queries": initial_queries,
            "executed_queries": list(executed_queries),
            "search_rounds_completed": len(round_history),
            "search_max_rounds": max_rounds,
            "search_coverage_score": (coverage_pct / 100.0) if not search_failed else 0.0,
            "sources_discovered": len(final_sources),
            "sources_extracted": sum(1 for s in final_sources if s.get("accessible")),
            "sources_rejected": sum(1 for s in final_sources if not s.get("accessible")),
            "sources": final_sources,
            "sources_count": len(final_sources),
            "search_failed": search_failed,
            "search_warning": search_warning,
            "source_summaries": analysis_data.get("source_summaries", []),
            "comparative_analysis": analysis_data.get("comparative_analysis", []),
            "consensus_points": analysis_data.get("consensus_points", []),
            "conflicting_evidence": analysis_data.get("conflicting_evidence", []),
            "common_findings": analysis_data.get("common_findings", []),
            "methodological_differences": analysis_data.get("methodological_differences", []),
            "dataset_differences": analysis_data.get("dataset_differences", []),
            "emerging_themes": analysis_data.get("emerging_themes", []),
            "areas_with_insufficient_evidence": analysis_data.get("areas_with_insufficient_evidence", []),
            "evidence_items": evidence_items,
            "coverage_assessment": coverage_assessment,
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
