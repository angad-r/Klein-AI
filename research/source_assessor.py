"""
Source Quality Assessor for KLEIN AI.
Evaluates collected sources for:
- Source Type Classification (Academic Preprint, Peer-reviewed, Official Tech Spec, Industry Report, Web News/Blog)
- Credibility Tier (High Authority, Peer Reviewed, Moderate, Requires Caution)
- Publication Date extraction / inference
- Author attribution
- Quality Assessment Rationale (explaining why a source is useful or requires caution)
- Relevance vs Credibility distinction
"""
import re
from urllib.parse import urlparse
from typing import Dict, Any, List


ACADEMIC_DOMAINS = {
    "arxiv.org": ("Preprint (ArXiv)", "High Authority - Academic Archive", 0.95),
    "openreview.net": ("Conference Review (OpenReview)", "High Authority - Peer Reviewed", 0.92),
    "aclanthology.org": ("Conference Proceedings (ACL)", "High Authority - Peer Reviewed", 0.96),
    "ieee.org": ("Journal/Conference (IEEE)", "High Authority - Peer Reviewed", 0.97),
    "acm.org": ("Digital Library (ACM)", "High Authority - Peer Reviewed", 0.97),
    "nature.com": ("Scientific Journal (Nature)", "High Authority - Top Tier Peer Reviewed", 0.99),
    "science.org": ("Scientific Journal (Science)", "High Authority - Top Tier Peer Reviewed", 0.99),
    "semanticscholar.org": ("Academic Index (Semantic Scholar)", "High Authority - Aggregator", 0.90),
    "ncbi.nlm.nih.gov": ("Biomedical Repository (PubMed/NIH)", "High Authority - Medical Peer Reviewed", 0.98),
    "biorxiv.org": ("Preprint (BioRxiv)", "High Authority - Academic Archive", 0.92),
    "medrxiv.org": ("Preprint (MedRxiv)", "High Authority - Academic Archive", 0.92),
    "springer.com": ("Academic Publisher (Springer)", "High Authority - Peer Reviewed", 0.94),
    "sciencedirect.com": ("Academic Publisher (Elsevier)", "High Authority - Peer Reviewed", 0.95),
    "wiley.com": ("Academic Publisher (Wiley)", "High Authority - Peer Reviewed", 0.94),
}

OFFICIAL_TECH_DOMAINS = {
    "github.com": ("Code Repository / Open Source", "Moderate Authority - Technical Artifact", 0.75),
    "nist.gov": ("Government Standards (NIST)", "High Authority - Official Standard", 0.96),
    "who.int": ("Global Agency (WHO)", "High Authority - Official Guideline", 0.95),
    "cisa.gov": ("Federal Cybersecurity (CISA)", "High Authority - Official Advisory", 0.95),
    "hhs.gov": ("Department of Health (HHS)", "High Authority - Government Regulatory", 0.95),
    "microsoft.com": ("Industry Whitepaper (Microsoft)", "Moderate Authority - Industry Tech", 0.80),
    "google.com": ("Industry Whitepaper (Google)", "Moderate Authority - Industry Tech", 0.80),
    "research.google": ("Corporate Research (Google Research)", "High Authority - Corporate R&D", 0.92),
    "openai.com": ("Corporate Research (OpenAI)", "Moderate to High Authority - Corporate R&D", 0.88),
    "anthropic.com": ("Corporate Research (Anthropic)", "Moderate to High Authority - Corporate R&D", 0.88),
    "deepmind.google": ("Corporate Research (Google DeepMind)", "High Authority - Corporate R&D", 0.93),
}


def assess_source_quality(source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes source type, authority score, credibility tier,
    and a specific quality assessment rationale.
    """
    url = source.get("url", "").strip()
    title = source.get("title", "").strip()
    content = source.get("content", source.get("snippet", ""))
    pub_date = source.get("published_date", "")

    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
    except Exception:
        domain = "web"

    source_type = "Web Article / Tech Blog"
    credibility_tier = "Moderate"
    authority_score = 0.65
    rationale = "General public web source. Findings should be cross-verified against peer-reviewed publications."

    # 1. Match known academic repositories
    for d, (s_type, tier, auth) in ACADEMIC_DOMAINS.items():
        if d in domain:
            source_type = s_type
            credibility_tier = tier
            authority_score = auth
            rationale = (
                f"Published or indexed on trusted academic repository ({d}). "
                "Highly credible for theoretical frameworks, formal empirical benchmarks, and peer evaluations."
            )
            break

    # 2. Match official tech/government agencies
    if authority_score == 0.65:
        for d, (s_type, tier, auth) in OFFICIAL_TECH_DOMAINS.items():
            if d in domain:
                source_type = s_type
                credibility_tier = tier
                authority_score = auth
                rationale = (
                    f"Official institutional or organizational domain ({d}). "
                    "Valuable for empirical deployment data, policy standards, or reference code implementations."
                )
                break

    # 3. Detect blog / news / generic domains
    if authority_score == 0.65:
        if any(term in domain for term in ["medium.com", "substack.com", "blogspot", "wordpress"]):
            source_type = "Independent Blog / Opinion"
            credibility_tier = "Requires Caution"
            authority_score = 0.45
            rationale = "Self-published editorial content. Lacks formal peer review; cite for illustrative or qualitative industry perspectives only."
        elif any(term in domain for term in ["techcrunch.com", "theverge.com", "wired.com", "forbes.com"]):
            source_type = "Technology Journalism"
            credibility_tier = "Moderate"
            authority_score = 0.70
            rationale = "Journalistic coverage. Good for industry timelines and qualitative narratives, but lacks rigorous experimental methodology."
        elif ".edu" in domain or ".ac." in domain or ".org" in domain:
            source_type = "Institutional / Non-Profit Portal"
            credibility_tier = "Moderate Authority"
            authority_score = 0.82
            rationale = "Hosted by an educational institution or non-profit organization."

    # Try extracting date if missing
    if not pub_date:
        date_match = re.search(r"\b(20[12][0-9])[-/.](0[1-9]|1[0-2])[-/.]([0-2][0-9]|3[01])\b", content[:1000])
        if date_match:
            pub_date = date_match.group(0)
        else:
            year_match = re.search(r"\b(201[89]|202[0-6])\b", content[:500])
            if year_match:
                pub_date = year_match.group(0)

    # Flag if content is very thin or inaccessible
    flags = []
    if not source.get("accessible", True):
        flags.append("Inaccessible / paywalled content (snippet only)")
    if len(content) < 150:
        flags.append("Limited content length (< 150 chars)")
    if authority_score < 0.60:
        flags.append("Unverified authorship / informal blog")

    return {
        "domain": domain,
        "source_type": source_type,
        "credibility_tier": credibility_tier,
        "authority_score": authority_score,
        "quality_rationale": rationale,
        "extracted_published_date": pub_date or "N/D",
        "quality_flags": flags,
        "is_peer_reviewed_or_official": authority_score >= 0.85,
    }


def enrich_sources_with_quality(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enriches all collected sources with quality assessment metadata."""
    for s in sources:
        assessment = assess_source_quality(s)
        s.update(assessment)
        if not s.get("published_date") and assessment.get("extracted_published_date") != "N/D":
            s["published_date"] = assessment["extracted_published_date"]
    
    # Sort by authority score descending
    return sorted(sources, key=lambda x: x.get("authority_score", 0.5), reverse=True)
