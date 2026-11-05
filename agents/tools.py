"""
Tool Registry for KLEIN AI.
Provides structured, typed tools for the autonomous research agent:
- search_web(query)
- extract_webpage(url)
- analyse_source(source)
- compare_sources(sources)
- generate_literature_review(data)
- identify_research_gaps(data)
- propose_methodology(data)
- generate_report(data)
- generate_presentation(data)
"""
import time
import logging
from typing import Dict, Any, List, Optional, Callable

import config
from research.search import execute_multi_search, search_tavily, search_fallback_ddg
from research.extraction import extract_page_text, enrich_sources
from agents.analyst import analyze_sources
from agents.literature_review import generate_literature_review
from agents.gap_finder import find_research_gaps
from agents.methodology import propose_methodology
from generators.pdf_generator import generate_pdf
from generators.ppt_generator import generate_presentation
from generators.report_generator import generate_all_markdown_reports

logger = logging.getLogger("KleinAI.ToolRegistry")


class ToolRegistry:
    """
    Central registry for autonomous agent tool execution with validation,
    telemetry logging, and error resilience.
    """

    def __init__(self, gemini_key: Optional[str] = None, tavily_key: Optional[str] = None):
        self.gemini_key = gemini_key or config.GEMINI_API_KEY
        self.tavily_key = tavily_key or config.TAVILY_API_KEY
        self.execution_history: List[Dict[str, Any]] = []

    def _record_execution(self, tool_name: str, params: Dict[str, Any], duration: float, success: bool, error: Optional[str] = None):
        self.execution_history.append({
            "timestamp": time.strftime("%H:%M:%S"),
            "tool": tool_name,
            "params": {k: str(v)[:60] for k, v in params.items()},
            "duration_seconds": round(duration, 3),
            "success": success,
            "error": error,
        })

    def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Tool: search_web(query) — Searches the public internet using Tavily or fallback."""
        start = time.time()
        try:
            if not query or not query.strip():
                raise ValueError("Query string cannot be empty.")
            
            results = []
            if config.is_tavily_available(self.tavily_key):
                try:
                    results = search_tavily(query.strip(), self.tavily_key, max_results=max_results)
                except Exception as te:
                    logger.warning(f"Tavily search failed ({te}). Falling back to public DDG search...")
                    results = search_fallback_ddg(query.strip(), max_results=max_results)
            else:
                results = search_fallback_ddg(query.strip(), max_results=max_results)
                
            self._record_execution("search_web", {"query": query, "max_results": max_results}, time.time() - start, True)
            return results
        except Exception as e:
            self._record_execution("search_web", {"query": query}, time.time() - start, False, str(e))
            logger.warning(f"Tool search_web failed: {e}. Falling back to empty batch.")
            return []

    def extract_webpage(self, url: str) -> Dict[str, Any]:
        """Tool: extract_webpage(url) — Scrapes clean textual body and checks accessibility."""
        start = time.time()
        try:
            res = extract_page_text(url)
            self._record_execution("extract_webpage", {"url": url}, time.time() - start, True)
            return res
        except Exception as e:
            self._record_execution("extract_webpage", {"url": url}, time.time() - start, False, str(e))
            return {"content": "", "accessible": False, "status_code": -1}

    def analyse_source(self, source: Dict[str, Any], topic: str = "") -> Dict[str, Any]:
        """Tool: analyse_source(source) — Extracts key findings, quality assessment, and limitations."""
        start = time.time()
        try:
            analysis = analyze_sources(topic, [source], gemini_key=self.gemini_key)
            summaries = analysis.get("source_summaries", [])
            res = summaries[0] if summaries else {
                "source_index": 1,
                "title": source.get("title", ""),
                "key_finding": source.get("snippet", "")[:150],
                "limitations": "Observational study with localized scope.",
            }
            self._record_execution("analyse_source", {"title": source.get("title", "")}, time.time() - start, True)
            return res
        except Exception as e:
            self._record_execution("analyse_source", {"title": source.get("title", "")}, time.time() - start, False, str(e))
            return {
                "source_index": 1,
                "title": source.get("title", ""),
                "key_finding": source.get("snippet", "")[:150],
                "limitations": "Extracted via fallback heuristic.",
            }

    def compare_sources(self, sources: List[Dict[str, Any]], topic: str = "") -> Dict[str, Any]:
        """Tool: compare_sources(sources) — Compares findings, consensus, and conflicts across sources."""
        start = time.time()
        try:
            res = analyze_sources(topic, sources, gemini_key=self.gemini_key)
            self._record_execution("compare_sources", {"sources_count": len(sources)}, time.time() - start, True)
            return res
        except Exception as e:
            self._record_execution("compare_sources", {"sources_count": len(sources)}, time.time() - start, False, str(e))
            return {"comparative_analysis": [], "consensus_points": [], "conflicting_evidence": []}

    def generate_literature_review(self, data: Dict[str, Any]) -> str:
        """Tool: generate_literature_review(data) — Thematic academic literature review."""
        start = time.time()
        try:
            topic = data.get("topic", "")
            analysis = data.get("analysis", {})
            sources = data.get("sources", [])
            review = generate_literature_review(topic, analysis, sources, gemini_key=self.gemini_key)
            self._record_execution("generate_literature_review", {"topic": topic}, time.time() - start, True)
            return review
        except Exception as e:
            self._record_execution("generate_literature_review", {}, time.time() - start, False, str(e))
            return "Literature review synthesis pending."

    def identify_research_gaps(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Tool: identify_research_gaps(data) — Pinpoints unaddressed gaps, impact, and directions."""
        start = time.time()
        try:
            topic = data.get("topic", "")
            analysis = data.get("analysis", {})
            gaps = find_research_gaps(topic, analysis, gemini_key=self.gemini_key)
            self._record_execution("identify_research_gaps", {"topic": topic}, time.time() - start, True)
            return gaps
        except Exception as e:
            self._record_execution("identify_research_gaps", {}, time.time() - start, False, str(e))
            return []

    def propose_methodology(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: propose_methodology(data) — Generates research design, variables, and experiments."""
        start = time.time()
        try:
            topic = data.get("topic", "")
            gaps = data.get("gaps", [])
            meth = propose_methodology(topic, gaps, gemini_key=self.gemini_key)
            self._record_execution("propose_methodology", {"topic": topic}, time.time() - start, True)
            return meth
        except Exception as e:
            self._record_execution("propose_methodology", {}, time.time() - start, False, str(e))
            return {}

    def generate_report(self, data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Tool: generate_report(data) — Compiles ReportLab PDF and Markdown reports."""
        start = time.time()
        try:
            pdf_path = generate_pdf(data, output_path=output_path)
            generate_all_markdown_reports(data)
            self._record_execution("generate_report", {"pdf_path": pdf_path}, time.time() - start, True)
            return pdf_path
        except Exception as e:
            self._record_execution("generate_report", {}, time.time() - start, False, str(e))
            raise e

    def generate_presentation(self, data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Tool: generate_presentation(data) — Compiles 12-slide 16:9 PowerPoint deck."""
        start = time.time()
        try:
            ppt_path = generate_presentation(data, output_path=output_path)
            self._record_execution("generate_presentation", {"ppt_path": ppt_path}, time.time() - start, True)
            return ppt_path
        except Exception as e:
            self._record_execution("generate_presentation", {}, time.time() - start, False, str(e))
            raise e
