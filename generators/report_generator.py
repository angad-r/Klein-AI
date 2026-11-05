"""
Report Generator for KLEIN AI.
Produces publication-grade Markdown artifacts formatted into 17 academic sections:
1. Title Page / Header
2. Abstract
3. Keywords
4. Introduction
5. Background & Motivation
6. Problem Statement
7. Research Objectives
8. Research Questions
9. Synthesized Literature Review
10. Comparative Analysis & Synthesis
11. Critical Research Gaps (7 dimensions)
12. Proposed Methodology & Architecture
13. Proposed Experimental Validation Suite
14. Expected Contributions
15. Limitations
16. Conclusion
17. Bibliographic References & Citation Audit
"""
from pathlib import Path
from typing import Dict, Any
import config


def generate_all_markdown_reports(report_data: Dict[str, Any], output_dir: Path = None) -> Dict[str, str]:
    """Generates all specified markdown files."""
    out = output_dir or config.OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    title = report_data.get("title", "Autonomous Academic Research Report")
    topic = report_data.get("topic", "")
    abstract = report_data.get("abstract", "")
    keywords = ", ".join(report_data.get("keywords", [topic, "Empirical Evaluation", "Artificial Intelligence"]))
    intro = report_data.get("introduction", "")
    scope = report_data.get("scope_and_motivation", "")
    problem_statement = report_data.get("problem_statement", "")
    objectives = "\n".join([f"- {o}" for o in report_data.get("objectives", [])])
    questions = "\n".join([f"- **{q}**" for q in report_data.get("research_questions", [])])
    lit_review = report_data.get("literature_review", "")
    comparative = "\n".join([f"- {c}" for c in report_data.get("comparative_analysis", [])])
    consensus = "\n".join([f"- {c}" for c in report_data.get("consensus_points", [])])
    conflicts = "\n".join([f"- {c}" for c in report_data.get("conflicting_evidence", [])])

    # Gaps (7 dimensions)
    gaps = report_data.get("research_gaps", [])
    gaps_md = []
    for g in gaps:
        supp = ", ".join(g.get("supporting_sources", [])) or "Identified in collected literature"
        gaps_md.append(
            f"### {g.get('gap_id', 'GAP')}: {g.get('gap_title', g.get('title', ''))}\n"
            f"- **Explanation:** {g.get('explanation', g.get('description', ''))}\n"
            f"- **Supporting Sources:** {supp}\n"
            f"- **Why It Matters:** {g.get('why_it_matters', g.get('impact', ''))}\n"
            f"- **Suggested Research Question:** {g.get('suggested_research_question', 'N/A')}\n"
            f"- **Possible Methodology:** {g.get('possible_methodology', g.get('future_direction', ''))}\n"
            f"- **Feasibility:** `{g.get('feasibility', 'Moderate')}`\n"
        )
    gaps_text = "\n".join(gaps_md)

    methodology = report_data.get("methodology", {})
    workflow = "\n".join([f"1. {s}" for s in methodology.get("workflow_stages", [])])
    hypotheses = "\n".join([f"- **{h}**" for h in methodology.get("hypotheses", [])])

    vars_dict = methodology.get("variables", {})
    indep_vars = "\n".join([f"- {v}" for v in vars_dict.get("independent_variables", [])])
    dep_vars = "\n".join([f"- {v}" for v in vars_dict.get("dependent_variables", [])])

    experiments = report_data.get("proposed_experiments", [])
    exp_md = []
    for exp in experiments:
        exp_md.append(
            f"#### {exp.get('experiment_id', 'EXP')}: {exp.get('name', 'Proposed Experiment')}\n"
            f"> *Validation Status: {exp.get('validation_status', 'Proposed Protocol')}*\n\n"
            f"- **Hypothesis:** {exp.get('hypothesis', '')}\n"
            f"- **Target Datasets / Workloads:** {exp.get('target_datasets', '')}\n"
            f"- **Baseline Models:** {exp.get('baseline_models', '')}\n"
            f"- **Evaluation Metrics:** {exp.get('evaluation_metrics', '')}\n"
        )
    exp_text = "\n".join(exp_md)

    # Evidence items table
    evidence_items = report_data.get("evidence_items", [])
    ev_rows = []
    for ev in evidence_items:
        conf_badge = f"`{ev.get('confidence', 'Supported')}`"
        ev_rows.append(
            f"| [{ev.get('citation_index', 1)}] {ev.get('source_title', '')[:35]}... | "
            f"{ev.get('claim', '')} | "
            f"{ev.get('evidence', '')[:90]}... | "
            f"{conf_badge} |"
        )
    ev_table = (
        "| Source | Empirical Claim | Extracted Evidence Passage | Confidence |\n"
        "|---|---|---|---|\n"
        + "\n".join(ev_rows)
    )

    contributions = "\n".join([f"- {c}" for c in report_data.get("expected_contributions", [])])
    limitations = "\n".join([f"- {l}" for l in report_data.get("limitations", [])])
    conclusion = report_data.get("conclusion", "")

    references = report_data.get("references", [])
    refs_md = []
    for r in references:
        status_tag = "✓ Verified" if r.get("accessible") else "⚠ Partially Inaccessible"
        pub = f" (Pub: {r.get('published_date')})" if r.get('published_date') != "N/D" else ""
        refs_md.append(f"[{r.get('index')}] **{r.get('title')}**{pub}. *Available:* [{r.get('url')}]({r.get('url')}) [{status_tag}]")
    refs_text = "\n\n".join(refs_md)

    # 1. Complete research_report.md (17 SECTIONS)
    full_report_content = f"""# {title}

**KLEIN AI** | Autonomous Scientific Research Dossier  
*Topic:* {topic}  
*Engine:* Gemini AI + Tavily Web Intelligence | *Depth:* {report_data.get('depth', 'Standard')}

---

## Abstract
{abstract}

**Keywords:** {keywords}

---

## 1. Introduction
{intro}

## 2. Background & Motivation
{scope}

## 3. Problem Statement
{problem_statement}

## 4. Research Objectives
{objectives}

## 5. Formal Research Questions
{questions}

## 6. Synthesized Literature Review
{lit_review}

## 7. Comparative Analysis & Synthesis
### Comparative Insights Across Sources
{comparative}

### Scholarly Consensus
{consensus}

### Conflicting Evidence & Active Debates
{conflicts}

## 8. Evidence Matrix & Grounded Claims
{ev_table}

## 9. Critical Research Gaps (7 Dimensions)
> *Notice: These identified research gaps represent potential bottlenecks and open questions observed within the collected literature partition; they do not constitute absolute proof of global novelty.*

{gaps_text}

## 10. Proposed Methodology & Architecture
**Proposed Framework:** {methodology.get('framework_name', 'Decoupled Adaptive Framework')}

**Research Design:** {methodology.get('research_design', '')}  
**Methodological Approach:** {methodology.get('research_approach', '')}

### Formal Scientific Hypotheses
{hypotheses}

### Dataset Requirements & Data Collection Protocols
- **Dataset Requirements:** {methodology.get('dataset_requirements', '')}
- **Data Collection Methods:** {methodology.get('data_collection_methods', '')}

### Variables Definition
**Independent Variables:**
{indep_vars}

**Dependent Variables:**
{dep_vars}

### Sequential Workflow Stages
{workflow}

## 11. Proposed Experimental Validation Suite
> **Notice:** The following empirical experiments are formally proposed to validate the architectural paradigm against established baselines. They are designated as proposals pending execution.

{exp_text}

## 12. Expected Contributions
{contributions}

## 13. Acknowledged Limitations
{limitations}

## 14. Conclusion & Future Horizon
{conclusion}

## 15. Bibliographic References & Citation Audit
{refs_text}
"""

    report_path = out / "research_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(full_report_content)

    # 2. literature_review.md
    lit_path = out / "literature_review.md"
    with open(lit_path, "w", encoding="utf-8") as f:
        f.write(f"# Literature Review: {topic}\n\n{lit_review}\n")

    # 3. references.md
    ref_path = out / "references.md"
    audit = report_data.get("citation_audit", {})
    ref_content = f"""# References & Citation Audit: {topic}

**Total Sources Collected:** {audit.get('total_sources_collected', len(references))}  
**Total Sources Cited in Review:** {audit.get('total_sources_cited', 0)}  
**Citation Coverage:** {audit.get('citation_coverage_percent', 0.0)}%  
**Integrity Audit Status:** `{audit.get('integrity_status', 'VERIFIED')}`

---

## Bibliographic Sources
{refs_text}
"""
    with open(ref_path, "w", encoding="utf-8") as f:
        f.write(ref_content)

    # 4. research_gaps.md
    gaps_path = out / "research_gaps.md"
    with open(gaps_path, "w", encoding="utf-8") as f:
        f.write(f"# Identified Research Gaps (7 Dimensions): {topic}\n\n{gaps_text}\n")

    # 5. research_methodology.md
    method_path = out / "research_methodology.md"
    method_content = f"""# Proposed Research Methodology: {topic}

**Framework:** {methodology.get('framework_name', '')}  
**Design:** {methodology.get('research_design', '')}  
**Approach:** {methodology.get('research_approach', '')}

## Formal Hypotheses
{hypotheses}

## Variables
### Independent Variables:
{indep_vars}
### Dependent Variables:
{dep_vars}

## Sequential Workflow Stages
{workflow}

## Proposed Experiments (Validation Protocols)
{exp_text}

## Expected Contributions
{contributions}

## Limitations
{limitations}
"""
    with open(method_path, "w", encoding="utf-8") as f:
        f.write(method_content)

    return {
        "report_md": str(report_path),
        "literature_review_md": str(lit_path),
        "references_md": str(ref_path),
        "research_gaps_md": str(gaps_path),
        "methodology_md": str(method_path),
    }
