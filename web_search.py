"""
Backward compatibility wrapper for search operations.
Delegates to research.search and research.extraction.
"""
from research.search import execute_multi_search, search_tavily, search_fallback_ddg, deduplicate_sources
from research.extraction import extract_page_text, enrich_sources
