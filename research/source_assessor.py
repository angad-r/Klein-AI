"""
Source Quality Assessor for KLEIN AI.
Evaluates collected sources across 6 rigorous, explainable dimensions:
1. Relevance (semantic keyword density & domain alignment)
2. Authority (domain standing, archival status, organizational rigor)
3. Publication Transparency (author attribution, institutional publisher, date disclosure)
4. Recency (chronological timeliness)
5. Methodological Detail (empirical setup, baselines, metric reporting)
6. Evidence Availability (quantitative data, tables, numerical results)

Clearly distinguishes:
- Academic Publications
- Government Publications
- Institutional Reports
- News Articles
- Commercial Websites
- Other Web Sources

Enforces: Relevance != Credibility. Never claims peer review unless verified.
"""
import re
from urllib.parse import urlparse
from typing import Dict, Any, List

# Verified peer-reviewed academic databases and publisher repositories
VERIFIED_PEER_REVIEWED_DOMAINS = {
    "ieee.org": ("Journal/Conference (IEEE)", "High Authority - Peer Reviewed", 0.97, "Academic Publication"),
    "acm.org": ("Digital Library (ACM)", "High Authority - Peer Reviewed", 0.97, "Academic Publication"),
    "nature.com": ("Scientific Journal (Nature)", "High Authority - Top Tier Peer Reviewed", 0.99, "Academic Publication"),
    "science.org": ("Scientific Journal (Science)", "High Authority - Top Tier Peer Reviewed", 0.99, "Academic Publication"),
    "sciencedirect.com": ("Academic Publisher (Elsevier)", "High Authority - Peer Reviewed", 0.95, "Academic Publication"),
    "springer.com": ("Academic Publisher (Springer)", "High Authority - Peer Reviewed", 0.94, "Academic Publication"),
    "wiley.com": ("Academic Publisher (Wiley)", "High Authority - Peer Reviewed", 0.94, "Academic Publication"),
    "ncbi.nlm.nih.gov": ("Biomedical Repository (PubMed/NIH)", "High Authority - Medical Peer Reviewed", 0.98, "Academic Publication"),
    "aclanthology.org": ("Conference Proceedings (ACL)", "High Authority - Peer Reviewed", 0.96, "Academic Publication"),
    "openreview.net": ("Conference Review (OpenReview)", "High Authority - Peer Reviewed", 0.92, "Academic Publication"),
    "frontiersin.org": ("Academic Publisher (Frontiers)", "High Authority - Peer Reviewed", 0.93, "Academic Publication"),
    "tandfonline.com": ("Taylor & Francis Online", "High Authority - Peer Reviewed", 0.94, "Academic Publication"),
    "mdpi.com": ("Academic Publisher (MDPI)", "Moderate to High Authority - Open Access", 0.88, "Academic Publication"),
}

# Academic Preprints & Repositories (Academic, High Authority, but not yet formal journal peer-reviewed)
ACADEMIC_PREPRINT_DOMAINS = {
    "arxiv.org": ("Preprint (ArXiv)", "High Authority - Academic Archive", 0.95, "Academic Publication"),
    "biorxiv.org": ("Preprint (BioRxiv)", "High Authority - Academic Archive", 0.92, "Academic Publication"),
    "medrxiv.org": ("Preprint (MedRxiv)", "High Authority - Academic Archive", 0.92, "Academic Publication"),
    "semanticscholar.org": ("Academic Index (Semantic Scholar)", "High Authority - Aggregator", 0.90, "Academic Publication"),
    "researchgate.net": ("Academic Network (ResearchGate)", "Moderate Authority - Self-Archived", 0.82, "Academic Publication"),
}

