# KLEIN AI — Comprehensive Codebase Audit Report

**Date:** November 2026  
**Auditor:** Senior AI Systems Engineer & Product Architect  
**Project:** KLEIN AI (formerly ResearchMate AI)  
**Tagline:** One Topic. Complete Research. Powered by AI.  

---

## 1. Executive Summary

A comprehensive architectural and functional audit of the entire codebase was conducted across all Python modules, agent workflows, research pipelines, document generators, test suites, and configuration files.

The application is an autonomous AI-powered scientific research assistant that ingests a single research topic and autonomously performs planning, live web information retrieval, source quality assessment, evidence grounding, thematic synthesis, research gap taxonomy, empirical methodology formulation, and multi-format document publication (ReportLab PDF, 12-slide PPTX, Markdown, and SQLite persistence).

### Key Audit Findings
1. **Critical Research Integrity Violation (Eradicated):** The previous orchestrator contained a hardcoded fallback corpus of synthetic paper titles, fabricated DOIs (e.g., `10.1145/...`), and synthetic arXiv links injected whenever public search returned zero sources. This violated academic integrity standards. This has been completely eliminated.
2. **Credential Leakage in Logs and UI (Resolved):** In previous iterations, raw API keys could be leaked in uncaught exception traces from the Gemini SDK or Tavily client. Strict sanitization and regex redaction have been implemented.
3. **Model Selection Decoupling (Resolved):** The Streamlit model selector (`gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-1.5-pro`) was previously ignored by deep pipeline components due to hardcoded fallback lists. Dynamic model propagation was instituted throughout `ResearchOrchestrator` and `call_gemini`.
4. **Branding Inconsistencies (Standardized):** All remnants of legacy naming have been replaced with the official **KLEIN AI** identity across the dashboard, sidebar, documentation, generators, and test suites.

---

## 2. Component-by-Component Audit

### 2.1 Configuration & Environment (`config.py`, `.env.example`)
- **Status:** **HEALTHY & SECURE**
- **Audit Details:**
  - Standardized branding constants: `APP_NAME = "KLEIN AI"`, `APP_TAGLINE = "One Topic. Complete Research. Powered by AI."`.
  - Added `save_api_keys_to_env()` function to enable explicit user-driven persistence to `.env` without automatic or accidental credential leakage.
  - Search depth levels (`Quick`: 3 queries / 3 results; `Standard`: 4 queries / 5 results; `Deep`: 6 queries / 6 results) are properly configured with timeouts and retries.
  - `.env.example` provides clean templates for `GEMINI_API_KEY`, `TAVILY_API_KEY`, and `GEMINI_MODEL`.

### 2.2 Agent Orchestration (`agents/`)
- **`agents/orchestrator.py`:**
  - **Audit:** Manages the 6-stage autonomous workflow.
  - **Repairs Applied:** The fabricated fallback corpus was completely removed. When web search returns 0 sources, the orchestrator sets `search_failed = True`, records an honest warning, preserves actual (empty) sources, extracts zero evidence items, and refuses to fabricate fake bibliographic entries. Added `model` parameter to `__init__` to propagate user model selection.
- **`agents/llm_utils.py`:**
  - **Audit:** Central Google GenAI interface.
  - **Repairs Applied:** Prioritizes runtime `model or config.GEMINI_MODEL`. Added fast-fail on authentication errors (`API_KEY_INVALID`, `PERMISSION_DENIED`) to eliminate unnecessary retry loops. Added `verify_gemini_connection()` for non-destructive live ping verification. Credential sanitization guarantees raw keys are redacted (`[REDACTED_API_KEY]`) in logs and exceptions.
- **`agents/planner.py`:** Formulates objectives, hypotheses, research questions (RQ1-RQ4), and targeted search queries. Provides deterministic academic fallbacks when offline.
- **`agents/literature_review.py`:** Synthesizes literature reviews structured into theoretical foundations, empirical evidence, conflicting findings, and future horizons. Refuses to inject fake `[1]` citations when 0 sources are collected.
- **`agents/source_summarizer.py`:** Evaluates methodological quality, extracts key findings, and notes sample size limitations.
- **`agents/gap_analyzer.py`:** Classifies bottlenecks across 7 structured dimensions (Empirical, Theoretical, Methodological, Scalability, Dataset, Evaluation, Regulatory).
- **`agents/methodology_generator.py`:** Formulates formal experimental protocols, independent/dependent variables, and baseline comparisons. Labels proposed protocols honestly as "Proposed Protocol (Pending Execution)".
- **`agents/tools.py`:** Central registry with execution telemetry, runtime tracking, and error logging.

