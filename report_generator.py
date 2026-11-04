"""
Backward compatibility wrapper for report generation.
Delegates to generators.report_generator and generators.pdf_generator.
"""
from generators.pdf_generator import generate_pdf, generate_pdf as generate_pdf_report
from generators.report_generator import generate_all_markdown_reports