# Official Government & Standards Agencies
GOVERNMENT_DOMAINS = {
    "nist.gov": ("Government Standards (NIST)", "High Authority - Official Standard", 0.96, "Government Publication"),
    "who.int": ("Global Agency (WHO)", "High Authority - Official Guideline", 0.95, "Government Publication"),
    "cisa.gov": ("Federal Cybersecurity (CISA)", "High Authority - Official Advisory", 0.95, "Government Publication"),
    "hhs.gov": ("Department of Health (HHS)", "High Authority - Government Regulatory", 0.95, "Government Publication"),
    "nih.gov": ("National Institutes of Health (NIH)", "High Authority - Government Health", 0.97, "Government Publication"),
    "usda.gov": ("Department of Agriculture (USDA)", "High Authority - Government Agricultural", 0.96, "Government Publication"),
    "fao.org": ("Food & Agriculture Organization (UN FAO)", "High Authority - International Agency", 0.95, "Government Publication"),
    "europa.eu": ("European Union Portal (EU)", "High Authority - Official Government", 0.95, "Government Publication"),
}

# Corporate Research Labs & Major Technical Organizations
CORPORATE_R_AND_D_DOMAINS = {
    "research.google": ("Corporate Research (Google Research)", "High Authority - Corporate R&D", 0.92, "Institutional Report"),
    "deepmind.google": ("Corporate Research (Google DeepMind)", "High Authority - Corporate R&D", 0.93, "Institutional Report"),
    "openai.com": ("Corporate Research (OpenAI)", "Moderate to High Authority - Corporate R&D", 0.88, "Institutional Report"),
    "anthropic.com": ("Corporate Research (Anthropic)", "Moderate to High Authority - Corporate R&D", 0.88, "Institutional Report"),
    "meta.com": ("Corporate Research (Meta AI)", "Moderate to High Authority - Corporate R&D", 0.86, "Institutional Report"),
    "microsoft.com": ("Industry Whitepaper (Microsoft)", "Moderate Authority - Industry Tech", 0.82, "Institutional Report"),
    "ibm.com": ("Corporate Research (IBM Research)", "Moderate to High Authority - Corporate R&D", 0.85, "Institutional Report"),
    "github.com": ("Code Repository / Open Source", "Moderate Authority - Technical Artifact", 0.75, "Institutional Report"),
}


