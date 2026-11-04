# Klein AI — ResearchMate AI: Technical Project Documentation

## Executive Summary
**Klein AI — ResearchMate AI** is an autonomous AI research system designed to bridge the gap between superficial conversational AI and rigorous academic literature synthesis. Built with Python 3, Streamlit, Google Gemini (`google-genai`), Tavily Search, BeautifulSoup, ReportLab, and `python-pptx`, the system performs automated topic decomposition, public web searching, full-text scraping, cross-source comparative synthesis, empirical evidence anchoring, research gap identification, methodology design, and publication compilation.

---

## 1. Core Module Reference

### `agents/orchestrator.py` (ResearchOrchestrator)
The central director managing execution state, telemetry logs, and adaptive decision-making.
- **`run_pipeline(topic: str) -> dict`**:
  1. Calls `planner.plan_research` to decompose the topic into objectives, research questions, and queries.
  2. Dispatches initial search queries via `ToolRegistry.search_web`.
  3. Checks candidate count: If $< 4$, triggers adaptive deepening queries to expand evidence coverage.
  4. Scrapes webpage bodies via `ToolRegistry.extract_webpage`.
  5. Evaluates source credibility and assigns authority scores via `source_assessor.enrich_sources_with_quality`.
  6. Compares source findings and isolates consensus/conflicts via `ToolRegistry.compare_sources`.
  7. Extracts grounded empirical claims with direct passage evidence via `evidence_extractor.extract_evidence_items`.
  8. Synthesizes thematic literature review via `ToolRegistry.generate_literature_review`.
  9. Identifies 7-dimension research gaps via `ToolRegistry.identify_research_gaps`.
  10. Proposes system architecture, hypotheses ($H_1-H_3$), and experimental suite via `ToolRegistry.propose_methodology`.
  11. Audits citations and computes URL coverage via `citation_validator.validate_citations_and_sources`.
  12. Returns a structured academic dictionary containing 17 sections.

### `agents/tools.py` (ToolRegistry)
Provides typed tools with input validation, execution timing, and error boundaries:
- `search_web(query, max_results)`
- `extract_webpage(url)`
- `analyse_source(source, topic)`
- `compare_sources(sources, topic)`
- `generate_literature_review(data)`
- `identify_research_gaps(data)`
- `propose_methodology(data)`
- `generate_report(data, output_path)`
- `generate_presentation(data, output_path)`

### `research/source_assessor.py`
Audits collected sources to differentiate search relevance from scientific credibility:
- **`assess_source_quality(source: dict) -> dict`**:
  - Classifies source type: Preprint (ArXiv/BioRxiv), Peer-Reviewed Journal (IEEE, ACM, Nature), Official Standard (NIST, WHO, CISA), Industry Whitepaper, or Tech Blog.
  - Scores authority on a scale of $0.0$ to $1.0$.
  - Generates a specific quality rationale explaining why the source is useful or requires caution.

### `research/evidence_extractor.py`
Enforces evidence-based research by anchoring every major claim to actual collected text:
- **`extract_evidence_items(topic, sources, gemini_key) -> list[dict]`**:
  - Extracts claims formatted as:
    ```json
    {
      "citation_index": 1,
      "claim": "Specific empirical discovery",
      "source_title": "Original paper title",
      "source_url": "URL",
      "evidence": "Direct quote or exact passage",
      "publication_date": "2024",
      "source_type": "Preprint (ArXiv)",
      "confidence": "Supported"
    }
    ```
  - Categorizes confidence as `Supported`, `Limited`, or `Unverified`.

### `agents/gap_finder.py`
Analyzes literature limitations and discrepancies across 7 structured dimensions:
1. `gap_id`: Unique identifier (e.g., `GAP-01`)
2. `gap_title`: Formal title
3. `explanation`: Structural or empirical deficit in literature
4. `supporting_sources`: Specific collected sources highlighting this limitation
5. `why_it_matters`: Scientific and operational consequence
6. `suggested_research_question`: Testable research question
7. `possible_methodology`: Proposed analytical or empirical method
8. `feasibility`: `High`, `Moderate`, or `Challenging`

### `agents/methodology.py`
Designs structured research methodologies without falsely claiming experiments were completed:
- `framework_name`: Proposed architectural name
- `research_design`: Quantitative empirical benchmarking, factorial ablation
- `research_approach`: Empirical Modeling & Design Science
- `hypotheses`: 3 testable scientific hypotheses ($H_1, H_2, H_3$)
- `dataset_requirements`: Size, modality, class balance, noise levels
- `data_collection_methods`: Protocols for ingestion, deduplication, and splitting
- `variables`: Independent, dependent, and control variables
- `proposed_experiments`: 3 concrete validation experiments (Hypothesis, Datasets, Baselines, Metrics)
- `expected_contributions` & `expected_limitations`

### `generators/pdf_generator.py`
Produces publication-grade PDFs via ReportLab:
- Custom `NumberedCanvas` computing running headers and "Page X of Y" footers.
- Formats all 17 sections, Abstract callout box, Keywords, Problem Statement, Gap tables, and **clickable hyperlinks** for every bibliographic reference.

### `generators/ppt_generator.py`
Generates a 12-slide 16:9 presentation deck via `python-pptx`:
- Slide 1: Title & Metadata
- Slide 2: Research Background
- Slide 3: Problem Statement
- Slide 4: Research Objectives
- Slide 5: Research Questions ($RQ_1-RQ_4$)
- Slide 6: Literature Review
- Slide 7: Major Findings & Grounded Evidence Matrix
- Slide 8: Research Gaps (7 Dimensions)
- Slide 9: Proposed Methodology & Architecture
- Slide 10: Proposed Experiments (Validation Protocols)
- Slide 11: Expected Contributions & Limitations
- Slide 12: Bibliographic References & Citation Audit

### `database/db.py`
SQLite persistence layer:
- Stores sessions in `research_history.db`.
- Auto-migrates database schemas to support depth settings and metrics.
- Recovers session on browser refresh.

---

## 2. API Key Management & Demo Fallback
- **Live Mode:** When `GEMINI_API_KEY` and `TAVILY_API_KEY` are provided (via `.env` or sidebar), the agent queries the live Tavily web index and calls Gemini for synthesis.
- **Demo / Safe Mode:** When keys are omitted, the agent automatically switches to Demo Mode:
  - Executes public web search fallback via `ddgs`.
  - Performs structured scholarly synthesis using high-fidelity fallback templates.
  - Generates complete PDF, PPTX, and Markdown files without crashing or requiring credentials.
