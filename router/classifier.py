"""
router/classifier.py
Query complexity classifier.

Backends:
  - "llm"      : Ask a cheap model (Tier-1) to score complexity. Most reliable.
  - "heuristic": Rule-based, zero API calls. Fast but approximate.
  - "routellm" : RouteLLM pre-trained matrix-factorization router.
"""

import os
import re
import logging
from typing import Literal

logger = logging.getLogger("router.classifier")

# Complexity tier labels
Tier = Literal[1, 2, 3]

# ---------------------------------------------------------------------------
# Heuristic classifier (no API calls)
# ---------------------------------------------------------------------------

SIMPLE_PATTERNS = [
    r"^(what is|what's|who is|who's|when (is|was)|where is|define|spell)\b",
    r"^(translate|convert|format|list|summarize in one)\b",
    r"\b(current (date|time|weather)|capital of|population of)\b",
]

MEDIUM_PATTERNS = [
    r"\b(function|class|script|program|module|api|endpoint)\b",
    r"\b(write|implement|build|create|code|debug|fix|explain how)\b",
    r"\b(with (error handling|retry|logging|tests|validation|auth))\b",
    r"\b(step.?by.?step|how (do|does|can|should) (i|we|you))\b",
]

COMPLEX_PATTERNS = [
    r"\b(architect|design system|refactor|optimize|benchmark|research|compare|analyze|evaluate|strategy|tradeoff)\b",
    r"\b(multi.?step|end.?to.?end|production.?ready|scalable|comprehensive|in.?depth)\b",
    r"\b(math|proof|theorem|derive|differential equation|algorithm design)\b",
    r"\b(write a (paper|report|essay|specification|whitepaper))\b",
    r"\b(distributed|microservice|infrastructure|architecture|system design)\b",
]


def _heuristic_tier(query: str) -> Tier:
    q = query.lower().strip()
    word_count = len(q.split())

    # Complex signals (check first — take priority)
    for pat in COMPLEX_PATTERNS:
        if re.search(pat, q):
            return 3

    # Simple signals
    if word_count <= 10:
        for pat in SIMPLE_PATTERNS:
            if re.search(pat, q):
                return 1

    # Medium signals
    for pat in MEDIUM_PATTERNS:
        if re.search(pat, q):
            return 2

    # Length heuristic fallback
    if word_count <= 15:
        return 1
    elif word_count <= 60:
        return 2
    else:
        return 3


# ---------------------------------------------------------------------------
# LLM-based classifier (calls cheapest available model)
# ---------------------------------------------------------------------------

CLASSIFIER_PROMPT = """Rate the complexity of the following query on a scale of 1 to 3:
1 = Simple: factual lookup, formatting, translation, basic code snippet (<20 lines)
2 = Medium: multi-step reasoning, moderate coding task, research synthesis, drafting
3 = Complex: deep analysis, architectural decisions, long-form generation, hard math/science, anything requiring expert judgment

Respond with ONLY the digit 1, 2, or 3. No explanation.

Query: {query}"""


def _llm_tier(query: str, config) -> Tier:
    """Use the cheapest available model to classify query complexity."""
    import litellm

    from .config import available_models_for_tier

    classifiers = available_models_for_tier(1)
    if not classifiers:
        logger.warning("No Tier-1 models available for LLM classifier, falling back to heuristic.")
        return _heuristic_tier(query)

    model = classifiers[0]
    try:
        resp = litellm.completion(
            model=model,
            messages=[{
                "role": "user",
                "content": CLASSIFIER_PROMPT.format(query=query[:2000])  # cap at 2k chars
            }],
            max_tokens=5,
            temperature=0,
            timeout=15,
        )
        raw = resp.choices[0].message.content.strip()
        digit = int(re.search(r"[123]", raw).group())
        logger.debug(f"LLM classifier ({model}) → tier {digit}")
        return digit  # type: ignore
    except Exception as e:
        logger.warning(f"LLM classifier failed ({e}), falling back to heuristic.")
        return _heuristic_tier(query)


# ---------------------------------------------------------------------------
# RouteLLM classifier
# ---------------------------------------------------------------------------

def _routellm_tier(query: str, config) -> Tier:
    """
    Use RouteLLM's pre-trained router to decide strong vs weak.
    Maps to tier 1 (weak) or tier 3 (strong); tier 2 used for mid-range.
    """
    try:
        from routellm.controller import Controller

        from .config import available_models_for_tier

        strong = available_models_for_tier(3)
        weak   = available_models_for_tier(1)
        if not strong or not weak:
            raise ValueError("Need both Tier-1 and Tier-3 models for RouteLLM.")

        # RouteLLM expects OpenAI-style model names; we strip provider prefix for it
        def strip(m): return m.split("/", 1)[-1]

        client = Controller(
            routers=[config.routellm_router],
            strong_model=strip(strong[0]),
            weak_model=strip(weak[0]),
        )
        # Use the router's score method if available, else do a dry completion
        score = client.routers[config.routellm_router].calculate_strong_win_rate(query)
        if score < 0.33:
            return 1
        elif score < 0.67:
            return 2
        else:
            return 3
    except Exception as e:
        logger.warning(f"RouteLLM classifier failed ({e}), falling back to LLM classifier.")
        return _llm_tier(query, config)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def classify(query: str, config=None) -> Tier:
    """Classify query and return complexity tier (1, 2, or 3)."""
    if config is None:
        from .config import DEFAULT_CONFIG
        config = DEFAULT_CONFIG

    backend = config.classifier_backend

    if backend == "heuristic":
        tier = _heuristic_tier(query)
    elif backend == "routellm":
        tier = _routellm_tier(query, config)
    else:  # default: "llm"
        tier = _llm_tier(query, config)

    logger.info(f"Classified as Tier {tier} (backend={backend}): {query[:60]!r}")
    return tier
