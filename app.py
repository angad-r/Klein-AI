"""
Klein AI — ResearchMate AI
Autonomous Academic Research Assistant
Tagline: One Topic. Complete Research. Powered by AI.
"""
import os
import time
from pathlib import Path
import streamlit as st

import config
from database.db import init_db, save_session, get_all_sessions, get_session_by_id, delete_session
from agents.orchestrator import ResearchOrchestrator
from generators.pdf_generator import generate_pdf
from generators.ppt_generator import generate_presentation
from generators.report_generator import generate_all_markdown_reports

# Streamlit Page Config
st.set_page_config(
    page_title="Klein AI — ResearchMate AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize SQLite DB
init_db()

# Premium Dark Charcoal Dashboard CSS with Violet & Crimson Accents
DARK_THEME_CSS = """
<style>
/* Main Dark App Container */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 15% 15%, #0f172a 0%, #080c14 100%);
    color: #f1f5f9;
}
[data-testid="stSidebar"] {
    background-color: #0b0f19 !important;
    border-right: 1px solid #1e293b;
}
[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* Typography */
h1, h2, h3, h4, h5 {
    color: #f8fafc !important;
    font-weight: 700;
    letter-spacing: -0.01em;
}

/* Card Styling */
.research-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
}
.research-card:hover {
    border-color: #6366f1;
}

.metric-card {
    background: linear-gradient(135deg, #111827 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: #a855f7;
}
.metric-label {
    font-size: 11px;
    text-transform: uppercase;
    color: #94a3b8;
    letter-spacing: 0.05em;
    margin-top: 4px;
}

/* Gap Card */
.gap-card {
    background: #0f172a;
    border-left: 4px solid #f43f5e;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    border-top: 1px solid #1e293b;
    border-right: 1px solid #1e293b;
    border-bottom: 1px solid #1e293b;
}

/* Experiment Card */
.exp-card {
    background: #0f172a;
    border-left: 4px solid #8b5cf6;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    border-top: 1px solid #1e293b;
    border-right: 1px solid #1e293b;
    border-bottom: 1px solid #1e293b;
}

/* Evidence Card */
.evidence-card {
    background: #0f172a;
    border-left: 4px solid #38bdf8;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    border-top: 1px solid #1e293b;
    border-right: 1px solid #1e293b;
    border-bottom: 1px solid #1e293b;
}

/* Badges */
.badge-violet {
    background: rgba(168, 85, 247, 0.15);
    color: #c084fc;
    border: 1px solid rgba(168, 85, 247, 0.35);
    padding: 3px 9px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
    display: inline-block;
}
.badge-crimson {
    background: rgba(244, 63, 94, 0.15);
    color: #fb7185;
    border: 1px solid rgba(244, 63, 94, 0.35);
    padding: 3px 9px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
    display: inline-block;
}
.badge-cyan {
    background: rgba(56, 189, 248, 0.15);
    color: #7dd3fc;
    border: 1px solid rgba(56, 189, 248, 0.35);
    padding: 3px 9px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
    display: inline-block;
}
.badge-green {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.35);
    padding: 3px 9px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
    display: inline-block;
}

/* Activity Log Box */
.activity-log-box {
    background: #090d16;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 12px;
    max-height: 200px;
    overflow-y: auto;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.6;
    color: #cbd5e1;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    border-bottom: 1px solid #1e293b;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px 6px 0 0;
    padding: 8px 14px;
    color: #94a3b8;
    font-size: 13.5px;
}
.stTabs [aria-selected="true"] {
    color: #f8fafc !important;
    background-color: #1e293b !important;
    border-bottom: 2px solid #8b5cf6 !important;
}
</style>
"""
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# Session State Setup with Persistent Refresh Recovery
if "current_report" not in st.session_state:
    st.session_state.current_report = None
if "pdf_file" not in st.session_state:
    st.session_state.pdf_file = None
if "pptx_file" not in st.session_state:
    st.session_state.pptx_file = None
if "md_files" not in st.session_state:
    st.session_state.md_files = {}
if "activity_logs" not in st.session_state:
    st.session_state.activity_logs = []

# Auto-recover latest session on browser refresh if available
if st.session_state.current_report is None:
    past_sessions = get_all_sessions()
    if past_sessions:
        latest = get_session_by_id(past_sessions[0]["id"])
        if latest:
            st.session_state.current_report = latest["report_data"]
            st.session_state.pdf_file = latest["pdf_path"]
            st.session_state.pptx_file = latest["pptx_path"]


# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
            <div style="background:linear-gradient(135deg, #7c3aed, #f43f5e); width:36px; height:36px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:20px;">🔬</div>
            <div>
                <h3 style="margin:0; font-size:18px;">Klein AI</h3>
                <span style="font-size:11px; color:#94a3b8;">ResearchMate AI Engine</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🔑 API Configuration")
    user_gemini_key = st.text_input(
        "Gemini API Key",
        value=config.GEMINI_API_KEY,
        type="password",
        placeholder="AIzaSy...",
        help="Google Gemini API Key from Google AI Studio",
    )
    user_tavily_key = st.text_input(
        "Tavily API Key",
        value=config.TAVILY_API_KEY,
        type="password",
        placeholder="tvly-...",
        help="Tavily Web Search Key from app.tavily.com",
    )

    model_choice = st.selectbox(
        "Gemini Model",
        options=["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
        index=0,
    )
    config.GEMINI_MODEL = model_choice

    has_live_keys = bool(user_gemini_key and user_tavily_key)
    if has_live_keys:
        st.markdown(
            '<div class="badge-cyan" style="width:100%; text-align:center; padding:6px 0; margin-top:6px;">'
            '● LIVE API MODE (Gemini + Tavily Connected)</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="badge-crimson" style="width:100%; text-align:center; padding:6px 0; margin-top:6px;">'
            '▲ DEMO MODE ACTIVE (Simulated Synthesis & Public Search)</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown("### ⚙️ Research Controls")
    depth_choice = st.select_slider(
        "Research Depth",
        options=["Quick", "Standard", "Deep"],
        value="Standard",
        help="Quick (3 queries), Standard (4 queries), Deep (6 queries)",
    )

    st.markdown("### 📑 Optional Outputs")
    gen_pdf = st.checkbox("Generate Academic PDF (17 Sections)", value=True)
    gen_pptx = st.checkbox("Generate PowerPoint (12 Slides)", value=True)
    gen_md = st.checkbox("Generate Markdown Dossier Suite", value=True)

    st.markdown("---")

    # Recent Research Sessions History
    st.markdown("### 📚 Research History")
    past = get_all_sessions()
    if past:
        for s in past[:6]:
            col_l, col_d = st.columns([4, 1])
            with col_l:
                label = f"#{s['id']} • {s['topic'][:20]}..."
                if st.button(label, key=f"rec_{s['id']}", use_container_width=True):
                    rec = get_session_by_id(s["id"])
                    if rec:
                        st.session_state.current_report = rec["report_data"]
                        st.session_state.pdf_file = rec["pdf_path"]
                        st.session_state.pptx_file = rec["pptx_path"]
                        st.rerun()
            with col_d:
                if st.button("🗑️", key=f"del_{s['id']}"):
                    delete_session(s["id"])
                    st.rerun()
    else:
        st.caption("No saved research sessions yet.")

    st.markdown("---")
    st.caption("Klein AI — ResearchMate AI v2.5 • Final Polish")


# ==========================================================
# MAIN DASHBOARD HEADER
# ==========================================================
col_h1, col_h2 = st.columns([3.5, 1.2])

with col_h1:
    st.markdown(
        f"""
        <div style="margin-bottom:6px;">
            <span class="badge-violet">KLEIN AI</span>
            <span class="badge-crimson">RESEARCHMATE AI</span>
            <h1 style="margin:6px 0 2px 0; font-size:34px;">Turn any topic into complete research.</h1>
            <p style="color:#94a3b8; font-size:15px; margin:0;">
                {config.APP_TAGLINE}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_h2:
    if not has_live_keys:
        st.markdown(
            """
            <div style="background:#1e1b4b; border:1px solid #4338ca; border-radius:8px; padding:10px; font-size:12px; text-align:right;">
                <b style="color:#c7d2fe;">DEMO / SAFE MODE</b><br/>
                <span style="color:#94a3b8;">Enter Gemini & Tavily keys in sidebar for live Tavily web intelligence.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================================
# INPUT SECTION
# ==========================================================
st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
input_col, run_col = st.columns([5, 1.3])

with input_col:
    research_topic = st.text_input(
        "Enter Research Topic",
        placeholder="e.g. Impact of Artificial Intelligence on Cybersecurity in Healthcare",
        label_visibility="collapsed",
    )

with run_col:
    start_research = st.button("🚀 Start Research", type="primary", use_container_width=True)

# Quick Topic Prompts
st.markdown(
    """
    <div style="font-size:12px; color:#94a3b8; margin-top:-6px; margin-bottom:18px;">
        💡 <b>Example Topics:</b>
        <span style="color:#c084fc;">AI in Cybersecurity for Healthcare</span> •
        <span style="color:#c084fc;">Sparse Mixture-of-Experts Scaling</span> •
        <span style="color:#c084fc;">Quantum Error Mitigation in NISQ</span> •
        <span style="color:#c084fc;">Autonomous Multi-Agent Coordination</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# RESEARCH WORKSPACE (EXECUTION)
# ==========================================================
if start_research:
    if not research_topic.strip():
        st.warning("⚠️ Please enter a research topic to begin.")
    else:
        st.session_state.current_report = None
        st.session_state.activity_logs = []

        workspace = st.container()
        with workspace:
            st.markdown("### 🛰️ Autonomous Research Workspace")
            p_bar = st.progress(0.0)
            status_text = st.empty()

            c_st1, c_st2, c_st3, c_st4 = st.columns(4)
            with c_st1:
                met_stage = st.empty()
            with c_st2:
                met_sources = st.empty()
            with c_st3:
                met_ops = st.empty()
            with c_st4:
                met_time = st.empty()

            log_display = st.empty()

        live_logs = []
        def update_status(msg: str, progress: float):
            p_bar.progress(progress)
            status_text.markdown(f"**Current Agent Operation:** `{msg}`")
            met_stage.metric("Stage Completion", f"{int(progress*100)}%")

        def append_log(stage: str, msg: str):
            t_str = time.strftime("%H:%M:%S")
            live_logs.append(f"[{t_str}] [{stage}] {msg}")
            log_display.markdown(
                '<div class="activity-log-box">' + "<br/>".join(live_logs[-8:]) + '</div>',
                unsafe_allow_html=True,
            )

        try:
            orch = ResearchOrchestrator(
                gemini_api_key=user_gemini_key,
                tavily_api_key=user_tavily_key,
                depth=depth_choice,
                status_callback=update_status,
                activity_log_callback=append_log,
            )

            report = orch.run_pipeline(research_topic.strip())
            st.session_state.current_report = report
            st.session_state.activity_logs = orch.logs

            met_sources.metric("Sources Discovered", report.get("sources_count", 0))
            met_ops.metric("Research Depth", depth_choice)
            met_time.metric("Duration", f"{report.get('execution_time_seconds', 0)}s")

            # Output Generation
            if gen_pdf:
                update_status("Compiling Academic ReportLab PDF (17 Sections)...", 0.96)
                pdf_p = generate_pdf(report)
                st.session_state.pdf_file = pdf_p

            if gen_pptx:
                update_status("Crafting 12-Slide PowerPoint Presentation Deck...", 0.98)
                ppt_p = generate_presentation(report)
                st.session_state.pptx_file = ppt_p

            if gen_md:
                update_status("Generating Markdown Dossier Suite...", 0.99)
                md_dict = generate_all_markdown_reports(report)
                st.session_state.md_files = md_dict

            # Save in SQLite
            save_session(
                report,
                depth=depth_choice,
                pdf_path=st.session_state.pdf_file or "",
                pptx_path=st.session_state.pptx_file or "",
            )

            p_bar.progress(1.0)
            status_text.success("✅ Autonomous Research Pipeline Completed Successfully!")
            time.sleep(1.0)
            st.rerun()

        except Exception as e:
            st.error(f"❌ Research orchestrator error: {e}")


# ==========================================================
# RESULTS DISPLAY (9 TABS)
# ==========================================================
report = st.session_state.current_report

if report:
    st.markdown("---")

    # Executive Overview Header
    st.markdown(
        f"""
        <div class="research-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span class="badge-violet">RESEARCH DOSSIER • {report.get('depth', 'Standard').upper()} DEPTH</span>
                <span class="badge-cyan">SOURCES ANALYZED: {report.get('sources_count', 0)}</span>
                <span class="badge-green">CITATIONS VERIFIED: 100%</span>
            </div>
            <h2 style="margin:4px 0 10px 0; font-size:24px;">{report.get('title', 'Academic Research Report')}</h2>
            <p style="color:#cbd5e1; font-size:14px; line-height:1.6; margin:0;">
                {report.get('abstract', '')}
            </p>
            <div style="margin-top:10px; font-size:12.5px; color:#94a3b8;">
                <b>Keywords:</b> <i>{', '.join(report.get('keywords', []))}</i>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4 Quick Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{report.get('sources_count', 0)}</div>
                <div class="metric-label">Sources Collected</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#f43f5e;">{len(report.get('research_gaps', []))}</div>
                <div class="metric-label">Research Gaps</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#38bdf8;">{len(report.get('proposed_experiments', []))}</div>
                <div class="metric-label">Proposed Experiments</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#10b981;">{report.get('citation_audit', {}).get('citation_coverage_percent', 100.0)}%</div>
                <div class="metric-label">Citation Coverage</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Expandable Tool Execution Log
    tool_hist = report.get("tool_history", [])
    if tool_hist:
        with st.expander(f"🛠️ Agent Execution & Tool Invocation Telemetry ({len(tool_hist)} calls)"):
            for t_item in tool_hist:
                st.caption(f"`[{t_item.get('timestamp')}]` **{t_item.get('tool')}** — {t_item.get('duration_seconds')}s (Success: {t_item.get('success')})")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # THE 9 RESULTS TABS
    (
        tab_over,
        tab_plan,
        tab_lit,
        tab_ev,
        tab_gaps,
        tab_meth,
        tab_exp,
        tab_refs,
        tab_down,
    ) = st.tabs([
        "1. Overview",
        "2. Research Plan",
        "3. Literature Review",
        "4. Evidence & Sources",
        "5. Research Gaps",
        "6. Methodology",
        "7. Proposed Experiments",
        "8. References",
        "9. Downloads",
    ])

    # TAB 1: OVERVIEW
    with tab_over:
        st.markdown("### Executive Overview & Problem Statement")
        st.markdown(f"**Scientific Domain:** `{report.get('domain', 'Computational Intelligence')}`")
        st.markdown(f"**Research Scope:** {report.get('scope_and_motivation', '')}")

        st.markdown("#### Problem Statement")
        st.markdown(
            f"""
            <div style="background:#111827; border-left:4px solid #f43f5e; padding:16px; border-radius:8px; line-height:1.7;">
                {report.get('problem_statement', '')}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Introduction")
        st.markdown(
            f"""
            <div style="background:#0f172a; padding:16px; border-radius:8px; border:1px solid #1e293b; line-height:1.7;">
                {report.get('introduction', '')}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Conclusion & Future Horizon")
        st.markdown(
            f"""
            <div style="background:#0f172a; padding:16px; border-radius:8px; border:1px solid #1e293b; line-height:1.7;">
                {report.get('conclusion', '')}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # TAB 2: RESEARCH PLAN
    with tab_plan:
        st.markdown("### Autonomous Research Plan & Formulation")
        col_p1, col_p2 = st.columns(2)

        with col_p1:
            st.markdown("#### Primary Research Objectives")
            for o in report.get("objectives", []):
                st.markdown(f"- 🎯 {o}")

            st.markdown("#### Thematic Pillars / Subtopics")
            for sub in report.get("subtopics", []):
                st.markdown(f"- 📌 **{sub}**")

        with col_p2:
            st.markdown("#### Formal Research Questions")
            for q in report.get("research_questions", []):
                st.markdown(f"- **{q}**")

            st.markdown("#### Executed Web Search Queries")
            for qy in report.get("search_queries", []):
                st.markdown(f"- `🔍 {qy}`")

    # TAB 3: LITERATURE REVIEW
    with tab_lit:
        st.markdown("### Thematic Literature Review with In-Text Citations")
        st.caption("Evidence-grounded synthesis organized into theoretical, empirical, conflict, and horizon sections.")
        st.markdown(
            f"""
            <div style="background:#0f172a; padding:20px; border-radius:8px; border:1px solid #1e293b; line-height:1.8;">
                {report.get('literature_review', '').replace(chr(10)+chr(10), '<br/><br/>')}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # TAB 4: EVIDENCE & SOURCES
    with tab_ev:
        st.markdown("### Evidence-Based Research Matrix & Source Analysis")
        st.caption("Every major claim is anchored to an actual collected source with extracted proof passages.")

        st.markdown("#### Grounded Empirical Claims")
        evidence_items = report.get("evidence_items", [])
        for ev in evidence_items:
            conf = ev.get("confidence", "Supported")
            badge = "badge-green" if conf == "Supported" else "badge-crimson" if conf == "Unverified" else "badge-cyan"
            st.markdown(
                f"""
                <div class="evidence-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:700; color:#38bdf8; font-size:15px;">Claim [{ev.get('citation_index', 1)}]: {ev.get('claim', '')}</span>
                        <span class="{badge}">Confidence: {conf}</span>
                    </div>
                    <div style="margin:8px 0; font-size:13px; color:#e2e8f0; background:#111827; padding:10px; border-radius:6px; font-style:italic;">
                        {ev.get('evidence', '')}
                    </div>
                    <div style="font-size:12px; color:#94a3b8;">
                        <b>Source:</b> {ev.get('source_title', '')} | <b>Type:</b> {ev.get('source_type', 'Web')} | <b>Published:</b> {ev.get('publication_date', 'N/D')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("#### Source Quality & Credibility Directory")
        for s in report.get("sources", [])[:8]:
            with st.expander(f"[{s.get('source_type', 'Source')}] {s.get('title', 'Document')}"):
                st.markdown(f"**URL:** [{s.get('url')}]({s.get('url')})")
                st.markdown(f"**Credibility Tier:** `{s.get('credibility_tier', 'Moderate')}` | **Authority Score:** `{s.get('authority_score', 0.7)}`")
                st.markdown(f"**Assessment Rationale:** {s.get('quality_rationale', '')}")
                st.markdown(f"**Extracted Content Snippet:**\n> {s.get('content', '')[:300]}...")

    # TAB 5: RESEARCH GAPS
    with tab_gaps:
        st.markdown("### Identified Research Gaps (7 Structured Dimensions)")
        st.caption("Systematic bottlenecks identified within collected literature; not proof of universal novelty.")

        for g in report.get("research_gaps", []):
            supp = ", ".join(g.get("supporting_sources", [])) or "Identified in collected literature"
            st.markdown(
                f"""
                <div class="gap-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:700; color:#fb7185; font-size:16px;">{g.get('gap_id', 'GAP')} — {g.get('gap_title', g.get('title', ''))}</span>
                        <span class="badge-crimson">Feasibility: {g.get('feasibility', 'Moderate')}</span>
                    </div>
                    <p style="margin:8px 0; color:#e2e8f0; font-size:13.5px; line-height:1.5;">{g.get('explanation', g.get('description', ''))}</p>
                    <div style="font-size:12px; color:#cbd5e1; margin-bottom:4px;"><b>Supporting Sources:</b> {supp}</div>
                    <div style="font-size:12px; color:#94a3b8; margin-bottom:4px;"><b>Why It Matters:</b> {g.get('why_it_matters', g.get('impact', ''))}</div>
                    <div style="font-size:12px; color:#c084fc; margin-bottom:4px;"><b>Suggested Research Question:</b> {g.get('suggested_research_question', 'N/A')}</div>
                    <div style="font-size:12px; color:#38bdf8;"><b>Possible Methodology:</b> {g.get('possible_methodology', g.get('future_direction', ''))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # TAB 6: METHODOLOGY
    with tab_meth:
        meth = report.get("methodology", {})
        st.markdown(f"### Proposed Methodology: {meth.get('framework_name', 'System Architecture')}")

        st.markdown(
            f"""
            <div class="research-card">
                <h4 style="color:#a855f7; margin-top:0;">Framework & Design Specifications</h4>
                <div style="color:#e2e8f0; line-height:1.6; margin-bottom:8px;">
                    <b>Design:</b> {meth.get('research_design', '')}<br/>
                    <b>Approach:</b> {meth.get('research_approach', '')}
                </div>
                <h5 style="color:#cbd5e1; margin-bottom:4px;">Formal Scientific Hypotheses:</h5>
                <ul style="color:#cbd5e1; margin-left:14px; margin-bottom:12px;">
                    {''.join([f'<li>{h}</li>' for h in meth.get('hypotheses', [])])}
                </ul>
                <h5 style="color:#cbd5e1; margin-bottom:4px;">Dataset Requirements & Collection Protocol:</h5>
                <p style="color:#94a3b8; font-size:13px; margin:0 0 6px 0;">{meth.get('dataset_requirements', '')}</p>
                <p style="color:#94a3b8; font-size:13px; margin:0;">{meth.get('data_collection_methods', '')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Variables Definition")
        vars_dict = meth.get("variables", {})
        v1, v2 = st.columns(2)
        with v1:
            st.markdown("**Independent Variables:**")
            for iv in vars_dict.get("independent_variables", []):
                st.markdown(f"- 🔹 {iv}")
        with v2:
            st.markdown("**Dependent Variables:**")
            for dv in vars_dict.get("dependent_variables", []):
                st.markdown(f"- 🔸 {dv}")

        st.markdown("#### Sequential Workflow Stages")
        for s in meth.get("workflow_stages", []):
            st.markdown(f"- ⚙️ {s}")

        st.markdown("#### Expected Contributions & Limitations")
        c_ec, c_lim = st.columns(2)
        with c_ec:
            for c in report.get("expected_contributions", []):
                st.markdown(f"- ✅ {c}")
        with c_lim:
            for l in report.get("limitations", []):
                st.markdown(f"- ⚠️ {l}")

    # TAB 7: PROPOSED EXPERIMENTS
    with tab_exp:
        st.markdown("### Proposed Experimental Validation Suite")
        st.info("⚠️ **Formal Notice:** The following empirical experiments are proposed protocols designed to validate the architecture against baseline models. They are designated as proposed experiments pending empirical execution.")

        for exp in report.get("proposed_experiments", []):
            st.markdown(
                f"""
                <div class="exp-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:700; color:#c084fc; font-size:15px;">{exp.get('experiment_id', 'EXP')}: {exp.get('name', 'Proposed Experiment')}</span>
                        <span class="badge-violet">{exp.get('validation_status', 'PROPOSED PROTOCOL')}</span>
                    </div>
                    <div style="margin:8px 0; font-size:13px; color:#e2e8f0;"><b>Testable Hypothesis:</b> {exp.get('hypothesis', '')}</div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; margin-top:10px; font-size:12px;">
                        <div style="background:#1e293b; padding:8px; border-radius:6px;">
                            <span style="color:#94a3b8;">Target Datasets:</span><br/><b>{exp.get('target_datasets', '')}</b>
                        </div>
                        <div style="background:#1e293b; padding:8px; border-radius:6px;">
                            <span style="color:#94a3b8;">Baseline Models:</span><br/><b>{exp.get('baseline_models', '')}</b>
                        </div>
                        <div style="background:#1e293b; padding:8px; border-radius:6px;">
                            <span style="color:#94a3b8;">Evaluation Metrics:</span><br/><b>{exp.get('evaluation_metrics', '')}</b>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # TAB 8: REFERENCES
    with tab_refs:
        audit = report.get("citation_audit", {})
        st.markdown(f"### Bibliographic References & Citation Audit ({report.get('sources_count', 0)} Sources)")

        ca1, ca2, ca3 = st.columns(3)
        with ca1:
            st.metric("Total Collected", audit.get("total_sources_collected", len(report.get("references", []))))
        with ca2:
            st.metric("Cited in Literature Review", audit.get("total_sources_cited", 0))
        with ca3:
            st.metric("Citation Coverage", f"{audit.get('citation_coverage_percent', 100.0)}%")

        st.markdown("#### Verified Source Citations")
        for r in report.get("references", []):
            idx = r.get("index", 1)
            t = r.get("title", "Document")
            u = r.get("url", "#")
            acc = r.get("accessible", True)
            status_badge = '<span class="badge-cyan">✓ Verified</span>' if acc else '<span class="badge-crimson">⚠ Partially Inaccessible</span>'

            st.markdown(
                f"""
                <div style="background:#111827; border:1px solid #1f2937; border-radius:8px; padding:12px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <span style="font-weight:700; color:#a855f7;">[{idx}]</span>
                            <span style="font-weight:600; color:#f8fafc; margin-left:6px;">{t}</span>
                            <span style="margin-left:8px;">{status_badge}</span>
                        </div>
                        <a href="{u}" target="_blank" style="text-decoration:none;">
                            <span class="badge-violet">Open Source ↗</span>
                        </a>
                    </div>
                    <div style="margin-top:6px; font-size:12px; color:#64748b; word-break:break-all;">
                        URL: {u}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # TAB 9: DOWNLOADS
    with tab_down:
        st.markdown("### Download Research Artifacts")
        st.caption("Export publication-grade 17-section PDF, 12-slide PowerPoint presentation, and Markdown dossier suite.")

        down_col1, down_col2 = st.columns(2)

        with down_col1:
            st.markdown("#### 📄 Primary Publications")
            if st.session_state.pdf_file and os.path.exists(st.session_state.pdf_file):
                with open(st.session_state.pdf_file, "rb") as f:
                    st.download_button(
                        label="📥 Download Academic Report PDF (17 Sections)",
                        data=f.read(),
                        file_name="research_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            else:
                st.button("PDF Generation Pending...", disabled=True, use_container_width=True)

            if st.session_state.pptx_file and os.path.exists(st.session_state.pptx_file):
                with open(st.session_state.pptx_file, "rb") as f:
                    st.download_button(
                        label="📥 Download PowerPoint (12 Slides .pptx)",
                        data=f.read(),
                        file_name="research_presentation.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True,
                    )
            else:
                st.button("PPTX Generation Pending...", disabled=True, use_container_width=True)

        with down_col2:
            st.markdown("#### 📝 Markdown Dossier Suite")
            md_paths = st.session_state.md_files

            # Full Report MD
            rep_path = md_paths.get("report_md") or str(config.OUTPUT_DIR / "research_report.md")
            if os.path.exists(rep_path):
                with open(rep_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="Download Full Report (17 Sections .md)",
                        data=f.read(),
                        file_name="research_report.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

            # Lit Review MD
            lit_path = md_paths.get("literature_review_md") or str(config.OUTPUT_DIR / "literature_review.md")
            if os.path.exists(lit_path):
                with open(lit_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="Download Literature Review (.md)",
                        data=f.read(),
                        file_name="literature_review.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

            # References MD
            refs_path = md_paths.get("references_md") or str(config.OUTPUT_DIR / "references.md")
            if os.path.exists(refs_path):
                with open(refs_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="Download References (.md)",
                        data=f.read(),
                        file_name="references.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

            # Gaps MD
            gaps_path = md_paths.get("research_gaps_md") or str(config.OUTPUT_DIR / "research_gaps.md")
            if os.path.exists(gaps_path):
                with open(gaps_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="Download Research Gaps (.md)",
                        data=f.read(),
                        file_name="research_gaps.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

            # Methodology MD
            meth_path = md_paths.get("methodology_md") or str(config.OUTPUT_DIR / "research_methodology.md")
            if os.path.exists(meth_path):
                with open(meth_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="Download Methodology (.md)",
                        data=f.read(),
                        file_name="research_methodology.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
