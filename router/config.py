"""
router/config.py
Model registry, tier definitions, and configuration loader.
Add API keys to .env or environment before use.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Tier definitions
# Tier 1 = cheap/fast,  Tier 2 = balanced,  Tier 3 = powerful/expensive
# ---------------------------------------------------------------------------

TIERS: dict[int, list[str]] = {
    1: [
        "anthropic/claude-haiku-4-5",
        "openai/gpt-4o-mini",
        "gemini/gemini-2.0-flash",
    ],
    2: [
        "anthropic/claude-sonnet-4-6",
        "openai/gpt-4o",
        "gemini/gemini-2.0-pro",
    ],
    3: [
        "anthropic/claude-opus-4-6",
        "openai/gpt-4-turbo",
        "gemini/gemini-ultra",
    ],
}

# Preferred primary provider order within each tier (first available wins)
PROVIDER_PRIORITY = ["anthropic", "openai", "gemini"]

# API key env var names by provider prefix
PROVIDER_API_KEYS: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai":    "OPENAI_API_KEY",
    "gemini":    "GEMINI_API_KEY",
}


@dataclass
class RouterConfig:
    # Classifier backend: "llm" (default, uses Tier-1 model) or "routellm"
    classifier_backend: str = "llm"

    # RouteLLM router type if classifier_backend == "routellm"
    routellm_router: str = "mf"  # "mf" | "causal_llm" | "bert"

    # Cost threshold for RouteLLM (0–1, lower = more routing to weak model)
    routellm_threshold: float = 0.11593

    # Whether to allow escalation across tiers on failure
    allow_escalation: bool = True

    # Max retries per model before moving to next
    retries_per_model: int = 1

    # Timeout in seconds per model call
    timeout_seconds: int = 60

    # Log routing decisions to file
    log_file: Optional[str] = None


# Singleton config instance — override fields as needed
DEFAULT_CONFIG = RouterConfig()


def available_models_for_tier(tier: int) -> list[str]:
    """Return only models whose provider API key is set."""
    result = []
    for model in TIERS.get(tier, []):
        provider = model.split("/")[0]
        key_name = PROVIDER_API_KEYS.get(provider)
        if key_name and os.environ.get(key_name):
            result.append(model)
    return result


def all_available_models() -> dict[int, list[str]]:
    return {tier: available_models_for_tier(tier) for tier in TIERS}