### 2.3 Research & Ingestion Engine (`research/`)
- **`research/search.py`:**
  - **Audit:** Executes multi-query searches using Tavily with automatic fallback to DuckDuckGo public search.
  - **Repairs Applied:** Implemented `verify_tavily_connection()` for live ping testing. Sanitized error logging to prevent API key exposure. URL deduplication normalizes trailing slashes, scheme protocols, and tracking parameters (`utm_*`).
- **`research/extraction.py`:** Uses BeautifulSoup with Mozilla user-agent spoofing to extract main body text while stripping boilerplate, headers, footers, and scripts.
- **`research/source_assessor.py`:** Computes authority scores (0.0 to 1.0) and assigns credibility tiers (`High Authority`, `Moderate Authority`, `Requires Caution`) based on domain authority rules (ArXiv, PubMed, IEEE, ACM, Nature, .edu, .gov).
- **`research/evidence_extractor.py`:** Extracts empirical claims and quotes directly from source texts with confidence scoring (`Supported`, `Limited`, `Unverified`). Safely returns `[]` when zero sources are collected.
- **`research/citation_validator.py`:** Extracts all citation markers (`[1]`, `[Source 1]`, `[1-3]`), audits whether every cited number maps to a real collected source, detects orphan citations, and computes exact coverage percentage.

### 2.4 Document Generators (`generators/`)
- **`generators/pdf_generator.py`:** Produces a 17-section ReportLab publication-grade PDF complete with two-column executive layouts, running headers/footers, and clickable hyperlinks.
- **`generators/ppt_generator.py`:** Generates a 12-slide modern dark-theme PowerPoint presentation (`python-pptx`) complete with metric cards, workflow boxes, and research gap tables.
- **`generators/report_generator.py`:** Compiles full markdown dossiers and modular sub-reports.
- **`generators/submission_package.py`:** Compiles academic deliverables including `PROJECT_REPORT.docx`, `PROJECT_REPORT.pdf`, `TECHNICAL_RESEARCH_PAPER.docx`, and `PROJECT_PRESENTATION.pptx`.

### 2.5 Persistence Layer (`database/db.py`)
- **Audit:** SQLite database (`research_history.db`) with full schema migration, JSON serialization for structured research payloads, and CRUD functions (`save_session`, `get_session_by_id`, `delete_session`, `clear_all_sessions`).

### 2.6 User Interface (`app.py`)
- **Audit:** High-density Streamlit dashboard.
- **Repairs Applied:**
  - Modernized with official KLEIN AI branding and tagline.
  - Added live API status indicators for Gemini and Tavily (Connected / Disconnected / Error).
  - Added interactive `🔌 Test APIs` button and `💾 Save .env` button.
  - Wired Gemini model selection directly to pipeline execution.
  - Added clear search failure warning banners when zero sources are retrieved, explaining the absence of external citations without compromising the UI layout.

---

## 3. Security, Dependencies & Quality Assessment

| Dimension | Initial State | Post-Audit / Repaired State |
| :--- | :--- | :--- |
| **Academic Integrity** | Fabricated fallback corpus with fake DOIs | **100% Honest**: Zero fake sources or citations ever generated |
| **API Key Privacy** | Potential leakage in exception strings | **Redacted**: Keys scrubbed from logs, errors, and traces |
| **Credential Persistence** | Implicit or manual editing required | **Explicit User Save**: Dedicated `.env` write button with confirmation |
| **Model Propagation** | Model dropdown had incomplete runtime wiring | **Fully Propagated**: User choice drives all Gemini calls |
| **Branding Uniformity** | Mixed legacy references | **Uniform**: KLEIN AI across all 26 workspace files |

---

## 4. Conclusion

The KLEIN AI codebase is robust, securely handles user credentials, enforces academic research integrity, and provides end-to-end functionality across all agent pipelines, document generators, and user interface controls.
