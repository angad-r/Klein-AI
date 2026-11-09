"""
Web Search and Adaptive Research Engine for KLEIN AI.
Executes multi-round public web searches using Tavily API with content extraction,
domain diversity enforcement, URL normalization, query deduplication,
search coverage tracking, and public search fallback.
"""
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, Set
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
        return netloc if netloc else "web"
    except Exception:
        return "web"


def normalize_url(url: str) -> str:
    """Normalizes URL by stripping UTM/tracking parameters, fragments, lowercase domain, and trailing slashes."""
    try:
        from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        scheme = parsed.scheme.lower() or "https"
        # Filter out tracking query parameters
        tracking_keys = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term",
            "utm_content", "fbclid", "gclid", "ref", "source", "mc_cid", "mc_eid"
        }
        filtered_q = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in tracking_keys]
        new_query = urlencode(filtered_q)
        return urlunparse((scheme, netloc, path, "", new_query, ""))
    except Exception:
        return url.strip().rstrip("/")


def deduplicate_sources(
    sources: List[Dict[str, Any]],
    max_per_domain: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Deduplicates sources based on normalized URLs and normalized titles.
    Optionally enforces domain diversity by limiting sources from a single domain.
    """
    seen_urls: Set[str] = set()
    seen_titles: Set[str] = set()
    domain_counts: Dict[str, int] = {}
    unique: List[Dict[str, Any]] = []

    for s in sources:
        url = s.get("url", "").strip()
        title = s.get("title", "").strip().lower()
        norm = normalize_url(url) if url else ""
        dom = extract_domain(url)
        s["domain"] = dom

        if norm and norm in seen_urls:
            continue
        if title and title in seen_titles:
            continue

        if max_per_domain and domain_counts.get(dom, 0) >= max_per_domain:
            continue

        if norm:
            seen_urls.add(norm)
        if title:
            seen_titles.add(title)

        domain_counts[dom] = domain_counts.get(dom, 0) + 1
        unique.append(s)

    return unique


def verify_tavily_connection(api_key: str) -> Tuple[bool, str]:
    """Tests live Tavily connectivity without exposing credentials."""
    if not api_key or len(api_key.strip()) < 5:
        return False, "Tavily API key is missing or too short."
    try:
        client = TavilyClient(api_key=api_key.strip())
        res = client.search(query="test ping", max_results=1)
        if isinstance(res, dict) and "results" in res:
            return True, "Connected to Tavily Search API successfully."
        return False, "Unexpected response structure from Tavily."
    except Exception as e:
        err_str = str(e)
        if api_key in err_str:
            err_str = err_str.replace(api_key, "[REDACTED]")
        if "Unauthorized" in err_str or "401" in err_str or "invalid" in err_str.lower():
            return False, "Invalid API key: Tavily rejected the credential (401 Unauthorized)."
        if "429" in err_str or "limit" in err_str.lower():
            return False, "Quota exceeded: Tavily search limit reached."
        return False, f"Connection error: {err_str[:120]}"


def search_tavily(
    query: str,
    api_key: str,
    max_results: int = 5,
    search_depth: str = "advanced",
) -> List[Dict[str, Any]]:
    """Executes a real Tavily web search with retries and metadata enrichment."""
    if not api_key:
        raise ValueError("Tavily API key is missing.")

    client = TavilyClient(api_key=api_key.strip())
    retries = 0
    last_err = None
    retrieval_ts = datetime.now(timezone.utc).isoformat()

    while retries <= config.MAX_RETRIES:
        try:
            logger.info(f"Tavily search for query '{query[:40]}...' (attempt {retries + 1})...")
            res = client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_raw_content=False,
            )
            raw = res.get("results", [])
            formatted = []
            for item in raw:
                u = normalize_url(item.get("url", ""))
                raw_c = item.get("content", "")
                formatted.append({
                    "title": item.get("title", "Untitled Document"),
                    "url": u,
                    "domain": extract_domain(u),
                    "author": item.get("author", "Not stated"),
                    "published_date": item.get("published_date", ""),
                    "retrieval_date": retrieval_ts,
                    "query": query,
                    "snippet": raw_c,
                    "content": raw_c,
                    "raw_content": raw_c,
                    "score": float(item.get("score", 0.8)),
                    "source_engine": "Tavily Search API",
                    "extraction_status": "SNIPPET_FALLBACK",
                    "accessible": True,
                })
            return formatted
        except Exception as e:
            err_str = str(e)
            if api_key in err_str:
                err_str = err_str.replace(api_key, "[REDACTED]")
            last_err = err_str
            # Fast fail on 401 unauthorized to avoid hammering
            if "401" in err_str or "Unauthorized" in err_str:
                break
            retries += 1
            time.sleep(1.0)

    raise RuntimeError(f"Tavily search failed: {last_err}")


def search_fallback_ddg(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Fallback public search when Tavily key is omitted or rate limited."""
    try:
        from ddgs import DDGS
        logger.info(f"Public fallback search for '{query[:40]}...'")
        formatted = []
        retrieval_ts = datetime.now(timezone.utc).isoformat()
        with DDGS(timeout=6) as ddg:
            raw = list(ddg.text(query, max_results=max_results))
            for item in raw:
                u = item.get("href", item.get("url", ""))
                c = item.get("body", item.get("content", ""))
                formatted.append({
                    "title": item.get("title", "Untitled Document"),
                    "url": u,
                    "domain": extract_domain(u),
                    "author": "Not stated",
                    "published_date": "",
                    "retrieval_date": retrieval_ts,
                    "query": query,
                    "snippet": c,
                    "content": c,
                    "raw_content": c,
                    "score": 0.5,
                    "source_engine": "DuckDuckGo (Public Search)",
                    "extraction_status": "SNIPPET_FALLBACK",
                    "accessible": True,
                })
        return formatted
    except Exception as e:
        logger.error(f"Public fallback search error: {e}")
        return []


def extract_tavily(urls: List[str], api_key: str) -> Dict[str, Dict[str, Any]]:
    """
    Extracts full-page clean text using Tavily's extract API.
    Returns mapping of url -> {'content': str, 'status': str, 'raw_content': str}.
    """
    results: Dict[str, Dict[str, Any]] = {}
    if not api_key or not urls:
        return results

    try:
        client = TavilyClient(api_key=api_key.strip())
        # Tavily extract accepts a list of URLs (up to 20 per call)
        batch = [u for u in urls if u.startswith("http")][:15]
        if not batch:
            return results

        logger.info(f"Extracting {len(batch)} URLs via Tavily Extract API...")
        res = client.extract(urls=batch, timeout=config.TAVILY_EXTRACT_TIMEOUT)
        if isinstance(res, dict) and "results" in res:
            for item in res.get("results", []):
                u = item.get("url", "")
                raw_c = item.get("raw_content", "") or item.get("content", "")
                if raw_c and len(raw_c.strip()) > 80:
                    results[u] = {
                        "content": raw_c.strip()[:config.MAX_CONTENT_CHARS_PER_SOURCE],
                        "raw_content": raw_c.strip(),
                        "status": "TAVILY_EXTRACT",
                        "accessible": True,
                    }
    except Exception as e:
        err_str = str(e)
        if api_key in err_str:
            err_str = err_str.replace(api_key, "[REDACTED]")
        logger.warning(f"Tavily extract failed ({err_str[:80]}). Falling back to BeautifulSoup...")

    return results


def rank_and_prioritize_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ranks collected sources based on composite score: search score, domain tier, date presence, and content length."""
    def _compute_priority(s: Dict[str, Any]) -> float:
        base_score = float(s.get("score", 0.5))
        content_len = len(s.get("content", ""))
        has_date = 1.0 if s.get("published_date") else 0.0
        auth_score = float(s.get("authority_score", 0.6))
        # Weighting: 40% search score, 30% authority, 15% content length, 15% date
        len_factor = min(content_len / 2000.0, 1.0)
        return (base_score * 0.40) + (auth_score * 0.30) + (len_factor * 0.15) + (has_date * 0.15)

    return sorted(sources, key=_compute_priority, reverse=True)


class AdaptiveResearchEngine:
    """
    Multi-round autonomous research engine with query refinement,
    domain diversity enforcement, content extraction, and coverage tracking.
    """

    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        depth: str = "Standard",
        status_callback=None,
    ):
        self.tavily_key = tavily_api_key or config.get_tavily_api_key()
        self.depth = depth
        self.status_cb = status_callback
        self.depth_cfg = config.SEARCH_DEPTH_CONFIG.get(depth, config.SEARCH_DEPTH_CONFIG["Standard"])
        self.max_rounds = self.depth_cfg.get("max_rounds", 3)
        self.max_sources = self.depth_cfg.get("max_sources", 35)
        self.results_per_query = self.depth_cfg.get("results_per_query", 5)
        self.max_extract = self.depth_cfg.get("max_extract", 18)

        self.executed_queries: Set[str] = set()
        self.round_history: List[Dict[str, Any]] = []
        self.has_tavily = config.is_tavily_available(self.tavily_key)

    def _notify(self, message: str, progress: Optional[float] = None):
        if self.status_cb:
            self.status_cb(message, progress)
        logger.info(message)

    def execute_round(
        self,
        queries: List[str],
        round_num: int,
        existing_sources: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Executes a search round across new queries."""
        new_queries = [q.strip() for q in queries if q.strip() and q.strip().lower() not in self.executed_queries]
        if not new_queries:
            return existing_sources

        engine_name = "Tavily Search API" if self.has_tavily else "Public Search (Fallback)"
        self._notify(f"Iteration {round_num}/{self.max_rounds}: Executing {len(new_queries)} queries via {engine_name}...")

        batch_raw = []
        for idx, q in enumerate(new_queries, 1):
            self.executed_queries.add(q.lower())
            self._notify(f"Round {round_num} [{idx}/{len(new_queries)}]: Searching '{q[:45]}...'")

            results = []
            if self.has_tavily:
                try:
                    results = search_tavily(q, self.tavily_key, max_results=self.results_per_query)
                except Exception as e:
                    logger.warning(f"Tavily query failed ({e}); falling back to public search...")
                    results = search_fallback_ddg(q, max_results=self.results_per_query)
            else:
                results = search_fallback_ddg(q, max_results=self.results_per_query)

            batch_raw.extend(results)
            time.sleep(0.3)

        # Merge with existing, deduplicate, enforce domain diversity
        combined = existing_sources + batch_raw
        unique = deduplicate_sources(combined, max_per_domain=config.MAX_SOURCES_PER_DOMAIN)

        self.round_history.append({
            "round": round_num,
            "queries": new_queries,
            "raw_discovered": len(batch_raw),
            "total_unique": len(unique),
        })

        return unique

    def run_adaptive_search(
        self,
        topic: str,
        initial_queries: List[str],
        subtopics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes bounded multi-round search loop.
        Expands queries adaptively if source count or subtopic coverage is low.
        """
        collected_sources: List[Dict[str, Any]] = []

        # ROUND 1: Initial broad queries
        collected_sources = self.execute_round(initial_queries, round_num=1, existing_sources=[])

        # ROUND 2: Adaptive deepening if below target source count
        min_target = 6 if self.depth == "Quick" else 15
        if len(collected_sources) < min_target and self.max_rounds >= 2:
            self._notify(f"Source count ({len(collected_sources)}) below target ({min_target}). Formulating adaptive Round 2 deepening queries...")
            round_2_queries = [
                f"{topic} empirical benchmark comparative evaluation metrics",
                f"{topic} architectural mechanisms implementation dataset",
                f"{topic} failure modes edge cases robustness survey",
            ]
            if subtopics:
                for sub in subtopics[:2]:
                    round_2_queries.append(f"{topic} {sub} state of the art")

            collected_sources = self.execute_round(round_2_queries, round_num=2, existing_sources=collected_sources)

        # ROUND 3: Focused resolution for gaps if needed and depth allows
        if len(collected_sources) < (min_target + 5) and self.max_rounds >= 3:
            self._notify(f"Expanding coverage in Round 3 for empirical validation and survey synthesis...")
            round_3_queries = [
                f"{topic} arXiv IEEE ACM state of the art survey",
                f"{topic} ablation study latency throughput hardware efficiency",
            ]
            collected_sources = self.execute_round(round_3_queries, round_num=3, existing_sources=collected_sources)

        # Cap at max_sources
        final_sources = collected_sources[:self.max_sources]
        ranked_sources = rank_and_prioritize_sources(final_sources)

        return {
            "sources": ranked_sources,
            "total_sources": len(ranked_sources),
            "executed_queries": list(self.executed_queries),
            "round_history": self.round_history,
            "rounds_completed": len(self.round_history),
        }


def execute_multi_search(
    queries: List[str],
    tavily_api_key: Optional[str] = None,
    max_results_per_query: int = 5,
    status_callback=None,
) -> List[Dict[str, Any]]:
    """Legacy compatibility function for executing queries and deduplicating."""
    engine = AdaptiveResearchEngine(
        tavily_api_key=tavily_api_key,
        status_callback=status_callback,
    )
    res = engine.execute_round(queries, round_num=1, existing_sources=[])
    return deduplicate_sources(res)
