# KLEIN AI 🎓🔬
> **Tagline:** One Topic. Complete Research. Powered by AI.

---

## 1. Project Title
**KLEIN AI: Autonomous Academic AI Research Assistant**

## 2. Project Overview
KLEIN AI is a full-stack, autonomous artificial intelligence research agent. Given a single research topic, the system automatically analyzes the inquiry, formulates formal academic objectives and research questions ($RQ_1-RQ_4$), executes multi-engine public web searches via Tavily, evaluates source credibility, extracts accessible text using BeautifulSoup, synthesizes cross-source evidence using Google Gemini, pinpoints 7-dimension research gaps, proposes novel architectural methodologies with formal experimental protocols, and compiles publication-grade deliverables—including an academic 17-section PDF report, a 12-slide PowerPoint presentation deck, and a Markdown dossier suite.

## 3. Problem Statement
Academic literature review and state-of-the-art synthesis represent massive computational and cognitive bottlenecks for researchers, students, and engineers. Traditional manual literature searching is fragmented across proprietary databases, susceptible to publication bias, slow, and prone to citation errors. Conversely, standard conversational Large Language Model chatbots hallucinate non-existent citations, cannot search the live public internet autonomously, fail to extract full-page textual evidence, and conflate speculative opinions with verified scientific claims.

## 4. Project Objectives
1. **Autonomous Planning:** Transform a raw natural language research topic into structured research objectives, formal research questions ($RQ_1-RQ_4$), and targeted academic search queries.
2. **Multi-Engine Public Web Intelligence:** Query Tavily API for public web literature with automated fallback search and URL deduplication.
3. **Evidence-Based Grounding:** Anchor every major empirical claim to extracted source passages with confidence ratings (`Supported`, `Limited`, `Unverified`), eliminating fabricated references.
4. **Source Credibility Auditing:** Classify source types (Preprints, Peer-Reviewed Journals, Official Specs, Technical Whitepapers) and score authority.
5. **Critical Gap Discovery:** Identify 7-dimension research gaps analyzing repeated limitations, conflicting findings, and methodological deficits.
6. **Methodology & Experimental Suite:** Propose an architectural paradigm and define formal **proposed validation experiments** (with hypotheses, datasets, baselines, and metrics).
7. **Multi-Format Deliverables:** Produce a 17-section academic PDF (with running headers & page numbers), a 12-slide 16:9 PowerPoint presentation, and Markdown files.

## 5. Main Features
- **Intelligent Autonomous Orchestrator:** Multi-stage workflow with adaptive secondary search deepening when candidate sources are $< 4$.
- **Typed Tool Registry:** Formalized tools (`search_web`, `extract_webpage`, `analyse_source`, `compare_sources`, `generate_literature_review`, `identify_research_gaps`, `propose_methodology`, `generate_report`, `generate_presentation`) with telemetry and execution boundaries.
- **Source Quality Assessor:** Real-time domain and metadata classification with quality rationales.
- **Grounded Evidence Matrix:** Maps claims directly to extracted source passages.
- **7-Dimension Research Gap Engine:** Identifies Gap Title, Explanation, Supporting Sources, Operational Impact, Suggested RQ, Possible Methodology, and Feasibility.
- **Publication-Grade 17-Section PDF:** Styled via ReportLab with two-pass header/footer calculation and **clickable hyperlinks**.
- **12-Slide Dark PowerPoint Presentation:** 16:9 widescreen presentation matching academic evaluation criteria.
- **Persistent SQLite Database:** Retains session history across browser refreshes.
- **Offline / Safe Demo Mode:** Full pipeline functions seamlessly even when API keys are not supplied.

## 6. Technology Stack
- **Programming Language:** Python 3.11+ (Tested on Python 3.13)
- **Dashboard UI:** Streamlit 1.35+
- **Reasoning & Synthesis Engine:** Google Gemini API via official `google-genai` SDK (`gemini-2.5-flash`, `gemini-1.5-flash`)
- **Web Intelligence:** Tavily Search API (`tavily-python`) & Fallback Search (`ddgs`)
- **Webpage Scraping & Parsing:** BeautifulSoup4 & Requests
- **Document Generation:** ReportLab (PDF) & `python-pptx` (PowerPoint 16:9)
- **Database / Persistence:** SQLite 3 (`research_history.db`)
- **Environment & Configuration:** `python-dotenv`
- **Testing Harness:** `pytest`

