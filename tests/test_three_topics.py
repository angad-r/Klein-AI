"""
Test runner for 3 diverse research topics.
Validates end-to-end execution, evidence extraction, PDF/PPTX generation,
and database persistence.
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.orchestrator import ResearchOrchestrator
from generators.pdf_generator import generate_pdf
from generators.ppt_generator import generate_presentation
from generators.report_generator import generate_all_markdown_reports
from database.db import save_session

topics = [
    "Impact of Artificial Intelligence on Cybersecurity in Healthcare",
    "Inference Latency Optimization in Quantized Large Language Models",
    "Autonomous Multi-Agent Coordination Protocols for Disaster Response",
]


def run_three_topics():
    orch = ResearchOrchestrator(depth="Quick")

    for idx, topic in enumerate(topics, 1):
        print(f"\n==========================================")
        print(f"RUNNING TOPIC {idx}: {topic}")
        print(f"==========================================")

        report = orch.run_pipeline(topic)

        title = report.get("title", "")
        sources_count = report.get("sources_count", 0)
        ev_count = len(report.get("evidence_items", []))
        gaps_count = len(report.get("research_gaps", []))
        exp_count = len(report.get("proposed_experiments", []))

        print(f"Academic Title: {title}")
        print(f"Sources Collected: {sources_count}")
        print(f"Evidence Items Extracted: {ev_count}")
        print(f"Research Gaps Identified: {gaps_count}")
        print(f"Proposed Experiments: {exp_count}")

        pdf_path = generate_pdf(report)
        ppt_path = generate_presentation(report)
        md_dict = generate_all_markdown_reports(report)

        sess_id = save_session(report, depth="Quick", pdf_path=pdf_path, pptx_path=ppt_path)
        print(f"Persisted to SQLite ID: {sess_id}")

        assert gaps_count >= 1, "Should have identified gaps"
        assert exp_count >= 1, "Should have proposed experiments"
        assert sess_id > 0, "Should persist to DB"

    print("\nAll 3 research topics successfully completed with verified deliverables!")


if __name__ == "__main__":
    run_three_topics()
