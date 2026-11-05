"""
Academic PDF Report Generator for KLEIN AI.
Produces publication-grade PDFs via ReportLab with 17 academic sections:
1. Title Header & Metadata
2. Abstract Callout Box
3. Keywords
4. Introduction
5. Background & Motivation
6. Problem Statement
7. Research Objectives
8. Research Questions
9. Synthesized Literature Review
10. Comparative Analysis & Synthesis
11. Critical Research Gaps (Table with 7 dimensions)
12. Proposed Methodology & Variables
13. Proposed Experimental Validation Suite
14. Expected Contributions
15. Limitations
16. Conclusion
17. Bibliographic References (with clickable hyperlinks and audit status)
"""
import re
from pathlib import Path
from typing import Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.pdfgen import canvas
import config


class NumberedCanvas(canvas.Canvas):
    """Computes total page count and renders running headers and footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running header for pages > 1
        if self._pageNumber > 1:
            self.drawString(54, 755, "KLEIN AI  |  Autonomous Academic Dossier")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 748, 558, 748)

        # Running footer on all pages
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_str)
        self.drawString(54, 36, "Generated autonomously by Klein AI • KLEIN AI Suite")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)

        self.restoreState()


def clean_markdown_for_pdf(text: str) -> str:
    """Sanitizes text for ReportLab Paragraph compatibility."""
    if not text:
        return ""
    t = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    t = re.sub(r"\*(.*?)\*", r"<i>\1</i>", t)
    t = re.sub(r"^#{1,6}\s*(.*)", r"<b>\1</b>", t, flags=re.MULTILINE)
    t = re.sub(r"&(?![a-zA-Z]+;)", "&amp;", t)
    return t


def generate_pdf(report_data: Dict[str, Any], output_path: str = None) -> str:
    """Generates the 17-section publication-grade PDF file."""
    if not output_path:
        output_path = str(config.OUTPUT_DIR / "research_report.pdf")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    COLOR_PRIMARY = colors.HexColor("#4C1D95")    # Deep Violet
    COLOR_CRIMSON = colors.HexColor("#831843")    # Deep Crimson
    COLOR_DARK = colors.HexColor("#0F172A")       # Charcoal
    COLOR_BG_LIGHT = colors.HexColor("#F8FAFC")
    COLOR_BORDER = colors.HexColor("#CBD5E1")
    COLOR_LINK = colors.HexColor("#2563EB")       # Blue Link

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=23,
        textColor=COLOR_DARK,
        spaceAfter=10,
    )

    tag_style = ParagraphStyle(
        "ReportTag",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=COLOR_PRIMARY,
        spaceAfter=10,
        textTransform="uppercase",
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=COLOR_PRIMARY,
        spaceBefore=11,
        spaceAfter=4,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=COLOR_DARK,
        spaceBefore=5,
        spaceAfter=3,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=12.5,
        textColor=COLOR_DARK,
        spaceAfter=5,
        alignment=4,  # Justified
    )

    abstract_style = ParagraphStyle(
        "ReportAbstract",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.8,
        leading=13,
        textColor=COLOR_DARK,
        alignment=4,
    )

    bullet_style = ParagraphStyle(
        "ReportBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=COLOR_DARK,
        leftIndent=14,
        spaceAfter=3,
    )

    story = []

    # 1. Title Page / Header
    title = report_data.get("title", "Autonomous Academic Research Report")
    story.append(Paragraph("KLEIN AI • AUTONOMOUS INVESTIGATION SERIES", tag_style))
    story.append(Paragraph(title, title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_PRIMARY, spaceBefore=2, spaceAfter=10))

    # 2. Abstract
    abstract_text = report_data.get("abstract", "")
    ab_p = Paragraph(f"<b>Abstract — </b>{clean_markdown_for_pdf(abstract_text)}", abstract_style)
    ab_table = Table([[ab_p]], colWidths=[504])
    ab_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
        ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(ab_table)
    story.append(Spacer(1, 6))

    # 3. Keywords
    keywords_list = report_data.get("keywords", ["Artificial Intelligence", "Empirical Benchmarking"])
    keywords_str = ", ".join(keywords_list)
    story.append(Paragraph(f"<b>Keywords:</b> <i>{keywords_str}</i>", body_style))
    story.append(Spacer(1, 4))

    # 4. Introduction
    story.append(Paragraph("1. Introduction", h1_style))
    story.append(Paragraph(clean_markdown_for_pdf(report_data.get("introduction", "")), body_style))

    # 5. Background & Motivation
    story.append(Paragraph("2. Background & Motivation", h1_style))
    story.append(Paragraph(clean_markdown_for_pdf(report_data.get("scope_and_motivation", "")), body_style))

    # 6. Problem Statement
    story.append(Paragraph("3. Problem Statement", h1_style))
    story.append(Paragraph(clean_markdown_for_pdf(report_data.get("problem_statement", "")), body_style))

    # 7. Research Objectives & 8. Research Questions
    story.append(Paragraph("4. Research Objectives & Formal Questions", h1_style))
    story.append(Paragraph("<b>Primary Research Objectives:</b>", h2_style))
    for obj in report_data.get("objectives", []):
        story.append(Paragraph(f"• {clean_markdown_for_pdf(obj)}", bullet_style))

    story.append(Spacer(1, 3))
    story.append(Paragraph("<b>Formal Research Questions:</b>", h2_style))
    for rq in report_data.get("research_questions", []):
        story.append(Paragraph(f"• <b>{clean_markdown_for_pdf(rq)}</b>", bullet_style))

    # 9. Literature Review
    story.append(Spacer(1, 5))
    story.append(Paragraph("5. Synthesized Literature Review", h1_style))
    lit_review = report_data.get("literature_review", "")
    for block in lit_review.split("\n\n"):
        p_clean = block.strip()
        if p_clean:
            if p_clean.startswith("###") or p_clean.startswith("##"):
                h_text = re.sub(r"^#+\s*", "", p_clean)
                story.append(Paragraph(h_text, h2_style))
            else:
                story.append(Paragraph(clean_markdown_for_pdf(p_clean), body_style))

    # 10. Comparative Analysis & Synthesis
    story.append(Spacer(1, 5))
    story.append(Paragraph("6. Comparative Analysis & Scholarly Synthesis", h1_style))
    story.append(Paragraph("<b>Cross-Source Synthesis & Benchmarks:</b>", h2_style))
    for c in report_data.get("comparative_analysis", []):
        story.append(Paragraph(f"• {clean_markdown_for_pdf(c)}", bullet_style))

    consensus = report_data.get("consensus_points", [])
    if consensus:
        story.append(Spacer(1, 2))
        story.append(Paragraph("<b>Scholarly Consensus:</b>", h2_style))
        for c in consensus:
            story.append(Paragraph(f"• {clean_markdown_for_pdf(c)}", bullet_style))

    conflicts = report_data.get("conflicting_evidence", [])
    if conflicts:
        story.append(Spacer(1, 2))
        story.append(Paragraph("<b>Conflicting Evidence & Debates:</b>", h2_style))
        for c in conflicts:
            story.append(Paragraph(f"• {clean_markdown_for_pdf(c)}", bullet_style))

    # 11. Research Gaps Table
    story.append(Spacer(1, 5))
    story.append(Paragraph("7. Critical Unaddressed Research Gaps (7 Dimensions)", h1_style))
    gaps = report_data.get("research_gaps", [])
    gap_rows = [
        [
            Paragraph("<b>Identifier / Title</b>", h2_style),
            Paragraph("<b>Deficiency, Supporting Sources & Feasibility</b>", h2_style),
        ]
    ]
    for g in gaps:
        col1_text = f"<b>{g.get('gap_id', 'GAP')}</b><br/>{g.get('gap_title', g.get('title', ''))}<br/><i>Feasibility: {g.get('feasibility', 'Moderate')}</i>"
        supp_text = ", ".join(g.get("supporting_sources", [])) or "Extracted literature"
        col2_text = (
            f"{g.get('explanation', g.get('description', ''))}<br/>"
            f"<b>Supporting Sources:</b> {supp_text}<br/>"
            f"<b>Impact:</b> {g.get('why_it_matters', g.get('impact', ''))}<br/>"
            f"<b>RQ:</b> {g.get('suggested_research_question', 'N/A')}"
        )
        gap_rows.append([Paragraph(col1_text, body_style), Paragraph(col2_text, body_style)])

    if len(gap_rows) > 1:
        gt = Table(gap_rows, colWidths=[160, 344])
        gt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(gt)

    # 12. Proposed Methodology & Architecture
    methodology = report_data.get("methodology", {})
    story.append(Spacer(1, 7))
    story.append(Paragraph("8. Proposed Methodology & Architecture", h1_style))
    story.append(Paragraph(f"<b>Proposed Framework:</b> {clean_markdown_for_pdf(methodology.get('framework_name', ''))}", h2_style))
    story.append(Paragraph(f"<b>Design:</b> {clean_markdown_for_pdf(methodology.get('research_design', ''))} | <b>Approach:</b> {clean_markdown_for_pdf(methodology.get('research_approach', ''))}", body_style))

    hypotheses = methodology.get("hypotheses", [])
    if hypotheses:
        story.append(Paragraph("<b>Formal Testable Hypotheses:</b>", h2_style))
        for h in hypotheses:
            story.append(Paragraph(f"• {clean_markdown_for_pdf(h)}", bullet_style))

    # 13. Proposed Experiments Suite
    story.append(Spacer(1, 5))
    story.append(Paragraph("9. Proposed Experimental Validation Suite", h1_style))
    story.append(Paragraph(
        "<i>Notice: The following experimental setups are formally proposed to validate the architectural paradigm "
        "against established baselines. They are designated as proposals pending empirical execution.</i>",
        body_style,
    ))

    exps = report_data.get("proposed_experiments", [])
    for exp in exps:
        story.append(Paragraph(f"<b>{exp.get('experiment_id', 'EXP')}: {exp.get('name', 'Proposed Experiment')}</b>", h2_style))
        det = (
            f"<b>Hypothesis:</b> {exp.get('hypothesis', '')}<br/>"
            f"<b>Target Datasets:</b> {exp.get('target_datasets', '')}<br/>"
            f"<b>Baseline Models:</b> {exp.get('baseline_models', '')}<br/>"
            f"<b>Evaluation Metrics:</b> {exp.get('evaluation_metrics', '')}"
        )
        story.append(Paragraph(clean_markdown_for_pdf(det), bullet_style))
        story.append(Spacer(1, 2))

    # 14. Expected Contributions & 15. Limitations
    story.append(Spacer(1, 5))
    story.append(Paragraph("10. Expected Contributions & Limitations", h1_style))
    story.append(Paragraph("<b>Core Expected Contributions:</b>", h2_style))
    for c in report_data.get("expected_contributions", []):
        story.append(Paragraph(f"• {clean_markdown_for_pdf(c)}", bullet_style))

    story.append(Spacer(1, 2))
    story.append(Paragraph("<b>Acknowledged Limitations:</b>", h2_style))
    for lim in report_data.get("limitations", []):
        story.append(Paragraph(f"• {clean_markdown_for_pdf(lim)}", bullet_style))

    # 16. Conclusion
    story.append(Spacer(1, 5))
    story.append(Paragraph("11. Conclusion & Horizon", h1_style))
    story.append(Paragraph(clean_markdown_for_pdf(report_data.get("conclusion", "")), body_style))

    # 17. Bibliographic References (with clickable links)
    story.append(Spacer(1, 7))
    story.append(Paragraph("12. Bibliographic References & Citation Audit", h1_style))
    refs = report_data.get("references", [])
    for r in refs:
        idx = r.get("index", 1)
        t = r.get("title", "")
        u = r.get("url", "#")
        pub = f" (Pub: {r.get('published_date')})" if r.get("published_date") and r.get("published_date") != "N/D" else ""
        acc = "✓ Verified" if r.get("accessible") else "⚠ Partially Inaccessible"
        # Clickable link in ReportLab via <a href="...">
        cit_html = f"[{idx}] <b>{clean_markdown_for_pdf(t)}</b>{pub}. <a href=\"{u}\" color=\"#2563EB\"><u>Available Online</u></a> [{acc}]."
        story.append(Paragraph(cit_html, bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path
