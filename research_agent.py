"""
Backward compatibility wrapper for ResearchAgent.
Delegates to agents.orchestrator.ResearchOrchestrator.
"""
from agents.orchestrator import ResearchOrchestrator as ResearchAgent

__all__ = ["ResearchAgent"]
