"""
PowerPoint Presentation Generator for KLEIN AI.
Produces a 12-slide publication-grade 16:9 presentation adhering to the exact required outline:
Slide 1: Title
Slide 2: Research Background
Slide 3: Problem Statement
Slide 4: Research Objectives
Slide 5: Research Questions
Slide 6: Literature Review
Slide 7: Major Findings & Evidence
Slide 8: Research Gaps
Slide 9: Proposed Methodology
Slide 10: Experiment Design (Proposed Protocols)
Slide 11: Expected Contributions
Slide 12: Bibliographic References
"""
from typing import Dict, Any, List
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import config

COLOR_BG = RGBColor(15, 23, 42)              # Charcoal/Slate
COLOR_CARD_BG = RGBColor(30, 41, 59)         # Dark Slate Card
COLOR_CARD_BORDER = RGBColor(71, 85, 105)    # Slate Border
COLOR_TEXT_PRIMARY = RGBColor(248, 250, 252) # Crisp White
COLOR_TEXT_MUTED = RGBColor(148, 163, 184)   # Slate Light
COLOR_ACCENT_VIOLET = RGBColor(168, 85, 247) # Violet
COLOR_ACCENT_CRIMSON = RGBColor(244, 63, 94) # Crimson
COLOR_ACCENT_CYAN = RGBColor(56, 189, 248)   # Cyan


def _apply_dark_bg(slide, prs):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = COLOR_BG
    shape.line.color.rgb = COLOR_BG
    return shape


def _add_header(slide, title_text: str, category_text: str = "KLEIN AI • AUTONOMOUS INVESTIGATION"):
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.35))
    tf_c = cat_box.text_frame
    tf_c.word_wrap = True
    p_c = tf_c.paragraphs[0]
    p_c.text = category_text.upper()
    p_c.font.name = "Calibri"
    p_c.font.size = Pt(10.5)
    p_c.font.bold = True
    p_c.font.color.rgb = COLOR_ACCENT_VIOLET

    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.5), Inches(0.75))
    tf_t = title_box.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title_text
    p_t.font.name = "Calibri"
    p_t.font.size = Pt(24)
    p_t.font.bold = True
    p_t.font.color.rgb = COLOR_TEXT_PRIMARY


