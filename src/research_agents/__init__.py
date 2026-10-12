"""Dual-agent research: Gemini explores, Claude critiques."""

from .orchestrator import ResearchResult, Round, run_research

__all__ = ["ResearchResult", "Round", "run_research"]
