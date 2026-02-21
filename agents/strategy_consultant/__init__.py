"""
Strategy Consulting Multi-Agent System
=======================================
11 specialist agents operating as a senior consulting team.

Quick start:
    from agents.strategy_consultant.orchestrator import EngagementPartner
    ep = EngagementPartner()

    # Get intake questions first
    qs = ep.get_intake_questions("Should we build our own LLM or use APIs?")

    # Run full engagement
    result = ep.start_engagement(
        problem="Should we build our own LLM or use APIs?",
        client_name="AcmeCorp",
        proactivity=Proactivity.HIGH,
        competitors=["OpenAI", "Anthropic", "Cohere"],
        data_files=["/path/to/financials.xlsx"],
    )
    print(result['pdf_path'])

CLI:
    python -m agents.strategy_consultant.cli engage "Your problem here"
    python -m agents.strategy_consultant.cli validate
    python -m agents.strategy_consultant.cli history
"""

from .orchestrator import EngagementPartner
from .config import Proactivity, ProjectType
from .state import EngagementState, search_engagements
