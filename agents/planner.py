"""
Research Planner Agent for KLEIN AI.
Analyzes research topic, determines research domain, context, core problem,
objectives, formal research questions (RQ1-RQ4), thematic subtopics,
technical terminology, search strategy, expected evidence requirements,
and generates 8–12 diverse, topic-specific search queries.
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
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates comprehensive research plan and diverse search queries."""
    depth_cfg = config.SEARCH_DEPTH_CONFIG.get(depth, config.SEARCH_DEPTH_CONFIG["Standard"])
    num_queries = depth_cfg.get("initial_queries", 8)

    prompt = f"""
Act as a Principal Research Scientist and Academic Director.
Conduct a rigorous deep research planning session for the topic: "{topic}".
Research Depth Setting: {depth} (Generate at least {num_queries} diverse search queries).

Analyze the topic and return a strictly valid JSON object with the following fields:
1. "academic_title": A formal, publication-grade academic title.
2. "domain": Primary scientific or technical domain (e.g. Computer Vision in Precision Agriculture, Distributed Systems, Bioinformatics).
3. "research_context": 2-3 sentences summarizing the historical background and recent technological shifts leading to this topic.
4. "core_problem": Precise formulation of the primary technical, empirical, or theoretical bottleneck being addressed.
5. "scope_and_motivation": 2-3 sentences explaining why this topic is critical and what specific architectural scope is investigated.
6. "objectives": A list of 4 to 6 concrete, prioritized research objectives.
7. "research_questions": A list of 4 to 6 formal research questions (e.g., RQ1: ..., RQ2: ...).
8. "subtopics": A list of 4 to 6 distinct thematic pillars or subtopics covering theory, benchmarks, architectures, and deployment.
9. "technical_terminology": A list of 6 to 10 essential domain terms, evaluation metrics (e.g. mAP, F1, P99 Latency), and architectural mechanisms.
10. "search_strategy": A 2-sentence rationale detailing the multi-angle search strategy across surveys, benchmarks, failure modes, and recent advancements.
11. "expected_evidence_requirements": A list of 4 concrete empirical evidence requirements (e.g. quantitative benchmark tables, real-world deployment telemetry, ablation metrics).
12. "search_queries": A list of {num_queries} to 12 diverse, highly specific search queries designed for technical and academic search engines.
    Ensure queries are varied and investigate distinct aspects:
    - Query 1: Comprehensive state-of-the-art survey / review (2024-2026)
    - Query 2: Core algorithmic architecture and foundational mathematical/computational mechanisms
    - Query 3: Standardized datasets and empirical benchmarking evaluation
    - Query 4: Failure modes, edge cases, and robustness under non-stationary distributions
    - Query 5: Latency, compute footprint, and hardware efficiency trade-offs
    - Query 6: Comparative analysis against established baseline methodologies
    - Query 7: Real-world operational field deployments and telemetry
    - Query 8: Open research gaps, unresolved challenges, and future horizons

Return ONLY valid JSON.
"""
    if config.is_gemini_available(gemini_key):
        try:
            raw = call_gemini(
                prompt,
                api_key=gemini_key,
                model=model,
                system_instruction="You are a senior academic research planner. Always respond in valid JSON without markdown wrapping or commentary.",
            )
            data = extract_json_from_text(raw)
            if data and isinstance(data, dict) and "objectives" in data and "search_queries" in data:
                # Ensure search_queries is clean and deduplicated
                seen_q = set()
                clean_q = []
                for q in data.get("search_queries", []):
                    q_str = str(q).strip().strip('"').strip("'")
                    if q_str and q_str.lower() not in seen_q:
                        seen_q.add(q_str.lower())
                        clean_q.append(q_str)
                data["search_queries"] = clean_q
                return data
        except Exception as e:
            logger.warning(f"Gemini planner error: {e}. Using deterministic plan.")

    # High-quality, diverse fallback plan
    clean_topic = topic.strip()
    return {
        "academic_title": f"A Systematic Investigation into {clean_topic}: Architectures, Empirical Benchmarks, and Future Trajectories",
        "domain": "Artificial Intelligence & Applied Computational Systems",
        "research_context": (
            f"Recent advances in machine learning, distributed sensors, and algorithmic optimization have accelerated "
            f"inquiries into {clean_topic}. While initial implementations demonstrate theoretical viability, scalable "
            f"field deployments require rigorous multi-dimensional empirical validation."
        ),
        "core_problem": (
            f"The central bottleneck in {clean_topic} resides in balancing inference accuracy, computational latency, "
            f"and out-of-distribution robustness across non-stationary real-world environments."
        ),
        "scope_and_motivation": (
            f"This study investigates foundational mechanisms, empirical breakthroughs, and operational constraints "
            f"surrounding {clean_topic}, providing an evidence-backed synthesis for academic and practical deployments."
        ),
        "objectives": [
            f"Analyze theoretical frameworks and algorithmic foundations underpinning {clean_topic}.",
            f"Evaluate contemporary benchmarks and empirical performance of state-of-the-art implementations in {clean_topic}.",
            f"Identify critical bottlenecks, scalability challenges, and security/robustness implications.",
            f"Formulate a novel architectural paradigm and experimental validation framework for {clean_topic}.",
        ],
        "research_questions": [
            f"RQ1: What are the primary computational paradigms governing recent advances in {clean_topic}?",
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
        "technical_terminology": [
            "Empirical Benchmark",
            "Out-of-Distribution Generalization",
            "Inference Latency (P99)",
            "Ablation Analysis",
            "F1-Score / mAP",
            "Computational Complexity",
            "Parameter Efficiency",
            "Domain Adaptation",
        ],
        "search_strategy": (
            f"Multi-vector search examining peer-reviewed literature, benchmark comparisons, operational telemetry, "
            f"and architectural ablations for {clean_topic} across academic repositories and industry whitepapers."
        ),
        "expected_evidence_requirements": [
            "Standardized benchmark dataset evaluations with comparative baselines",
            "Ablation metrics quantifying accuracy versus inference speed",
            "Empirical reports documenting edge/field deployment challenges",
            "Peer-reviewed survey literature documenting existing theoretical boundaries",
        ],
        "search_queries": [
            f"{clean_topic} state of the art survey review 2024 2025 2026",
            f"{clean_topic} algorithmic architecture deep learning neural network",
            f"{clean_topic} empirical benchmark comparative analysis dataset",
            f"{clean_topic} robustness out of distribution edge cases failure modes",
            f"{clean_topic} inference latency computational efficiency hardware",
            f"{clean_topic} baseline comparison quantitative metrics ablation",
            f"{clean_topic} real world operational field telemetry evaluation",
            f"{clean_topic} challenges limitations research gaps future horizons",
        ][:max(num_queries, 4)],
    }
