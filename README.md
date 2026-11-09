# KLEIN AI 🎓🔬
> **One Topic. Complete Research. Powered by AI.**
> 
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Framework: Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)
[![LLM: Google Gemini](https://img.shields.io/badge/LLM-Gemini%203.8%20Flash-orange.svg)](https://aistudio.google.com/)
[![Tests: 69 Passed](https://img.shields.io/badge/Tests-69%20Passed-brightgreen.svg)](docs/TESTING.md)

[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 1. Project Title & Overview

**KLEIN AI** is a full-stack, autonomous artificial intelligence research assistant designed for researchers, students, and engineers. Given a single research topic, the system automatically analyzes the inquiry, formulates formal academic objectives and research questions ($RQ_1-RQ_4$), executes multi-engine public web searches, evaluates source credibility, extracts accessible text, synthesizes cross-source evidence, pinpoints 7-dimension research gaps, proposes novel architectural methodologies with formal experimental protocols, and compiles publication-grade deliverables—including an academic 17-section PDF report, a 12-slide PowerPoint presentation deck, and a Markdown dossier suite.

Traditional literature review is fragmented, time-consuming, and prone to publication bias. Standard conversational chatbots frequently hallucinate non-existent academic papers, invent fake DOIs, cannot crawl the public internet autonomously, and fail to anchor claims to verifiable text passages. **KLEIN AI solves this by enforcing a zero-fabrication research architecture**: every empirical claim is grounded in real text extracts, and every citation is verified against accessible web sources.

---

## 2. Dual Execution Modes

KLEIN AI operates in two distinct, transparent modes depending on API key availability:

| Feature | 🟢 Live API Mode (Connected) | 🔵 Safe / Demo Mode (Offline) |
| :--- | :--- | :--- |
| **Prerequisites** | Valid Gemini and/or Tavily API Keys | **None** (Zero keys required) |
| **Reasoning Engine** | Google Gemini API (`gemini-3.8-flash` default, `gemini-3.5-flash-lite`, `gemini-1.5-flash`, `gemini-1.5-pro`) via official `google-genai` SDK | Deterministic academic synthesis heuristics (No fake citations or synthetic DOIs) |
| **Web Search** | Tavily Search API with advanced academic filtering & multi-URL batch text extraction | DuckDuckGo public web search fallback (`ddgs`) with BeautifulSoup HTML parsing |
| **Verification Ping** | Optimized low-thinking test (`thinking_level=LOW`, max 20 tokens, 25s timeout) | Mock ping response for offline validation |
| **Deliverables** | Full 17-Section PDF, 12-Slide PPTX, Markdown dossiers, SQLite persistence | Full 17-Section PDF, 12-Slide PPTX, Markdown dossiers, SQLite persistence |

---

## 3. Feature Overview

- **Autonomous Research Planner:** Transforms natural language queries into 4 formal objectives, research questions ($RQ_1-RQ_4$), and targeted multi-angle search queries.
- **Adaptive Multi-Round Web Search:** Queries Tavily API with automatic secondary deepening if initial candidate sources are $< 4$. Enforces domain diversity ($\le 3$ sources per domain) to prevent source monopolization.
- **Full-Text HTML Body Scraping:** Uses BeautifulSoup4 to extract clean paragraph text, stripping navigation menus, scripts, advertisements, and footers.
- **6-Dimension Source Credibility Scoring:** Ranks sources across Domain Authority, Author Credentials, Publication Venue, Recency, Reference Density, and Methodological Rigor. Separates authority from topic relevance.
- **Grounded Evidence Matrix:** Maps empirical findings directly to extracted source passages with explicit confidence ratings (`Supported`, `Limited`, `Unverified`).
- **7-Dimension Research Gap Discovery:** Identifies 4 critical bottlenecks evaluating Gap Title, Detailed Explanation, Supporting Citations, Operational Impact, Suggested RQ, Proposed Methodology, and Feasibility.
- **Methodology & Experimental Protocol Suite:** Generates proposed system architecture, hypotheses ($H_1-H_3$), independent/dependent variables, benchmark datasets, baselines, and evaluation metrics.
- **Automated Citation Coverage Audit:** Calculates citation coverage percentage and highlights ungrounded references.
- **Publication-Grade 17-Section PDF:** Styled via ReportLab with running headers, dynamic page numbering ("Page X of Y"), and **clickable web hyperlinks**.
- **12-Slide Dark 16:9 Presentation Deck:** Generated via `python-pptx` matching academic defense criteria (widescreen, metric cards, workflow boxes, and research gap tables).
- **Persistent SQLite Database:** Retains session history across browser restarts with full session reload, deletion, and JSON export.

---

## 4. Architecture & Workflow

```
                        User Topic Input
                               │
                               ▼
                    [ 1. Research Planner ]
       Formulates Title, Objectives, RQ1-RQ4, Thematic Pillars
                               │
                               ▼
               [ 2. Autonomous Web Intelligence ]
     Tavily Search API (or DDG Fallback) with Adaptive Deepening
                               │
                               ▼
                 [ 3. Extraction & Filtering ]
       URL Normalization (Strip UTM) & BeautifulSoup HTML Scraping
                               │
                               ▼
                  [ 4. Source Quality Assessor ]
       6-Dimension Credibility Scoring & Tier Classification
                               │
                               ▼
              [ 5. Analyst & Evidence Matrix Engine ]
         Grounded Claims, Passage Proofs, Consensus & Debates
                               │
                               ▼
                [ 6. Literature Review Agent ]
           Thematic Academic Synthesis with In-Text Citations [1], [2]
                               │
                               ▼
                 [ 7. Research Gap Discovery ]
           7-Dimension Bottleneck & Feasibility Analysis
                               │
                               ▼
                 [ 8. Methodology Architect ]
       Proposed Architecture, Hypotheses (H1-H3), Experimental Suite
                               │
                               ▼
                 [ 9. Citation Audit Engine ]
           URL Verification, Coverage Audit & Integrity Checks
                               │
                               ▼
              [ 10. Multi-Format Deliverable Suite ]
      ├── 17-Section Academic PDF (ReportLab with Clickable Links)
      ├── 12-Slide Widescreen Presentation (.pptx via python-pptx)
      ├── 5 Markdown Dossiers (Report, Lit Review, Gaps, Methods, References)
      └── SQLite Persistence Layer (research_history.db)
```

---

## 5. Technology Stack

| Component | Technology | Version | Purpose |
| :--- | :--- | :---: | :--- |
| **Language** | Python | `3.11+` (Tested on `3.13.7`) | Core application runtime |
| **Dashboard UI** | Streamlit | `^1.35.0` | Dark charcoal reactive web interface with 9 analysis tabs |
| **LLM Reasoning** | Google Gemini API (`google-genai`) | `^0.1.0` | Research planning, evidence synthesis & gap discovery |
| **Search Engine** | Tavily Search API (`tavily-python`) | `^0.3.0` | Academic public web search & batch URL extraction |
| **Fallback Search** | DuckDuckGo Search (`ddgs`) | `^9.0.0` | Public fallback search for offline/safe demo mode |
| **HTML Parser** | BeautifulSoup4 & Requests | `^4.12.0` | Clean web body extraction stripping ads & navigation |
| **PDF Generation** | ReportLab | `^4.1.0` | 17-section publication-grade PDF with clickable links |
| **Slide Generation** | python-pptx | `^0.6.21` | 12-slide 16:9 dark-theme PowerPoint presentation |
| **Persistence** | SQLite 3 | Built-in | Research history database with full session recovery |
| **Configuration** | python-dotenv | `^1.0.0` | Local environment management |
| **Testing Harness** | pytest | `^8.0.0` | 69 unit, integration, and UI regression tests |

---

## 6. Installation & Setup

### Prerequisites
- Python 3.11, 3.12, or 3.13 installed.
- Git installed.

### 1. Clone the Repository
```bash
git clone https://github.com/angad-r/Klein-AI.git
cd Klein-AI
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 7. API Key Configuration

KLEIN AI supports two methods for configuring API credentials:

### Method A: Local `.env` File (Recommended)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your API credentials:
```ini
# Google Gemini API Key (Get from https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here

# Tavily Web Search API Key (Get from https://app.tavily.com/)
TAVILY_API_KEY=your_tavily_api_key_here

# Gemini Model Selection (Default: gemini-3.8-flash, Alternative: gemini-3.5-flash-lite)
GEMINI_MODEL=gemini-3.8-flash
```

### Method B: Streamlit Sidebar at Runtime
You can enter keys directly into the sidebar input fields in the web application and click **"💾 Save .env"** to persist them locally.

> **Verification Latency Optimization:**
> When you click **"🔌 Test Gemini Connection"**, KLEIN AI dispatches an optimized health ping (`"Reply with exactly: KLEIN AI CONNECTED"`) configured with `max_output_tokens=20`, `thinking_level=LOW`, and an explicit 25-second HTTP timeout. This prevents UI blocking and returns an immediate status check.

---

## 8. Usage Instructions

### Launch the Application
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

### Running a Research Session
1. **Enter a Topic:** Input any natural language inquiry (e.g., *"Inference Latency Optimization in Quantized Large Language Models"*).
2. **Choose Search Depth:**
   - **Quick:** 4 queries, 3 results/query, 8 extracts, 2 rounds (Fastest, ~15-25s).
   - **Standard:** 8 queries, 5 results/query, 18 extracts, 3 rounds (Balanced, ~35-50s).
   - **Deep:** 12 queries, 6 results/query, 30 extracts, 4 rounds (Exhaustive, ~60-90s).
3. **Click "Start Research":** Monitor live progress through the multi-agent orchestration pipeline.
4. **Explore the 9 Results Tabs:**
   - **Tab 1: Overview:** Executive summary, research pillars, and source statistics.
   - **Tab 2: Plan & RQs:** Academic title, objectives, and research questions ($RQ_1-RQ_4$).
   - **Tab 3: Literature Review:** 4-theme synthesis with in-text citations.
   - **Tab 4: Evidence:** Grounded claim matrix with direct quotes and confidence ratings.
   - **Tab 5: Research Gaps:** 4 critical bottlenecks analyzed across 7 dimensions.
   - **Tab 6: Methodology:** Architectural specifications and formal proposed validation experiments.
   - **Tab 7: Citation Audit:** Bibliographic references, access statuses, and coverage computation.
   - **Tab 8: Downloads:** Instant access to generated PDF, PPTX, and Markdown dossiers.
   - **Tab 9: History:** Session manager with SQLite search, restore, and deletion.

---

## 9. Application Screenshots

Application screenshots illustrating the dark reactive dashboard and report outputs can be found in [`screenshots/`](screenshots/):

| Dashboard View | Description |
| :--- | :--- |
| **Executive Overview** | Real-time orchestration pipeline and source authority metrics |
| **Grounded Evidence Matrix** | Direct passage quotes mapped to citations with confidence ratings |
| **7-Dimension Research Gaps** | Interactive gap analysis cards with feasibility indicators |
| **ReportLab 17-Section PDF** | Publication-grade academic PDF with running headers and clickable links |
| **12-Slide Presentation Deck** | 16:9 widescreen dark presentation deck with metric cards |

*(Screenshots can be captured and added to [`screenshots/`](screenshots/) by running the application locally).*

---

## 10. Project Directory Structure

```
KLEIN AI/
├── app.py                              # Streamlit Dashboard Application (9 Tabs)
├── config.py                           # System Defaults, Model ID & Search Depth Config
├── requirements.txt                    # Project Dependencies (10 Verified Packages)
├── LICENSE                             # Official MIT License (2026 Angad Ranjan)
├── .env.example                        # Safe Key Template (Zero Credentials)
├── .gitignore                          # Caches, Local Database, and Output Exclusions
├── README.md                           # Public Open-Source Documentation
│
├── ppt_generator.py                    # Backward-Compatibility Re-Export Shim
├── report_generator.py                 # Backward-Compatibility Re-Export Shim
├── research_agent.py                   # Backward-Compatibility Re-Export Shim
├── storage.py                          # Backward-Compatibility Re-Export Shim
├── web_search.py                       # Backward-Compatibility Re-Export Shim
│
├── agents/                             # Autonomous AI Multi-Agent Pipeline
│   ├── orchestrator.py                 # Central Research Orchestrator & Adaptive Search
│   ├── planner.py                      # Research Planning, Objectives & RQ Formulation
│   ├── researcher.py                   # Search Execution & Extraction Coordinator
│   ├── analyst.py                      # Cross-Source Synthesis & Grounded Claims
│   ├── literature_review.py            # Thematic Literature Review with In-Text Citations
│   ├── gap_finder.py                   # 7-Dimension Research Gap Engine
│   ├── methodology.py                  # Architectural Methodology & Proposed Experiments
│   ├── tools.py                        # Typed Tool Registry & Execution Boundaries
│   └── llm_utils.py                    # Google GenAI Caller, Low-Thinking Ping & Redaction
│
├── database/                           # SQLite Persistence Layer
│   └── db.py                           # SQLite Database Manager for Sessions & History
│
├── generators/                         # Document & Artifact Compilation Engines
│   ├── pdf_generator.py                # 17-Section ReportLab PDF Engine (Clickable Links)
│   ├── ppt_generator.py                # 12-Slide Dark 16:9 Presentation Generator
│   ├── report_generator.py             # Markdown Dossier Suite Generator
│   └── submission_package.py           # Academic Deliverables Compilation Suite
│
├── research/                           # Web Intelligence & Scientific Validation
│   ├── search.py                       # Tavily Search API, Fallback & Domain Diversity
│   ├── extraction.py                   # BeautifulSoup HTML Content Scraper
│   ├── source_assessor.py              # 6-Dimension Authority Scoring & Credibility Tiers
│   ├── evidence_extractor.py           # Grounded Claims & Direct Passage Quote Extraction
│   └── citation_validator.py           # Reference Verification & Citation Coverage Auditing
│
├── tests/                              # Comprehensive Test Suite (69 Tests)
│   ├── test_day2_research_engine.py    # 17 tests: Autonomous multi-round search & ranking
│   ├── test_foundation_repairs.py      # 13 tests: Zero-fabrication & degradation
│   ├── test_gemini_verification.py     # 8 tests: Connection ping, timeout & retry handling
│   ├── test_interactive_ui.py          # 14 tests: Streamlit UI, widgets & persistence CRUD
│   ├── test_model_selection.py         # 9 tests: Discovery, propagation & 404 handling
│   ├── test_pipeline.py                # 8 tests: End-to-end pipeline & document generation
│   ├── test_demonstration.py           # Demonstration test harness
│   └── test_three_topics.py            # Multi-topic integration tests
│
├── docs/                               # Organized Documentation Hub
│   ├── PROJECT_DOCUMENTATION.md        # Technical Specification & Module Reference
│   ├── SYSTEM_ARCHITECTURE.md          # Multi-Agent Dataflow & Mermaid Diagrams
│   ├── DEMO_SCRIPT.md                  # Step-by-Step Live Demonstration Script
│   ├── TESTING.md                      # Consolidated Test Dossier & QA Verification (69/69)
│   └── academic-submission/            # Preserved Academic College Submission Package
│       ├── PROJECT_REPORT.pdf          # 31-Section College Project Report (PDF)
│       ├── PROJECT_REPORT.docx         # 31-Section College Project Report (DOCX)
│       ├── PROJECT_PRESENTATION.pptx   # 15-Slide Evaluation Presentation Deck
│       ├── TECHNICAL_RESEARCH_PAPER.docx # Scholarly Paper describing KLEIN AI
│       ├── COLLEGE_PRESENTATION.md     # Presentation Slide Content & Defense Notes
│       └── VIVA_PREPARATION.md         # Comprehensive Viva Voce Q&A Guide
│
├── screenshots/                        # Genuine Application Screenshots Directory
│   └── .gitkeep                        # Clean placeholder
│
└── outputs/                            # Export Directory for User Sessions (.gitignored)
```

---

## 11. Testing & Quality Assurance

KLEIN AI includes **69 automated tests** with 100% pass rate:

```bash
# Run the complete test suite
python -m pytest -v
```

### Focused Test Suites
```bash
# Model selection and latency verification tests (17 tests)
python -m pytest tests/test_model_selection.py tests/test_gemini_verification.py -v

# Autonomous multi-round search engine tests (17 tests)
python -m pytest tests/test_day2_research_engine.py -v

# Interactive UI and SQLite CRUD tests (14 tests)
python -m pytest tests/test_interactive_ui.py -v

# Core pipeline and document compilation tests (8 tests)
python -m pytest tests/test_pipeline.py -v
```

Full test descriptions, historical regression runs, and multi-topic QA evaluations are documented in [`docs/TESTING.md`](docs/TESTING.md).

---

## 12. Known Limitations & Scientific Boundaries

1. **Paywalled Content:** Scientific publishers with strict paywalls only expose title and abstract snippets via public web scraping; the engine automatically flags these as `"Partially Inaccessible / Snippet Only"` rather than fabricating full text.
2. **Computational Validation:** In accordance with scientific integrity guidelines, proposed experiments are structured proposals with testable hypotheses, datasets, baselines, and metrics; they are not claimed as completed empirical laboratory runs.
3. **Search Depth vs. Latency:** Deep search configurations (12 queries, 30 extracts) require 45–75 seconds due to live web scraping and extraction latency.

---

## 13. Project Roadmap

- [ ] **Native ArXiv & Semantic Scholar Connectors:** Add direct academic API adapters alongside Tavily.
- [ ] **Local PDF Vector Ingestion:** Allow users to upload local PDF collections for hybrid local + web synthesis.
- [ ] **Camera-Ready LaTeX Generation:** Export camera-ready IEEE/ACM `.tex` archives with BibTeX files.
- [ ] **Containerized Sandbox Execution:** Execute proposed Python benchmarks in isolated Docker containers.

---

## 14. Contributing Guidelines

Contributions are welcome! Please follow these steps:
1. **Fork the Repository:** Click `Fork` on GitHub.
2. **Create a Feature Branch:** `git checkout -b feature/amazing-feature`.
3. **Ensure Code Quality:** Follow PEP 8 style standards and maintain docstring integrity.
4. **Run Tests:** Ensure all 69 tests pass with `python -m pytest -v`.
5. **Commit Changes:** Write clear, concise commit messages.
6. **Open a Pull Request:** Describe your changes and reference any related issues.

---

## 15. License

KLEIN AI is open-source software licensed under the terms of the [MIT License](LICENSE).

```
Copyright (c) 2026 Angad Ranjan
```
