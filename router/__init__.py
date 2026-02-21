"""
Homebody Model Router
─────────────────────
Complexity-aware LLM routing with automatic fallback.

Quick start:
    from router import route
    result = route("Explain transformer attention in detail")
    print(result.content, result.model_used)

With config:
    from router import ModelRouter
    from router.config import RouterConfig
    r = ModelRouter(RouterConfig(classifier_backend="heuristic", allow_escalation=True))
    result = r.route("What is 2+2?")
"""

from .router import ModelRouter, RouteResult, route, get_router
from .classifier import classify
from .config import RouterConfig, DEFAULT_CONFIG, TIERS, available_models_for_tier, all_available_models

__all__ = [
    "route",
    "get_router",
    "ModelRouter",
    "RouteResult",
    "classify",
    "RouterConfig",
    "DEFAULT_CONFIG",
    "TIERS",
    "available_models_for_tier",
    "all_available_models",
]
