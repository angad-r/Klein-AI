"""
Web Research Agent for Klein AI — ResearchMate AI.
Orchestrates multi-query search, deduplication, webpage text extraction,
and accessibility tagging.
"""
import logging
from typing import List, Dict, Any, Optional
import config
from research.search import execute_multi_search
from research.extraction import enrich_sources

logger = logging.getLogger("KleinAI.Researcher")


def execute_research(
    queries: List[str],
    tavily_key: Optional[str] = None,
    depth: str = "Standard",
    status_callback=None,
) -> List[Dict[str, Any]]:
    """Performs web search and content enrichment."""
    depth_cfg = config.SEARCH_DEPTH_CONFIG.get(depth, config.SEARCH_DEPTH_CONFIG["Standard"])
    max_results = depth_cfg["results_per_query"]
    max_extract = depth_cfg["max_extract"]

    # 1. Search phase
    raw_sources = execute_multi_search(
        queries=queries,
        tavily_api_key=tavily_key,
        max_results_per_query=max_results,
        status_callback=status_callback,
    )

    if status_callback:
        status_callback(f"Collected {len(raw_sources)} unique sources. Extracting page bodies...")

    # 2. Webpage extraction phase
    enriched_sources = enrich_sources(
        raw_sources,
        max_to_extract=max_extract,
        status_callback=status_callback,
    )

    return enriched_sources
