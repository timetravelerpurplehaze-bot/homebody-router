"""
router/router.py
Main routing orchestrator.

Flow:
  query → classify → select models for tier → call via LiteLLM
        → on failure: retry → try next model in tier → escalate tier → error
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import litellm

from .classifier import classify
from .config import DEFAULT_CONFIG, RouterConfig, available_models_for_tier

litellm.drop_params = True  # ignore unsupported params per-model silently
logger = logging.getLogger("router")


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class RouteResult:
    content: str
    model_used: str
    tier_requested: int
    tier_used: int
    classification_ms: float
    call_ms: float
    attempts: list[dict] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "model_used": self.model_used,
            "tier_requested": self.tier_requested,
            "tier_used": self.tier_used,
            "classification_ms": round(self.classification_ms, 1),
            "call_ms": round(self.call_ms, 1),
            "attempts": self.attempts,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Core router
# ---------------------------------------------------------------------------

class ModelRouter:
    def __init__(self, config: RouterConfig = DEFAULT_CONFIG):
        self.config = config
        self._setup_logging()

    def _setup_logging(self):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[router] %(levelname)s %(message)s"))
        if not logger.handlers:
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def _call_model(self, model: str, messages: list[dict], **kwargs) -> str:
        """Make a single model call via LiteLLM. Raises on failure."""
        resp = litellm.completion(
            model=model,
            messages=messages,
            timeout=self.config.timeout_seconds,
            num_retries=self.config.retries_per_model,
            **kwargs,
        )
        return resp.choices[0].message.content

    def _build_model_order(self, start_tier: int) -> list[tuple[int, str]]:
        """
        Build ordered list of (tier, model) to try.
        Starts at start_tier, then escalates if allow_escalation=True.
        """
        order = []
        tiers_to_try = [start_tier]
        if self.config.allow_escalation:
            tiers_to_try += [t for t in [1, 2, 3] if t > start_tier]

        for tier in tiers_to_try:
            for model in available_models_for_tier(tier):
                order.append((tier, model))

        return order

    def route(
        self,
        query: str,
        messages: Optional[list[dict]] = None,
        force_tier: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **litellm_kwargs,
    ) -> RouteResult:
        """
        Route a query to the best available model.

        Args:
            query:          The user's query text (used for classification).
            messages:       Full message list (if None, builds from query + system_prompt).
            force_tier:     Skip classification and use this tier directly.
            system_prompt:  Optional system message prepended to messages.
            **litellm_kwargs: Passed directly to litellm.completion.

        Returns:
            RouteResult with content, metadata, and attempt log.
        """
        # --- Classification ---
        t0 = time.monotonic()
        tier = force_tier if force_tier is not None else classify(query, self.config)
        classification_ms = (time.monotonic() - t0) * 1000

        # --- Build messages ---
        if messages is None:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": query})

        # --- Attempt models in order ---
        model_order = self._build_model_order(tier)
        if not model_order:
            return RouteResult(
                content="",
                model_used="",
                tier_requested=tier,
                tier_used=tier,
                classification_ms=classification_ms,
                call_ms=0,
                error="No models available. Check your API keys.",
            )

        attempts = []
        call_start = time.monotonic()

        for tier_used, model in model_order:
            attempt: dict[str, Any] = {"model": model, "tier": tier_used}
            try:
                logger.info(f"Trying {model} (tier {tier_used})")
                content = self._call_model(model, messages, **litellm_kwargs)
                call_ms = (time.monotonic() - call_start) * 1000
                attempt["status"] = "success"
                attempts.append(attempt)

                result = RouteResult(
                    content=content,
                    model_used=model,
                    tier_requested=tier,
                    tier_used=tier_used,
                    classification_ms=classification_ms,
                    call_ms=call_ms,
                    attempts=attempts,
                )
                self._log(query, result)
                return result

            except Exception as e:
                attempt["status"] = "failed"
                attempt["error"] = str(e)
                attempts.append(attempt)
                logger.warning(f"{model} failed: {e}")

        call_ms = (time.monotonic() - call_start) * 1000
        return RouteResult(
            content="",
            model_used="",
            tier_requested=tier,
            tier_used=tier,
            classification_ms=classification_ms,
            call_ms=call_ms,
            attempts=attempts,
            error="All models failed. See attempts for details.",
        )

    def _log(self, query: str, result: RouteResult):
        if not self.config.log_file:
            return
        entry = {"query_preview": query[:100], **result.to_dict()}
        try:
            with open(self.config.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.warning(f"Could not write log: {e}")


# ---------------------------------------------------------------------------
# Convenience singleton
# ---------------------------------------------------------------------------

_default_router: Optional[ModelRouter] = None


def get_router(config: RouterConfig = DEFAULT_CONFIG) -> ModelRouter:
    global _default_router
    if _default_router is None:
        _default_router = ModelRouter(config)
    return _default_router


def route(query: str, **kwargs) -> RouteResult:
    """Module-level convenience: route(query) → RouteResult."""
    return get_router().route(query, **kwargs)
