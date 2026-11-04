"""
Web search engine for Klein AI — ResearchMate AI.
Executes public web searches using Tavily API with retry logic, rate limit handling,
and public fallback search.
"""
import time
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from tavily import TavilyClient

import config

logger = logging.getLogger("KleinAI.Search")
logging.basicConfig(level=logging.INFO)


def extract_domain(url: str) -> str:
    """Extracts clean domain name from URL."""
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return "web"


def normalize_url(url: str) -> str:
    """Normalizes URL by stripping UTM parameters, fragments, and trailing slashes."""
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return f"{parsed.scheme}://{netloc}{path}"
    except Exception:
        return url.strip().rstrip("/")


def deduplicate_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicates sources based on normalized URLs and normalized titles."""
    seen_urls = set()
    seen_titles = set()
    unique = []

    for s in sources:
        url = s.get("url", "").strip()
        title = s.get("title", "").strip().lower()
        norm = normalize_url(url) if url else ""

        if norm and norm in seen_urls:
            continue
        if title and title in seen_titles:
            continue

        if norm:
            seen_urls.add(norm)
        if title:
            seen_titles.add(title)

        s["domain"] = extract_domain(url)
        unique.append(s)

    return unique


def search_tavily(query: str, api_key: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Executes a real Tavily web search with retries."""
    if not api_key:
        raise ValueError("Tavily API key is missing.")

    client = TavilyClient(api_key=api_key)
    retries = 0
    last_err = None

    while retries <= config.MAX_RETRIES:
        try:
            logger.info(f"Tavily search for '{query}' (attempt {retries + 1})...")
            res = client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_raw_content=False,
            )
            raw = res.get("results", [])
            formatted = []
            for item in raw:
                formatted.append({
                    "title": item.get("title", "Untitled Document"),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.8),
                    "published_date": item.get("published_date", ""),
                    "source_engine": "Tavily Public Web",
                    "accessible": True,
                })
            return formatted
        except Exception as e:
            last_err = e
            retries += 1
            time.sleep(1.0)

    raise RuntimeError(f"Tavily search failed: {last_err}")


def search_fallback_ddg(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Fallback search when Tavily key is omitted or rate limited."""
    try:
        from ddgs import DDGS
        logger.info(f"Fallback search for '{query}'...")
        formatted = []
        with DDGS() as ddg:
            raw = list(ddg.text(query, max_results=max_results))
            for item in raw:
                formatted.append({
                    "title": item.get("title", "Untitled Document"),
                    "url": item.get("href", item.get("url", "")),
                    "snippet": item.get("body", item.get("content", "")),
                    "content": item.get("body", item.get("content", "")),
                    "score": 0.5,
                    "published_date": "",
                    "source_engine": "DuckDuckGo (Fallback)",
                    "accessible": True,
                })
        return formatted
    except Exception as e:
        logger.error(f"Fallback search error: {e}")
        return []


def execute_multi_search(
    queries: List[str],
    tavily_api_key: Optional[str] = None,
    max_results_per_query: int = 5,
    status_callback=None,
) -> List[Dict[str, Any]]:
    """Executes multi-query search and aggregates unique sources."""
    all_results = []
    has_tavily = bool(tavily_api_key and len(tavily_api_key.strip()) > 5)

    for idx, q in enumerate(queries, 1):
        if status_callback:
            engine = "Tavily Search" if has_tavily else "Public Search (Fallback)"
            status_callback(f"Executing Query {idx}/{len(queries)}: '{q[:40]}...' via {engine}")

        batch = []
        if has_tavily:
            try:
                batch = search_tavily(q, tavily_api_key, max_results=max_results_per_query)
            except Exception as e:
                logger.warning(f"Tavily query failed ({e}), falling back to DDG...")
                batch = search_fallback_ddg(q, max_results=max_results_per_query)
        else:
            batch = search_fallback_ddg(q, max_results=max_results_per_query)

        all_results.extend(batch)
        time.sleep(0.4)

    return deduplicate_sources(all_results)