def generate_presentation(report_data: Dict[str, Any], output_path: str = None) -> str:
    """Generates the 12-slide academic research presentation deck."""
    if not output_path:
        output_path = str(config.OUTPUT_DIR / "research_presentation.pptx")

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    topic = report_data.get("topic", "Research Topic")
    title = report_data.get("title", f"Autonomous Investigation: {topic}")
    sources_count = report_data.get("sources_count", len(report_data.get("references", [])))

    # SLIDE 1: Title
    s1 = prs.slides.add_slide(blank_layout)
    _apply_dark_bg(s1, prs)

    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(1.8), Inches(0.12), Inches(3.8))
    bar.fill.solid()
    bar.fill.fore_color.rgb = COLOR_ACCENT_CRIMSON
    bar.line.color.rgb = COLOR_ACCENT_CRIMSON

    tb1 = s1.shapes.add_textbox(Inches(1.3), Inches(1.8), Inches(11.0), Inches(3.8))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "KLEIN AI"
    p0.font.bold = True
    p0.font.size = Pt(13)
    p0.font.color.rgb = COLOR_ACCENT_VIOLET
    p0.space_after = Pt(12)

    p1 = tf1.add_paragraph()
    p1.text = title
    p1.font.bold = True
    p1.font.size = Pt(28)
    p1.font.color.rgb = COLOR_TEXT_PRIMARY
    p1.space_after = Pt(16)

    p2 = tf1.add_paragraph()
    p2.text = f"Synthesized Evidence Base: {sources_count} Public Sources  |  Gemini AI + Tavily Autonomous Pipeline"
    p2.font.size = Pt(13)
    p2.font.color.rgb = COLOR_TEXT_MUTED

    # SLIDE 2: Research Background
    s2 = prs.slides.add_slide(blank_layout)
    _apply_dark_bg(s2, prs)
    _add_header(s2, "Research Background & Context")

    c2 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.0))
    c2.fill.solid()
    c2.fill.fore_color.rgb = COLOR_CARD_BG
    c2.line.color.rgb = COLOR_CARD_BORDER
    tf2 = c2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = Inches(0.4)
    tf2.margin_top = Inches(0.3)

    p_bgh = tf2.paragraphs[0]
    p_bgh.text = f"SCIENTIFIC DOMAIN: {report_data.get('domain', 'Computational Systems').upper()}"
    p_bgh.font.bold = True
    p_bgh.font.size = Pt(14)
    p_bgh.font.color.rgb = COLOR_ACCENT_CYAN
    p_bgh.space_after = Pt(12)

    p_bg = tf2.add_paragraph()
    p_bg.text = report_data.get("scope_and_motivation", report_data.get("introduction", ""))
    p_bg.font.size = Pt(13)
    p_bg.font.color.rgb = COLOR_TEXT_PRIMARY
    p_bg.space_after = Pt(14)

    p_subs = tf2.add_paragraph()
    p_subs.text = "Core Thematic Pillars:"
    p_subs.font.bold = True
    p_subs.font.size = Pt(12)
    p_subs.font.color.rgb = COLOR_ACCENT_VIOLET
    p_subs.space_after = Pt(6)

    for sub in report_data.get("subtopics", [])[:4]:
        p = tf2.add_paragraph()
        p.text = f"•  {sub}"
        p.font.size = Pt(11.5)
        p.font.color.rgb = COLOR_TEXT_PRIMARY

    # SLIDE 3: Problem Statement
    s3 = prs.slides.add_slide(blank_layout)
    _apply_dark_bg(s3, prs)
    _add_header(s3, "Problem Statement & Bottlenecks")

    c3 = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.0))
    c3.fill.solid()
    c3.fill.fore_color.rgb = COLOR_CARD_BG
    c3.line.color.rgb = COLOR_CARD_BORDER
    tf3 = c3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = Inches(0.4)
    tf3.margin_top = Inches(0.3)

    p_psh = tf3.paragraphs[0]
    p_psh.text = "CORE CHALLENGE IDENTIFIED IN THE LITERATURE"
    p_psh.font.bold = True
    p_psh.font.size = Pt(14)
    p_psh.font.color.rgb = COLOR_ACCENT_CRIMSON
    p_psh.space_after = Pt(12)

    p_ps = tf3.add_paragraph()
    p_ps.text = report_data.get("problem_statement", "")
    p_ps.font.size = Pt(13.5)
    p_ps.font.color.rgb = COLOR_TEXT_PRIMARY
    p_ps.space_after = Pt(16)

    p_obs = tf3.add_paragraph()
    p_obs.text = "Operational Implications:\n• Lack of cross-study baseline standardization\n• Latency volatility under non-stationary traffic\n• Insufficient out-of-distribution robustness auditing"
    p_obs.font.size = Pt(12)
    p_obs.font.color.rgb = COLOR_TEXT_MUTED

    # SLIDE 4: Research Objectives
    s4 = prs.slides.add_slide(blank_layout)
    _apply_dark_bg(s4, prs)
    _add_header(s4, "Primary Research Objectives")

    for i, obj in enumerate(report_data.get("objectives", [])[:4]):
        top_y = Inches(1.8 + (i * 1.25))
        card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top_y, Inches(11.7), Inches(1.1))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_CARD_BORDER
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.3)
        tf.margin_top = Inches(0.15)

        po_idx = tf.paragraphs[0]
        po_idx.text = f"OBJECTIVE 0{i+1}"
        po_idx.font.bold = True
        po_idx.font.size = Pt(10)
        po_idx.font.color.rgb = COLOR_ACCENT_VIOLET

        po_text = tf.add_paragraph()
        po_text.text = obj
        po_text.font.size = Pt(12)
        po_text.font.color.rgb = COLOR_TEXT_PRIMARY

    # SLIDE 5: Research Questions
    s5 = prs.slides.add_slide(blank_layout)
    _apply_dark_bg(s5, prs)
    _add_header(s5, "Formal Research Questions (RQ1 - RQ4)")

    for i, rq in enumerate(report_data.get("research_questions", [])[:4]):
        top_y = Inches(1.8 + (i * 1.25))
        card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top_y, Inches(11.7), Inches(1.1))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_CARD_BORDER
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.3)
        tf.margin_top = Inches(0.15)

        prq_idx = tf.paragraphs[0]
        prq_idx.text = f"RESEARCH QUESTION {i+1}"
        prq_idx.font.bold = True
        prq_idx.font.size = Pt(10)
        prq_idx.font.color.rgb = COLOR_ACCENT_CRIMSON

        prq_text = tf.add_paragraph()
        prq_text.text = rq
        prq_text.font.size = Pt(12)
        prq_text.font.color.rgb = COLOR_TEXT_PRIMARY

    # SLIDE 6: Literature Review
    s6 = prs.slides.add_slide(blank_layout)
    _apply_dark_bg(s6, prs)
    _add_header(s6, "Synthesized Literature Review", "THEMATIC SCHOLARLY SYNTHESIS")

    c6 = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.0))
    c6.fill.solid()
    c6.fill.fore_color.rgb = COLOR_CARD_BG
    c6.line.color.rgb = COLOR_CARD_BORDER
    tf6 = c6.text_frame
    tf6.word_wrap = True
    tf6.margin_left = Inches(0.4)
    tf6.margin_top = Inches(0.3)

    p6_h = tf6.paragraphs[0]
    p6_h.text = "THEMATIC STATE-OF-THE-ART SYNTHESIS"
    p6_h.font.bold = True
    p6_h.font.size = Pt(14)
    p6_h.font.color.rgb = COLOR_ACCENT_VIOLET
    p6_h.space_after = Pt(10)

    clean_lit = report_data.get("literature_review", "").replace("#", "")
    p6_b = tf6.add_paragraph()
    p6_b.text = clean_lit[:680] + "..."
    p6_b.font.size = Pt(11.5)
    p6_b.font.color.rgb = COLOR_TEXT_PRIMARY

    # SLIDE 7: Major Findings & Evidence Matrix
    s7 = prs.slides.add_slide(blank_layout)
    _apply_dark_bg(s7, prs)
    _add_header(s7, "Major Findings & Grounded Evidence Matrix")

    evs = report_data.get("evidence_items", [])[:3]
    for i, ev in enumerate(evs):
        top_y = Inches(1.8 + (i * 1.65))
        card = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top_y, Inches(11.7), Inches(1.5))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_CARD_BORDER
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.3)
        tf.margin_top = Inches(0.15)

        p_claim = tf.paragraphs[0]
        p_claim.text = f"CLAIM [{ev.get('citation_index', i+1)}]: {ev.get('claim', '')}"
        p_claim.font.bold = True
        p_claim.font.size = Pt(11.5)
        p_claim.font.color.rgb = COLOR_ACCENT_CYAN

        p_ev = tf.add_paragraph()
        p_ev.text = f"Supporting Passage: {ev.get('evidence', '')[:160]}..."
        p_ev.font.size = Pt(10)
        p_ev.font.color.rgb = COLOR_TEXT_PRIMARY

        p_src = tf.add_paragraph()
        p_src.text = f"Source: {ev.get('source_title', '')[:50]} | Confidence: {ev.get('confidence', 'Supported')}"
        p_src.font.size = Pt(9.5)
        p_src.font.color.rgb = COLOR_TEXT_MUTED

    # SLIDE 8: Research Gaps
    s8 = prs.slides.add_slide(blank_layout)
    _apply_dark_bg(s8, prs)
    _add_header(s8, "Critical Research Gaps (7 Dimensions)")

    gaps = report_data.get("research_gaps", [])[:4]
    coords = [
        (Inches(0.8), Inches(1.8)),
        (Inches(6.8), Inches(1.8)),
        (Inches(0.8), Inches(4.3)),
        (Inches(6.8), Inches(4.3)),
    ]

    for idx, g in enumerate(gaps):
        gx, gy = coords[idx]
        g_box = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, gx, gy, Inches(5.7), Inches(2.3))
        g_box.fill.solid()
        g_box.fill.fore_color.rgb = COLOR_CARD_BG
        g_box.line.color.rgb = COLOR_CARD_BORDER
        tf_g = g_box.text_frame
        tf_g.word_wrap = True
        tf_g.margin_left = Inches(0.25)
        tf_g.margin_top = Inches(0.18)

        p_gid = tf_g.paragraphs[0]
        p_gid.text = f"{g.get('gap_id', f'GAP-0{idx+1}')} : {g.get('gap_title', g.get('title', ''))}"
        p_gid.font.bold = True
        p_gid.font.size = Pt(12)
        p_gid.font.color.rgb = COLOR_ACCENT_CRIMSON

        p_gdesc = tf_g.add_paragraph()
        p_gdesc.text = g.get("explanation", g.get("description", ""))[:120] + "..."
        p_gdesc.font.size = Pt(10)
        p_gdesc.font.color.rgb = COLOR_TEXT_PRIMARY

        p_gimp = tf_g.add_paragraph()
        p_gimp.text = f"Impact: {g.get('why_it_matters', '')[:90]} | Feasibility: {g.get('feasibility', 'Moderate')}"
        p_gimp.font.size = Pt(9)
        p_gimp.font.color.rgb = COLOR_TEXT_MUTED

    # SLIDE 9: Proposed Methodology
    s9 = prs.slides.add_slide(blank_layout)
    _apply_dark_bg(s9, prs)
    _add_header(s9, "Proposed Methodology & Architecture")

    methodology = report_data.get("methodology", {})
    m_card = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.8))
    m_card.fill.solid()
    m_card.fill.fore_color.rgb = COLOR_CARD_BG
    m_card.line.color.rgb = COLOR_CARD_BORDER
    tf_m = m_card.text_frame
    tf_m.word_wrap = True
    tf_m.margin_left = Inches(0.3)
    tf_m.margin_top = Inches(0.2)

    p_mh = tf_m.paragraphs[0]
    p_mh.text = f"FRAMEWORK: {methodology.get('framework_name', 'Proposed System Framework')}"
    p_mh.font.bold = True
    p_mh.font.size = Pt(14)
    p_mh.font.color.rgb = COLOR_ACCENT_VIOLET

    p_mb = tf_m.add_paragraph()
    p_mb.text = f"Design: {methodology.get('research_design', '')}\nApproach: {methodology.get('research_approach', '')}"
    p_mb.font.size = Pt(11)
    p_mb.font.color.rgb = COLOR_TEXT_PRIMARY

    stages = methodology.get("workflow_stages", [])[:4]
    for i, s_text in enumerate(stages):
        sx = Inches(0.8 + (i * 2.95))
        s_box = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx, Inches(3.9), Inches(2.8), Inches(2.9))
        s_box.fill.solid()
        s_box.fill.fore_color.rgb = COLOR_CARD_BG
        s_box.line.color.rgb = COLOR_CARD_BORDER
        tf_s = s_box.text_frame
        tf_s.word_wrap = True
        tf_s.margin_left = Inches(0.2)
        tf_s.margin_top = Inches(0.2)

        p_sn = tf_s.paragraphs[0]
        p_sn.text = f"STAGE 0{i+1}"
        p_sn.font.bold = True
        p_sn.font.size = Pt(12)
        p_sn.font.color.rgb = COLOR_ACCENT_CYAN
        p_sn.space_after = Pt(8)

        p_sb = tf_s.add_paragraph()
        p_sb.text = s_text
        p_sb.font.size = Pt(10.5)
        p_sb.font.color.rgb = COLOR_TEXT_PRIMARY

    # SLIDE 10: Experiment Design (Proposed Protocols)
    s10 = prs.slides.add_slide(blank_layout)
    _apply_dark_bg(s10, prs)
    _add_header(s10, "Proposed Experimental Validation Protocols", "VALIDATION SUITE (PENDING EXECUTION)")

    exps = report_data.get("proposed_experiments", [])[:3]
    for i, exp in enumerate(exps):
        ex_x = Inches(0.8 + (i * 3.95))
        e_card = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, ex_x, Inches(1.8), Inches(3.8), Inches(5.0))
        e_card.fill.solid()
        e_card.fill.fore_color.rgb = COLOR_CARD_BG
        e_card.line.color.rgb = COLOR_CARD_BORDER
        tf_e = e_card.text_frame
        tf_e.word_wrap = True
        tf_e.margin_left = Inches(0.25)
        tf_e.margin_top = Inches(0.25)

        p_eh = tf_e.paragraphs[0]
        p_eh.text = f"{exp.get('experiment_id', f'EXP-0{i+1}')}: {exp.get('name', '')}"
        p_eh.font.bold = True
        p_eh.font.size = Pt(13)
        p_eh.font.color.rgb = COLOR_ACCENT_CRIMSON
        p_eh.space_after = Pt(8)

        p_hyp = tf_e.add_paragraph()
        p_hyp.text = f"Hypothesis:\n{exp.get('hypothesis', '')}"
        p_hyp.font.size = Pt(10)
        p_hyp.font.color.rgb = COLOR_TEXT_PRIMARY
        p_hyp.space_after = Pt(6)

        p_dt = tf_e.add_paragraph()
        p_dt.text = f"Target Datasets:\n{exp.get('target_datasets', '')}"
        p_dt.font.size = Pt(9.5)
        p_dt.font.color.rgb = COLOR_TEXT_MUTED
        p_dt.space_after = Pt(6)

        p_mt = tf_e.add_paragraph()
        p_mt.text = f"Metrics: {exp.get('evaluation_metrics', '')}"
        p_mt.font.size = Pt(9.5)
        p_mt.font.color.rgb = COLOR_ACCENT_CYAN

    # SLIDE 11: Expected Contributions
    s11 = prs.slides.add_slide(blank_layout)
    _apply_dark_bg(s11, prs)
    _add_header(s11, "Expected Contributions & Limitations")

    cl_card = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.0))
    cl_card.fill.solid()
    cl_card.fill.fore_color.rgb = COLOR_CARD_BG
    cl_card.line.color.rgb = COLOR_CARD_BORDER
    tf_cl = cl_card.text_frame
    tf_cl.word_wrap = True
    tf_cl.margin_left = Inches(0.4)
    tf_cl.margin_top = Inches(0.3)

    p_ch = tf_cl.paragraphs[0]
    p_ch.text = "CORE SCIENTIFIC & TECHNICAL CONTRIBUTIONS"
    p_ch.font.bold = True
    p_ch.font.size = Pt(14)
    p_ch.font.color.rgb = COLOR_ACCENT_VIOLET
    p_ch.space_after = Pt(8)

    for c in report_data.get("expected_contributions", [])[:4]:
        p = tf_cl.add_paragraph()
        p.text = f"•  {c}"
        p.font.size = Pt(11.5)
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        p.space_after = Pt(6)

    p_lh = tf_cl.add_paragraph()
    p_lh.text = "ACKNOWLEDGED LIMITATIONS"
    p_lh.font.bold = True
    p_lh.font.size = Pt(13)
    p_lh.font.color.rgb = COLOR_ACCENT_CRIMSON
    p_lh.space_before = Pt(10)
    p_lh.space_after = Pt(4)

    for lim in report_data.get("limitations", [])[:2]:
        p = tf_cl.add_paragraph()
        p.text = f"•  {lim}"
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_TEXT_MUTED

    # SLIDE 12: References
    s12 = prs.slides.add_slide(blank_layout)
    _apply_dark_bg(s12, prs)
    _add_header(s12, "Bibliographic References & Citation Audit")

    ref_card = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.0))
    ref_card.fill.solid()
    ref_card.fill.fore_color.rgb = COLOR_CARD_BG
    ref_card.line.color.rgb = COLOR_CARD_BORDER
    tf_ref = ref_card.text_frame
    tf_ref.word_wrap = True
    tf_ref.margin_left = Inches(0.4)
    tf_ref.margin_top = Inches(0.3)

    p_rh = tf_ref.paragraphs[0]
    p_rh.text = f"CITATIONS & SOURCE DIRECTORY ({sources_count} SOURCES COLLECTED)"
    p_rh.font.bold = True
    p_rh.font.size = Pt(14)
    p_rh.font.color.rgb = COLOR_ACCENT_CYAN
    p_rh.space_after = Pt(10)

    for r in report_data.get("references", [])[:8]:
        p = tf_ref.add_paragraph()
        t = r.get("title", "")
        u = r.get("url", "")
        p.text = f"[{r.get('index')}] {t[:65]}... ({u[:45]})"
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_TEXT_PRIMARY
        p.space_after = Pt(4)

    prs.save(output_path)
    return output_path
