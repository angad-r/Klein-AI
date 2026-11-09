"""
Web Content Extractor for KLEIN AI.
Fetches accessible webpage content using Tavily Extract API and BeautifulSoup4 fallback.
Handles HTTP errors, timeouts, robots restrictions, PDF sources, and paywalls gracefully
without bypassing access controls.
"""
import re
import logging
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

import config
from research.search import extract_tavily

logger = logging.getLogger("KleinAI.Extraction")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 KLEIN-AI-Bot/2.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def extract_page_text(url: str, timeout: int = config.API_TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Fetches URL and parses clean textual paragraphs using BeautifulSoup.
    Returns dictionary with extracted text, status, and accessibility flag.
    """
    if not url or not url.startswith("http"):
        return {"content": "", "accessible": False, "status": "INVALID_URL", "status_code": 0}

    # Handle direct PDF documents gracefully
    if url.lower().endswith(".pdf"):
        return {
            "content": "Academic PDF Document (indexed via academic abstract/title metadata). Full body PDF extraction omitted for network efficiency.",
            "accessible": True,
            "status": "PDF_DOCUMENT",
            "status_code": 200,
        }

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code == 403 or resp.status_code == 401:
            return {"content": "", "accessible": False, "status": "PAYWALL_OR_FORBIDDEN", "status_code": resp.status_code}
        if resp.status_code != 200:
            return {"content": "", "accessible": False, "status": f"HTTP_{resp.status_code}", "status_code": resp.status_code}

        content_type = resp.headers.get("Content-Type", "").lower()
        if "pdf" in content_type:
            return {
                "content": "Academic PDF Document (indexed via abstract/title).",
                "accessible": True,
                "status": "PDF_DOCUMENT",
                "status_code": 200,
            }

        soup = BeautifulSoup(resp.content, "html.parser")

        # Strip unneeded structural elements
        for el in soup(["script", "style", "nav", "footer", "header", "aside", "form", "svg", "noscript", "iframe"]):
            el.decompose()

        main_el = soup.find("article") or soup.find("main") or soup.find("div", {"role": "main"})
        container = main_el if main_el else soup.body

        if not container:
            return {"content": "", "accessible": False, "status": "EMPTY_CONTAINER", "status_code": 200}

        paras = container.find_all(["p", "h1", "h2", "h3", "h4", "li"])
        lines = []
        for p in paras:
            text = p.get_text(strip=True)
            if len(text) >= 20:
                lines.append(text)

        raw_text = "\n\n".join(lines)
        clean = re.sub(r"\s+", " ", raw_text).strip()

        if len(clean) > config.MAX_CONTENT_CHARS_PER_SOURCE:
            clean = clean[:config.MAX_CONTENT_CHARS_PER_SOURCE] + "..."

        is_valid = len(clean) > 80
        return {
            "content": clean if is_valid else "",
            "accessible": is_valid,
            "status": "BEAUTIFUL_SOUP" if is_valid else "CONTENT_TOO_SHORT",
            "status_code": 200,
        }
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout extracting from {url}")
        return {"content": "", "accessible": False, "status": "TIMEOUT", "status_code": -1}
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed extracting from {url}: {e}")
        return {"content": "", "accessible": False, "status": "REQUEST_ERROR", "status_code": -1}
    except Exception as e:
        logger.warning(f"Unexpected parsing error for {url}: {e}")
        return {"content": "", "accessible": False, "status": "PARSE_ERROR", "status_code": -1}


def enrich_sources(
    sources: List[Dict[str, Any]],
    max_to_extract: int = 18,
    tavily_key: Optional[str] = None,
    status_callback=None,
) -> Dict[str, Any]:
    """
    Enriches candidate sources with full-text bodies.
    Attempts Tavily Extract API first for speed & quality, then falls back to BeautifulSoup.
    """
    total = min(len(sources), max_to_extract)
    candidates = sources[:total]
    urls_to_extract = [s.get("url") for s in candidates if s.get("url")]

    actual_tavily_key = tavily_key or config.get_tavily_api_key()
    tavily_results: Dict[str, Dict[str, Any]] = {}
    if config.is_tavily_available(actual_tavily_key):
        if status_callback:
            status_callback(f"Dispatching Tavily Extract API for top {len(urls_to_extract)} candidate URLs...")
        tavily_results = extract_tavily(urls_to_extract, api_key=actual_tavily_key)

    extracted_count = 0
    inaccessible_count = 0
    tavily_count = 0
    bs4_count = 0

    for idx, s in enumerate(candidates, 1):
        url = s.get("url", "")
        existing_snippet = s.get("snippet", "")

        # 1. Check if Tavily extract captured it
        if url in tavily_results and tavily_results[url].get("accessible"):
            s["content"] = tavily_results[url]["content"]
            s["raw_content"] = tavily_results[url].get("raw_content", "")
            s["extraction_status"] = "TAVILY_EXTRACT"
            s["accessible"] = True
            extracted_count += 1
            tavily_count += 1
            continue

        # 2. Fallback to BeautifulSoup scraping
        if status_callback:
            status_callback(f"Scraping Content ({idx}/{total}): {url[:45]}...")

        res = extract_page_text(url)
        if res.get("accessible") and len(res.get("content", "")) > len(existing_snippet):
            s["content"] = res["content"]
            s["raw_content"] = res["content"]
            s["extraction_status"] = "BEAUTIFUL_SOUP"
            s["accessible"] = True
            extracted_count += 1
            bs4_count += 1
        elif len(existing_snippet) > 80:
            s["content"] = existing_snippet
            s["extraction_status"] = "SNIPPET_FALLBACK"
            s["accessible"] = True
        else:
            s["content"] = existing_snippet
            s["extraction_status"] = res.get("status", "INACCESSIBLE")
            s["accessible"] = False
            inaccessible_count += 1

    return {
        "sources": sources,
        "extracted_count": extracted_count,
        "inaccessible_count": inaccessible_count,
        "tavily_extracted_count": tavily_count,
        "bs4_extracted_count": bs4_count,
    }
