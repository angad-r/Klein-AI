"""
Methodology Agent for KLEIN AI.
Generates structured empirical research methodology:
- Research Design & Research Approach
- Formal Hypotheses
- Dataset Requirements & Collection Protocols
- Independent & Dependent Variables
- Proposed Experimental Validation Suite (explicitly marked as proposed protocols)
- Quantitative Evaluation Metrics
- Expected Limitations
"""
import json
import logging
from typing import Dict, Any, List, Optional
import config
from agents.llm_utils import call_gemini, extract_json_from_text

logger = logging.getLogger("KleinAI.Methodology")


def propose_methodology(
    topic: str,
    gaps: List[Dict[str, Any]],
    gemini_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates comprehensive structured methodology addressing identified gaps."""
    gaps_str = "\n".join([f"- {g.get('gap_title', '')}: {g.get('explanation', '')}" for g in gaps])

    prompt = f"""
Act as a Principal Research Architect. Design an empirical research methodology addressing these literature gaps in "{topic}":
{gaps_str}

Return a valid JSON object with:
1. "framework_name": Formal name of proposed architecture (e.g. "Decoupled Adaptive Architecture (DAA) for ...")
2. "research_design": Formal design (e.g., Experimental quantitative ablation study, multi-baseline comparative benchmarking)
3. "research_approach": Methodological approach (e.g., Design Science Research, Empirical Quantitative Modeling)
4. "hypotheses": A list of 3 formal scientific hypotheses ($H_1, H_2, H_3$)
5. "dataset_requirements": Specification of datasets needed (sizes, modalities, class balances, noise levels)
6. "data_collection_methods": Protocols for ingesting, validating, and preprocessing benchmark data
7. "variables":
   - "independent_variables": Manipulated factors (e.g. model capacity, routing sparsity, noise perturbation levels)
   - "dependent_variables": Measured outcomes (e.g. latency ms, throughput QPS, F1 score, peak VRAM)
   - "control_variables": Controlled factors (hardware environment, batch size, seed)
8. "workflow_stages": A list of 4 sequential workflow execution stages
9. "proposed_experiments": A list of 3 concrete PROPOSED validation experiments:
   - "experiment_id": e.g. "EXP-01"
   - "name": Experiment title
   - "hypothesis": Precise hypothesis to test
   - "target_datasets": Specific suggested datasets or benchmarks
   - "baseline_models": Baselines for comparative benchmarking
   - "evaluation_metrics": Exact quantitative metrics (e.g., P99 latency ms, F1-score, QPS, FLOPs)
   - "validation_status": "Proposed Protocol (Pending Empirical Execution)"
10. "expected_contributions": A list of 4 key academic contributions
11. "expected_limitations": A list of 3 acknowledged technical or resource constraints

Return ONLY valid JSON.
"""
    if config.is_gemini_available(gemini_key):
        try:
            raw = call_gemini(prompt, api_key=gemini_key)
            data = extract_json_from_text(raw)
            if data and isinstance(data, dict) and "proposed_experiments" in data:
                return data
        except Exception as e:
            logger.warning(f"Gemini methodology failed: {e}. Using deterministic methodology.")

    # High-grade fallback structured methodology
    return {
        "framework_name": f"Decoupled Adaptive Framework (DAF) for {topic}",
        "research_design": "Empirical quantitative benchmarking, factorial ablation analysis, and stress-testing under non-stationary distributions.",
        "research_approach": "Empirical Quantitative Modeling coupled with Design Science Systems Engineering.",
        "hypotheses": [
            f"H1: Modular architectural decoupling reduces P99 inference latency in {topic} by >= 30% under high-concurrency request arrival rates.",
            "H2: Dynamic routing regularizers preserve >= 88% baseline benchmark accuracy under structured out-of-distribution noise perturbations.",
            "H3: Sub-component ablation confirms each architectural layer yields statistically significant improvements (p < 0.01) to global utility.",
        ],
        "dataset_requirements": "Multi-domain benchmark suites totaling >= 50,000 samples, spanning clean validation partitions and structured synthetic noise distributions.",
        "data_collection_methods": "Automated ingestion via standardized APIs, cryptographic hash deduplication, stratified validation splitting (70/15/15), and distribution normalization.",
        "variables": {
            "independent_variables": [
                "Architectural Modularity (Decoupled vs Monolithic End-to-End)",
                "Input Perturbation Severity (Gaussian Noise, Semantic Domain Shift)",
                "Routing Sparsity & Context Compression Coefficients",
            ],
            "dependent_variables": [
                "P99 & P50 Inference Latency (milliseconds)",
                "System Throughput (Queries Per Second, QPS)",
                "Task Accuracy, Precision, Recall & F1-Score",
                "Peak GPU Memory Footprint (VRAM in MB)",
            ],
            "control_variables": [
                "Host Accelerator Hardware (NVIDIA A100/H100 80GB)",
                "Inference Batch Size (Fixed at 1, 8, 32 across runs)",
                "Random Seed Initialization (Averaged across 5 distinct seeds)",
            ],
        },
        "workflow_stages": [
            "Stage 1: Multi-Source Benchmark Corpus Ingestion & Standardization",
            "Stage 2: Core Algorithmic Formulation & Decoupled Architectural Modeling",
            "Stage 3: Full-Scale Comparative Benchmarking & Factorial Ablation Analysis",
            "Stage 4: Stress-Testing, Adversarial Robustness Auditing & Statistical Validation",
        ],
        "proposed_experiments": [
            {
                "experiment_id": "EXP-01",
                "name": "Throughput and Latency Scalability Stress-Test",
                "hypothesis": "The decoupled adaptive framework reduces P99 latency by >= 35% compared to monolithic baselines without statistically significant fidelity loss (p < 0.05).",
                "target_datasets": "Standardized academic benchmarking partitions and synthetic high-concurrency request streams.",
                "baseline_models": "Current monolithic state-of-the-art implementations.",
                "evaluation_metrics": "P99 Latency (ms), Queries Per Second (QPS), Peak VRAM (GB)",
                "validation_status": "Proposed Protocol (Pending Empirical Execution)",
            },
            {
                "experiment_id": "EXP-02",
                "name": "Out-of-Distribution Robustness and Perturbation Evaluation",
                "hypothesis": "Dynamic routing layers preserve >= 88% baseline benchmark accuracy when exposed to structured adversarial noise perturbations.",
                "target_datasets": "Perturbation test suites incorporating noise injection and cross-domain data shifts.",
                "baseline_models": "Standard non-adaptive baseline and unregularized ablation variants.",
                "evaluation_metrics": "Robust F1-Score, Error Rate Degradation Ratio, Uncertainty Calibration Error",
                "validation_status": "Proposed Protocol (Pending Empirical Execution)",
            },
            {
                "experiment_id": "EXP-03",
                "name": "Component-Wise Factorial Ablation Analysis",
                "hypothesis": "Each modular sub-component (routing, context compression, calibration) contributes a statistically measurable performance increment to the global utility function.",
                "target_datasets": "Standardized validation benchmark partition.",
                "baseline_models": "Systematically ablated sub-variants isolating individual modules.",
                "evaluation_metrics": "Component Utility Delta, Parameter Efficiency, Normalized Training FLOPs",
                "validation_status": "Proposed Protocol (Pending Empirical Execution)",
            },
        ],
        "expected_contributions": [
            f"A novel conceptual architecture addressing core scalability and latency bottlenecks in {topic}.",
            "A comprehensive, reproducible open-source evaluation suite with standardized multi-baseline harnesses.",
            "Empirical evidence defining performance trade-offs under heterogeneous computational constraints.",
            "Actionable design guidelines and error taxonomies for academic and industrial researchers.",
        ],
        "expected_limitations": [
            "Validation requires substantial GPU cluster resources for prolonged stress-testing.",
            "Hyperparameter sensitivity during extreme noise regimes necessitates ongoing tuning.",
            "Current evaluation scope is tailored primarily to standardized English and high-resource benchmarks.",
        ],
    }