## 7. System Architecture
```
User Topic Input
       │
       ▼
[ Research Planner ] ──> Generates 4 Objectives, RQ1-RQ4, Thematic Pillars, Search Queries
       │
       ▼
[ Tool Registry: search_web ] ──> Tavily Multi-Query Search (with Fallback & Adaptive Deepening)
       │
       ▼
[ Deduplication & Extractor ] ──> Normalized URL filtering & BeautifulSoup HTML body parsing
       │
       ▼
[ Source Assessor ] ──> Authority scoring, credibility tiers (ArXiv, IEEE, Official Docs, Blogs)
       │
       ▼
[ Research Analyst & Evidence Engine ] ──> Grounded claims, passage proofs, consensus & debates
       │
       ▼
[ Literature Review Agent ] ──> Thematic synthesis with exact in-text citations [1], [2]
       │
       ▼
[ Research Gap Agent ] ──> 7-dimension bottleneck identification & feasibility ratings
       │
       ▼
[ Methodology Agent ] ──> Proposed architecture, hypotheses (H1-H3), and experimental validation suite
       │
       ▼
[ Citation Validator ] ──> URL verification, metadata integrity audit, coverage computation
       │
       ▼
[ Deliverables Generation Engine ]
  ├── 17-Section PDF (ReportLab with clickable links)
  ├── 12-Slide Presentation (.pptx via python-pptx)
  ├── 5 Markdown Dossiers (.md)
  └── SQLite Session Persistence
```

## 8. Agent Workflow
1. **Topic Ingestion:** Analyzes scope, domain, and research intent.
2. **Planning:** Formulates academic title, objectives, questions, and search queries.
3. **Execution:** Dispatches web searches across multiple search angles.
4. **Adaptive Deepening:** If candidate sources are insufficient ($< 4$), autonomously formulates secondary queries.
5. **Content Extraction:** Scrapes clean paragraph text, ignoring scripts, navigations, ads, and footers.
6. **Quality Assessment:** Assigns credibility tiers and audits authorship/publication dates.
7. **Evidence Extraction:** Extracts direct quotes anchoring claims to citations.
8. **Literature Review:** Drafts formal scholarly prose structured into four themes.
9. **Gap Discovery:** Pinpoints 4 critical bottlenecks across 7 structured dimensions.
10. **Methodology:** Designs system architecture, hypotheses, variables, and proposed experiments.
11. **Citation Audit:** Checks all citations against collected URLs.
12. **Export:** Compiles PDF, PPTX, and Markdown files and records session in SQLite.

## 9. Folder Structure
```
KLEIN AI/
│
├── app.py                     # Streamlit Dark Dashboard UI with 9 Results Tabs
├── config.py                  # System config, search depth & branding settings
├── requirements.txt           # Project dependencies
├── .env.example               # Template for Gemini & Tavily credentials
├── .gitignore                 # Excludes local artifacts, databases, and secrets
├── README.md                  # Comprehensive Project Guide (17 Sections)
├── PROJECT_DOCUMENTATION.md   # Complete Technical Specification & Module Reference
├── SYSTEM_ARCHITECTURE.md     # In-Depth Agent Architecture & Dataflow Diagrams
├── TESTING_REPORT.md          # Comprehensive QA Test Log & Multi-Topic Verification
│
├── agents/                    # Autonomous AI Agent Pipeline
│   ├── orchestrator.py        # Central Research Orchestrator with adaptive decision-making
│   ├── tools.py               # Typed Tool Registry with telemetry and execution boundaries
│   ├── planner.py             # Topic analysis, 4 objectives, RQ1-RQ4, search queries
│   ├── researcher.py          # Coordinates multi-query search & text extraction
│   ├── analyst.py             # Source summaries, comparative analysis, consensus & debates
│   ├── literature_review.py   # Thematic academic review with in-text citations
│   ├── gap_finder.py          # 7-dimension research gap discovery
│   ├── methodology.py         # Proposed system architecture & proposed validation suite
│   └── llm_utils.py           # Shared google-genai caller with automatic model fallback
│
├── research/                  # Web Intelligence & Integrity Tools
│   ├── search.py              # Real Tavily web search, URL deduplication & fallback
│   ├── extraction.py          # BeautifulSoup4 text scraper & accessibility auditor
│   ├── source_assessor.py     # Source quality, authority score & credibility tiers
│   ├── evidence_extractor.py  # Grounded empirical claim extraction with confidence ratings
│   └── citation_validator.py  # Reference verification and citation coverage auditing
│
├── generators/                # Artifact Generation Engines
│   ├── pdf_generator.py       # 17-section ReportLab PDF compilation with clickable links
│   ├── ppt_generator.py       # 12-slide 16:9 dark-theme PowerPoint presentation generator
│   └── report_generator.py    # Markdown suite generator (17-section report, lit review, gaps)
│
├── database/                  # Persistence Layer
│   └── db.py                  # SQLite database manager for sessions & persistent recovery
│
├── tests/                     # Test Suite
│   ├── test_pipeline.py       # 8 unit & integration tests
│   ├── test_three_topics.py   # Multi-topic evaluation script
│   └── test_demonstration.py  # Demonstration and QA verification runner
│
└── outputs/                   # Export directory for generated PDF, PPTX, and MD files
```

