"""
Web Content Extractor for KLEIN AI.
Fetches accessible webpage content and parses textual bodies using BeautifulSoup4.
Marks inaccessible or restricted sources.
"""
import re
import logging
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

import config

logger = logging.getLogger("KleinAI.Extraction")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 KleinAI-KLEIN AI/1.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def extract_page_text(url: str, timeout: int = config.API_TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Fetches URL and parses clean paragraphs using BeautifulSoup.
    Returns dictionary with extracted text and accessibility flag.
    """
    if not url or not url.startswith("http"):
        return {"content": "", "accessible": False, "status_code": 0}

    # Skip direct PDF links from simple HTML parser
    if url.lower().endswith(".pdf"):
        return {"content": "Academic PDF Document (indexed via abstract/title)", "accessible": True, "status_code": 200}

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code != 200:
            return {"content": "", "accessible": False, "status_code": resp.status_code}

        soup = BeautifulSoup(resp.content, "html.parser")

        # Strip clutter
        for el in soup(["script", "style", "nav", "footer", "header", "aside", "form", "svg", "noscript", "iframe"]):
            el.decompose()

        main_el = soup.find("article") or soup.find("main") or soup.find("div", {"role": "main"})
        container = main_el if main_el else soup.body

        if not container:
            return {"content": "", "accessible": False, "status_code": 200}

        paras = container.find_all(["p", "h1", "h2", "h3", "h4", "li"])
        lines = []
        for p in paras:
            text = p.get_text(strip=True)
            if len(text) > 35:
                lines.append(text)

        raw_text = "\n\n".join(lines)
        clean = re.sub(r"\s+", " ", raw_text).strip()

        if len(clean) > config.MAX_CONTENT_CHARS_PER_SOURCE:
            clean = clean[:config.MAX_CONTENT_CHARS_PER_SOURCE] + "..."

        return {
            "content": clean if len(clean) > 80 else "",
            "accessible": True if len(clean) > 80 else False,
            "status_code": 200,
        }
    except Exception as e:
        logger.warning(f"Failed extracting from {url}: {e}")
        return {"content": "", "accessible": False, "status_code": -1}


def enrich_sources(
    sources: List[Dict[str, Any]],
    max_to_extract: int = 8,
    status_callback=None,
) -> List[Dict[str, Any]]:
    """Enriches sources with extracted full-text content."""
    enriched = []
    total = min(len(sources), max_to_extract)

    for idx, s in enumerate(sources[:total], 1):
        url = s.get("url", "")
        existing_snippet = s.get("snippet", "")

        if status_callback:
            status_callback(f"Scraping Content ({idx}/{total}): {url[:45]}...")

        res = extract_page_text(url)
        if res.get("accessible") and len(res.get("content", "")) > len(existing_snippet):
            s["content"] = res["content"]
            s["accessible"] = True
        else:
            s["content"] = existing_snippet
            s["accessible"] = True if len(existing_snippet) > 20 else False

        enriched.append(s)

    for s in sources[total:]:
        s["content"] = s.get("snippet", "")
        enriched.append(s)

    return enriched
