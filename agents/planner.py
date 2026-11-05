"""
Research Planner Agent for KLEIN AI.
Analyzes research topic, generates formal research objectives, research questions (RQ1-RQ4),
thematic subtopics, and targeted search queries.
"""
import logging
from typing import Dict, Any, List, Optional
import config
from agents.llm_utils import call_gemini, extract_json_from_text

logger = logging.getLogger("KleinAI.Planner")


def plan_research(
    topic: str,
    depth: str = "Standard",
    gemini_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates research plan and queries."""
    depth_cfg = config.SEARCH_DEPTH_CONFIG.get(depth, config.SEARCH_DEPTH_CONFIG["Standard"])
    num_queries = depth_cfg["queries"]

    prompt = f"""
Act as a Principal Research Scientist and Academic Director.
Analyze this research topic: "{topic}".
Research Depth Setting: {depth}.

Output a strictly valid JSON object with the following fields:
1. "academic_title": A formal, publication-grade academic title.
2. "domain": Primary scientific or technical domain.
3. "scope_and_motivation": 2-3 sentences explaining why this topic is critical and what scope is investigated.
4. "objectives": A list of 4 concrete research objectives.
5. "research_questions": A list of 4 formal research questions (e.g., RQ1: ..., RQ2: ...).
6. "subtopics": A list of 4 distinct thematic pillars/subtopics.
7. "search_queries": A list of {num_queries} diverse, precise search queries suitable for academic search engines (e.g. arXiv, IEEE, ACM, surveys, empirical benchmarks).

Return ONLY valid JSON.
"""
    if config.is_gemini_available(gemini_key):
        try:
            raw = call_gemini(
                prompt,
                api_key=gemini_key,
                system_instruction="You are a senior academic research planner. Always respond in valid JSON.",
            )
            data = extract_json_from_text(raw)
            if data and isinstance(data, dict) and "objectives" in data:
                return data
        except Exception as e:
            logger.warning(f"Gemini planner error: {e}. Using deterministic plan.")

    # High-quality fallback plan
    return {
        "academic_title": f"A Systematic Investigation into {topic}: Architectures, Empirical Benchmarks, and Future Trajectories",
        "domain": "Artificial Intelligence & Computational Systems",
        "scope_and_motivation": (
            f"This study investigates foundational mechanisms, empirical breakthroughs, and operational constraints "
            f"surrounding {topic}, providing an evidence-backed synthesis for academic and practical deployments."
        ),
        "objectives": [
            f"Analyze theoretical frameworks and algorithmic foundations underpinning {topic}.",
            f"Evaluate contemporary benchmarks and empirical performance of state-of-the-art implementations in {topic}.",
            f"Identify critical bottlenecks, scalability challenges, and security implications.",
            f"Propose a novel architectural paradigm and experimental validation framework for {topic}.",
        ],
        "research_questions": [
            f"RQ1: What are the primary computational paradigms governing recent advances in {topic}?",
            f"RQ2: How do current empirical methodologies perform across standardized benchmarks and real-world workloads?",
            f"RQ3: What unaddressed research gaps and technical bottlenecks hinder widespread deployment?",
            f"RQ4: What novel methodological framework can overcome these limitations?",
        ],
        "subtopics": [
            "Algorithmic Foundations & Theoretical Paradigms",
            "State-of-the-Art Benchmarks & Empirical Performance",
            "Scalability, Latency & Robustness Trade-offs",
            "Methodological Innovations & Future Frontiers",
        ],
        "search_queries": [
            f"{topic} state of the art survey review 2024 2025 2026",
            f"{topic} empirical benchmark comparative analysis architecture",
            f"{topic} challenges limitations research gaps",
            f"{topic} proposed methodology experimental evaluation",
        ][:num_queries],
    }
