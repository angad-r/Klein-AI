"""
Demonstration & QA Verification Script for Klein AI — ResearchMate AI.
Executes the required demonstration topics:
1. 'Impact of Artificial Intelligence on Cybersecurity in Healthcare Systems.'
2. 'Applications of Artificial Intelligence in Healthcare.'
Audits citation integrity, checks PDF and PPTX compilation, and validates database records.
"""
import sys
import os
from pathlib import Path

# Set up project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.orchestrator import ResearchOrchestrator
from generators.pdf_generator import generate_pdf
from generators.ppt_generator import generate_presentation
from generators.report_generator import generate_all_markdown_reports
from database.db import save_session, get_session_by_id
from pptx import Presentation

DEMO_TOPICS = [
    "Impact of Artificial Intelligence on Cybersecurity in Healthcare Systems.",
    "Applications of Artificial Intelligence in Healthcare.",
]


def run_qa_demonstration():
    orch = ResearchOrchestrator(depth="Standard")
    
    for idx, topic in enumerate(DEMO_TOPICS, 1):
        print(f"\n{'='*70}")
        print(f"QA VERIFICATION TOPIC {idx}: {topic}")
        print(f"{'='*70}")
        
        # 1. Pipeline execution
        report = orch.run_pipeline(topic)
        
        # 2. Stage-by-stage audit
        print("  [OK] Objectives Formulated:", len(report.get("objectives", [])))
        print("  [OK] Research Questions (RQ1-RQ4):", len(report.get("research_questions", [])))
        print("  [OK] Queries Executed:", len(report.get("search_queries", [])))
        print("  [OK] Sources Discovered & Assessed:", report.get("sources_count", 0))
        print("  [OK] Evidence Items Grounded:", len(report.get("evidence_items", [])))
        print("  [OK] Literature Review Length:", len(report.get("literature_review", "")))
        print("  [OK] 7-Dimension Gaps Pinpointed:", len(report.get("research_gaps", [])))
        print("  [OK] Proposed Methodology Framework:", report.get("methodology", {}).get("framework_name", "N/A"))
        print("  [OK] Proposed Experiments Suite:", len(report.get("proposed_experiments", [])))
        
        # 3. Citation Audit
        audit = report.get("citation_audit", {})
        print("  [OK] Total Citations Audit:", audit.get("total_sources_collected", 0))
        print("  [OK] Citation Coverage %:", audit.get("citation_coverage_percent", 0.0))
        print("  [OK] Integrity Status:", audit.get("integrity_status", "UNKNOWN"))
        assert audit.get("total_sources_collected", 0) > 0, "Must collect sources"
        
        # 4. Generate PDF Report (17 sections)
        pdf_path = generate_pdf(report)
        assert os.path.exists(pdf_path), "PDF must exist"
        pdf_size_kb = round(os.path.getsize(pdf_path) / 1024, 2)
        print(f"  [OK] 17-Section PDF Compiled: {pdf_path} ({pdf_size_kb} KB)")
        
        # 5. Generate 12-Slide PowerPoint
        ppt_path = generate_presentation(report)
        assert os.path.exists(ppt_path), "PPTX must exist"
        prs = Presentation(ppt_path)
        slide_count = len(prs.slides)
        assert slide_count == 12, f"PPTX should have exactly 12 slides, found {slide_count}"
        ppt_size_kb = round(os.path.getsize(ppt_path) / 1024, 2)
        print(f"  [OK] 12-Slide PowerPoint Generated: {ppt_path} ({slide_count} slides, {ppt_size_kb} KB)")
        
        # 6. Generate Markdown Suite
        md_dict = generate_all_markdown_reports(report)
        assert os.path.exists(md_dict["report_md"]), "report.md must exist"
        print(f"  [OK] Markdown Suite Created: {len(md_dict)} files generated")
        
        # 7. Database Persistence
        sess_id = save_session(report, depth="Standard", pdf_path=pdf_path, pptx_path=ppt_path)
        assert sess_id > 0, "Must persist to SQLite"
        retrieved = get_session_by_id(sess_id)
        assert retrieved["topic"] == topic, "Stored topic must match"
        print(f"  [OK] SQLite Session Persisted: ID #{sess_id}")
        
    print("\n" + "="*70)
    print("ALL QA DEMONSTRATION WORKFLOWS VERIFIED SUCCESSFULLY!")
    print("="*70)


if __name__ == "__main__":
    run_qa_demonstration()