def assess_source_quality(source: Dict[str, Any], topic: str = "") -> Dict[str, Any]:
    """
    Evaluates a source across 6 explainable dimensions:
    1. Relevance
    2. Authority
    3. Publication Transparency
    4. Recency
    5. Methodological Detail
    6. Evidence Availability
    """
    url = source.get("url", "").strip()
    title = source.get("title", "").strip()
    content = source.get("content", source.get("snippet", ""))
    pub_date = source.get("published_date", "")
    author = source.get("author", "").strip()

    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
    except Exception:
        domain = "web"

    # -------------------------------------------------------------
    # Classification & Authority Scoring
    # -------------------------------------------------------------
    source_type = "Web Article / Tech Blog"
    credibility_tier = "Moderate"
    authority_score = 0.65
    source_category = "Other Web Source"
    is_peer_reviewed = False
    rationale = "General public web source. Findings should be cross-verified against peer-reviewed publications."

    # 1. Match Verified Peer-Reviewed Publications
    for d, (s_type, tier, auth, cat) in VERIFIED_PEER_REVIEWED_DOMAINS.items():
        if d in domain:
            source_type = s_type
            credibility_tier = tier
            authority_score = auth
            source_category = cat
            is_peer_reviewed = True
            rationale = (
                f"Published in vetted peer-reviewed academic literature ({d}). "
                "Highest methodological rigor, formal empirical benchmarks, and peer evaluations."
            )
            break

    # 2. Match Academic Preprints & Archives
    if not is_peer_reviewed:
        for d, (s_type, tier, auth, cat) in ACADEMIC_PREPRINT_DOMAINS.items():
            if d in domain:
                source_type = s_type
                credibility_tier = tier
                authority_score = auth
                source_category = cat
                is_peer_reviewed = False
                rationale = (
                    f"Indexed on academic preprint/archive repository ({d}). "
                    "Scholarly pre-publication with rigorous academic structure; awaiting formal peer review."
                )
                break

    # 3. Match Government & Standards Agencies
    if source_category == "Other Web Source":
        for d, (s_type, tier, auth, cat) in GOVERNMENT_DOMAINS.items():
            if d in domain:
                source_type = s_type
                credibility_tier = tier
                authority_score = auth
                source_category = cat
                is_peer_reviewed = False
                rationale = (
                    f"Official government or international regulatory standard ({d}). "
                    "Highly authoritative for baseline standards, legal compliance, and field surveys."
                )
                break

    # 4. Match Corporate R&D & Technical Whitepapers
    if source_category == "Other Web Source":
        for d, (s_type, tier, auth, cat) in CORPORATE_R_AND_D_DOMAINS.items():
            if d in domain:
                source_type = s_type
                credibility_tier = tier
                authority_score = auth
                source_category = cat
                is_peer_reviewed = False
                rationale = (
                    f"Published by major industrial technical laboratory ({d}). "
                    "Authoritative engineering benchmarks, architecture specifications, and open-source models."
                )
                break

    # 5. Generic domain patterns (.edu, .gov, journalism, blog, commercial)
    if source_category == "Other Web Source":
        if any(term in domain for term in ["medium.com", "substack.com", "blogspot", "wordpress"]):
            source_type = "Independent Blog / Opinion"
            credibility_tier = "Requires Caution"
            authority_score = 0.45
            source_category = "Other Web Source"
            rationale = "Self-published editorial content. Lacks formal peer review or editorial oversight; cite for qualitative perspectives only."
        elif any(term in domain for term in ["techcrunch.com", "theverge.com", "wired.com", "forbes.com", "reuters.com", "bloomberg.com"]):
            source_type = "Technology Journalism"
            credibility_tier = "Moderate"
            authority_score = 0.70
            source_category = "News Article"
            rationale = "Journalistic coverage. Valuable for industry timelines and event narratives, but lacks granular experimental reproducibility."
        elif ".edu" in domain or ".ac." in domain:
            source_type = "Institutional / University Portal"
            credibility_tier = "Moderate Authority"
            authority_score = 0.85
            source_category = "Institutional Report"
            rationale = "Hosted by an accredited university or academic institution."
        elif ".gov" in domain:
            source_type = "Government Publication"
            credibility_tier = "High Authority"
            authority_score = 0.94
            source_category = "Government Publication"
            rationale = "Official public sector portal."
        elif ".org" in domain:
            source_type = "Non-Profit / Organizational Portal"
            credibility_tier = "Moderate Authority"
            authority_score = 0.80
            source_category = "Institutional Report"
            rationale = "Published by a registered non-profit organization."
        elif ".com" in domain or ".io" in domain or ".ai" in domain:
            source_type = "Commercial Tech Site"
            credibility_tier = "Moderate"
            authority_score = 0.60
            source_category = "Commercial Website"
            rationale = "Commercial web entity. May contain product-aligned perspectives; findings require corroboration against academic sources."

    # -------------------------------------------------------------
    # 6-Dimension Structured Scoring
    # -------------------------------------------------------------
    full_text_lower = (title + " " + content).lower()

    # Dimension 1: Relevance Score
    # Evaluates presence of core topic keywords
    relevance_score = 0.60
    if topic:
        topic_words = [w.lower() for w in re.findall(r"\b[A-Za-z]{3,}\b", topic)]
        match_count = sum(1 for w in topic_words if w in full_text_lower)
        relevance_score = min(0.50 + (match_count / max(len(topic_words), 1) * 0.50), 1.0)
    else:
        relevance_score = 0.75

    # Dimension 2: Authority Score (already determined via domain standing)
    # Scaled to 0.0 - 1.0

    # Dimension 3: Publication Transparency
    transparency_score = 0.50
    has_author = bool(author and author.lower() not in ["not stated", "unknown", "admin", "n/a"])
    if has_author:
        transparency_score += 0.25
    if pub_date:
        transparency_score += 0.25

    # Try extracting date if missing
    if not pub_date:
        date_match = re.search(r"\b(20[12][0-9])[-/.](0[1-9]|1[0-2])[-/.]([0-2][0-9]|3[01])\b", content[:1000])
        if date_match:
            pub_date = date_match.group(0)
            transparency_score += 0.20
        else:
            year_match = re.search(r"\b(201[89]|202[0-6])\b", content[:500])
            if year_match:
                pub_date = year_match.group(0)
                transparency_score += 0.15

    # Dimension 4: Recency Score
    recency_score = 0.50
    if pub_date:
        if any(yr in pub_date for yr in ["2025", "2026"]):
            recency_score = 1.00
        elif "2024" in pub_date:
            recency_score = 0.95
        elif "2023" in pub_date:
            recency_score = 0.85
        elif "2022" in pub_date:
            recency_score = 0.75
        elif any(yr in pub_date for yr in ["2020", "2021"]):
            recency_score = 0.65
        else:
            recency_score = 0.50

    # Dimension 5: Methodological Detail Score
    method_keywords = [
        "methodology", "dataset", "benchmark", "accuracy", "latency", "baseline",
        "evaluation", "metrics", "experiment", "sample size", "ablation", "f1",
        "precision", "recall", "architecture", "training", "parameter"
    ]
    method_matches = sum(1 for kw in method_keywords if kw in full_text_lower)
    method_score = min(0.40 + (method_matches * 0.07), 1.0)

    # Dimension 6: Evidence Availability Score
    # Checks for presence of quantitative empirical evidence (percentages, metrics, numerical tokens)
    num_matches = len(re.findall(r"\b[0-9]+(?:\.[0-9]+)?%?\b", content))
    evidence_score = min(0.45 + (min(num_matches, 10) * 0.055), 1.0)

    # Explainable Dimension Dictionary
    dimension_scores = {
        "relevance": round(relevance_score, 2),
        "authority": round(authority_score, 2),
        "transparency": round(transparency_score, 2),
        "recency": round(recency_score, 2),
        "methodology": round(method_score, 2),
        "evidence_availability": round(evidence_score, 2),
    }

    dimension_explanations = {
        "relevance": f"Relevance Score: {dimension_scores['relevance']} (Semantic alignment with topic objectives).",
        "authority": f"Authority Score: {dimension_scores['authority']} (Institutional & domain credibility: {domain}).",
        "transparency": f"Transparency Score: {dimension_scores['transparency']} (Author disclosure: {'Yes' if has_author else 'No'}, Date: {pub_date or 'N/D'}).",
        "recency": f"Recency Score: {dimension_scores['recency']} (Published timeline: {pub_date or 'Undated'}).",
        "methodology": f"Methodological Detail: {dimension_scores['methodology']} (Found {method_matches} experimental/benchmark indicators).",
        "evidence_availability": f"Evidence Availability: {dimension_scores['evidence_availability']} (Found {num_matches} quantitative data points).",
    }

    # Quality Flags
    flags = []
    if not source.get("accessible", True):
        flags.append("Restricted access / paywalled content (snippet only)")
    if len(content) < 150:
        flags.append("Limited content excerpt (< 150 chars)")
    if authority_score < 0.60:
        flags.append("Informal or self-published domain")
    if not is_peer_reviewed and source_category == "Academic Publication":
        flags.append("Preprint repository; awaiting formal peer validation")

    return {
        "domain": domain,
        "source_type": source_type,
        "source_category": source_category,
        "credibility_tier": credibility_tier,
        "authority_score": authority_score,
        "peer_reviewed_verified": is_peer_reviewed,
        "is_peer_reviewed_or_official": authority_score >= 0.85,
        "quality_rationale": rationale,
        "extracted_published_date": pub_date or "N/D",
        "quality_dimensions": dimension_scores,
        "dimension_scores": dimension_scores,
        "dimension_explanations": dimension_explanations,
        "quality_flags": flags,
    }


def enrich_sources_with_quality(
    sources: List[Dict[str, Any]],
    topic: str = "",
) -> List[Dict[str, Any]]:
    """Enriches all collected sources with 6-dimension quality assessment metadata."""
    for s in sources:
        assessment = assess_source_quality(s, topic=topic)
        s.update(assessment)
        if not s.get("published_date") and assessment.get("extracted_published_date") != "N/D":
            s["published_date"] = assessment["extracted_published_date"]

    # Sort by authority score descending
    return sorted(sources, key=lambda x: x.get("authority_score", 0.5), reverse=True)