## 10. Installation Instructions
Clone the repository or navigate to the workspace directory:
```bash
git clone <repository-url>
cd "KLEIN AI"
```
Install dependencies via pip:
```bash
pip install -r requirements.txt
```

## 11. API Key Configuration
Create a `.env` file from `.env.example`:
```ini
# Google Gemini API Key (Get from https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here

# Tavily Web Search API Key (Get from https://app.tavily.com/)
TAVILY_API_KEY=your_tavily_api_key_here

# Gemini Model Selection
GEMINI_MODEL=gemini-2.5-flash
```
*Note: API keys can also be supplied directly in the Streamlit sidebar at runtime. In their absence, the application runs in **Demo / Safe Mode** using simulated synthesis and public web search fallback.*

## 12. How to Run the Application
Launch the Streamlit dashboard:
```bash
streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your web browser.

## 13. Example Research Workflow
1. Enter research topic: `"Impact of Artificial Intelligence on Cybersecurity in Healthcare Systems."`
2. Select depth: `Standard` (4 queries, 5 results/query, 8 extracts).
3. Click `Start Research`.
4. Watch real-time activity:
   - Formulating objectives and $RQ_1-RQ_4$
   - Querying Tavily web search across multiple subtopics
   - Deduplicating URLs and extracting webpage text via BeautifulSoup
   - Auditing source credibility tiers (ArXiv, PubMed, NIST)
   - Extracting grounded evidence items with direct passage quotes
   - Synthesizing thematic literature review with in-text citations
   - Pinpointing 4 research gaps across 7 structured dimensions
   - Formulating proposed methodology, hypotheses ($H_1-H_3$), and validation experiments
   - Auditing citation coverage against collected sources
5. Explore the 9 dashboard tabs.
6. Download the 17-section PDF and 12-slide PowerPoint presentation.

## 14. Output Files Generated
All deliverables are saved in the `outputs/` folder:
- `research_report.pdf`: 17-section publication-grade PDF report with running headers and page numbers.
- `research_presentation.pptx`: 12-slide 16:9 widescreen dark presentation deck.
- `research_report.md`: Complete 17-section Markdown report.
- `literature_review.md`: Standalone literature review dossier.
- `references.md`: Bibliographic references and citation audit report.
- `research_gaps.md`: 7-dimension research gap specifications.
- `research_methodology.md`: Architectural specifications, variables, and proposed experiments.

## 15. Limitations
1. **Paywalled Content:** Commercial paywalled portals without open-access preprints only expose abstract snippets; the agent flags these as `"Partially Inaccessible / Snippet Only"`.
2. **Computational Validation:** In accordance with scientific integrity guidelines, proposed experiments are structured proposals with testable hypotheses, datasets, baselines, and metrics; they are not claimed as completed empirical laboratory runs.
3. **Search Depth vs. Latency:** Deeper search configurations (Deep: 6 queries, 12 extracts) require 30–45 seconds due to web scraping latency.

## 16. Future Enhancements
- **Direct PDF Vector Ingestion:** Ingest uploaded local PDF papers for hybrid local + web synthesis.
- **ArXiv & Semantic Scholar Direct APIs:** Add direct academic API connectors alongside Tavily.
- **Automated Experiment Execution:** Connect to containerized sandbox environments (e.g. Docker, Modal) to automatically run synthetic benchmark scripts.
- **LaTeX Export:** Export camera-ready IEEE/ACM LaTeX templates (`.tex`).

## 17. Team Contribution Structure
- **AI Systems Engineer & Full-Stack Architect:** Multi-agent pipeline design, `ToolRegistry`, Gemini API integration, and adaptive search deepening.
- **Web Intelligence & Scraping Specialist:** Tavily API integration, BeautifulSoup scraper, URL deduplication, and source quality assessor.
- **Scientific Synthesis & Prompt Engineer:** Literature review synthesis, grounded evidence extraction engine, 7-dimension research gap discovery, and methodology design.
- **UI/UX Designer & Document Specialist:** Streamlit dashboard, ReportLab 17-section PDF compilation, `python-pptx` 12-slide presentation generator, and SQLite persistence.
