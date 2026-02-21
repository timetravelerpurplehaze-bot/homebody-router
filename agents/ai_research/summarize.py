"""
agents/ai_research/summarize.py
Uses the model router to generate crisp 2-3 sentence summaries for each paper.
Tier 1 models handle most summaries; abstracts with heavy math escalate to Tier 2.
"""

import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from router import ModelRouter
from router.config import RouterConfig

logger = logging.getLogger("ai_research.summarize")

SUMMARY_SYSTEM = """You are a concise AI research digest assistant.
Given a paper title and abstract (or title only), write a 2-3 sentence plain-English summary.
Focus on: what it does, why it matters, and who might care.
Do NOT use bullet points. Keep it under 60 words."""

SUMMARY_PROMPT = """Paper: {title}
Authors: {authors}
Source: {source}
Abstract: {abstract}

Write a 2-3 sentence summary."""

# Router config: use heuristic classifier (no extra API call per paper)
# and allow escalation in case a weak model struggles with heavy math
_router = ModelRouter(RouterConfig(
    classifier_backend="heuristic",
    allow_escalation=True,
    timeout_seconds=30,
))


def summarize_paper(paper) -> str:
    """Generate a summary for a single Paper. Returns summary string."""
    prompt = SUMMARY_PROMPT.format(
        title=paper.title,
        authors=paper.authors or "Unknown",
        source=paper.source,
        abstract=paper.abstract or "(no abstract available)",
    )

    result = _router.route(
        query=prompt,
        system_prompt=SUMMARY_SYSTEM,
    )

    if result.success:
        logger.debug(f"Summarized via {result.model_used} (tier {result.tier_used}): {paper.title[:50]}")
        return result.content.strip()
    else:
        logger.warning(f"Summary failed for '{paper.title}': {result.error}")
        return paper.abstract[:200] + "..." if paper.abstract else "(Summary unavailable)"


def summarize_all(papers: list, max_workers: int = 4) -> list:
    """
    Summarize all papers. Uses a thread pool for parallelism.
    Modifies papers in place (sets paper.summary), also returns the list.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _do(paper):
        paper.summary = summarize_paper(paper)
        return paper

    logger.info(f"Summarizing {len(papers)} papers with up to {max_workers} parallel workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_do, p): p for p in papers}
        for i, fut in enumerate(as_completed(futures), 1):
            p = futures[fut]
            try:
                fut.result()
                logger.info(f"[{i}/{len(papers)}] Done: {p.title[:60]}")
            except Exception as e:
                logger.warning(f"[{i}/{len(papers)}] Failed: {p.title[:60]} — {e}")
                p.summary = "(Summary unavailable)"

    return papers
