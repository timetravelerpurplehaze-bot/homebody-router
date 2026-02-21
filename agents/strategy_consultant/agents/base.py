"""
agents/strategy_consultant/agents/base.py
BaseAgent — every specialist agent inherits this.
"""

import logging
import sys
import os
from pathlib import Path

# Workspace on path
WORKSPACE = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(WORKSPACE))

from router import ModelRouter
from router.config import RouterConfig


class BaseAgent:
    """
    Base class for all strategy consulting agents.
    Handles model routing, logging, and standard run interface.
    """

    name: str = "base"
    default_tier: int = 2

    def __init__(self, state=None, config=None):
        self.state = state
        self.router = ModelRouter(config or RouterConfig(
            classifier_backend="heuristic",
            allow_escalation=True,
            timeout_seconds=60,
        ))
        self.logger = logging.getLogger(f"consultant.{self.name}")

    def call(self, prompt: str, system: str = "", force_tier: int = None) -> str:
        """Route a prompt through the model router and return text."""
        result = self.router.route(
            query=prompt,
            system_prompt=system or self._default_system(),
            force_tier=force_tier or self.default_tier,
        )
        if result.success:
            self.logger.info(f"[{self.name}] {result.model_used} tier={result.tier_used} {result.call_ms:.0f}ms")
            return result.content.strip()
        else:
            self.logger.error(f"[{self.name}] FAILED: {result.error}")
            return f"[{self.name} failed: {result.error}]"

    def _default_system(self) -> str:
        return (
            "You are a specialist agent within a senior strategy consulting team "
            "focused on tech and AI. Be rigorous, precise, and commercially grounded. "
            "No filler phrases. No hedging. Give direct, actionable analysis."
        )

    def run(self, **kwargs) -> str:
        """Override in subclass. Returns markdown string output."""
        raise NotImplementedError

    def validate(self) -> dict:
        """
        Run a self-validation test. Returns {passed: bool, output: str, notes: str}.
        Override in subclass for domain-specific tests.
        """
        try:
            out = self.call("Say 'AGENT_OK' and your agent name.", force_tier=1)
            return {"passed": "AGENT_OK" in out or len(out) > 5, "output": out[:200], "notes": "Basic connectivity test"}
        except Exception as e:
            return {"passed": False, "output": "", "notes": str(e)}
