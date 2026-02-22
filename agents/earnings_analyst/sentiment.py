"""
agents/earnings_analyst/sentiment.py
Uses the router (Haiku) to score earnings call sentiment per quarter.
Falls back to news headline analysis if no transcript available.
"""

import sys
from pathlib import Path
WORKSPACE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE))

from router import route

SYSTEM = """You are a financial analyst scoring earnings call sentiment.
Score 0.0 (very negative) to 1.0 (very positive).
Be precise. Base score on language confidence, guidance tone, and management outlook."""

TONES = {
    (0.0, 0.35): "Cautious",
    (0.35, 0.5): "Mixed",
    (0.5, 0.65): "Neutral",
    (0.65, 0.8): "Confident",
    (0.8, 1.01): "Bullish",
}


def _tone(score: float) -> str:
    for (lo, hi), label in TONES.items():
        if lo <= score < hi:
            return label
    return "Neutral"


def score_quarter(ticker: str, quarter_label: str, news_headlines: list,
                  financials_summary: str) -> dict:
    """Score one quarter's sentiment using available context."""
    headlines_text = "\n".join(f"- {h}" for h in news_headlines[:5]) if news_headlines else "None available"

    prompt = f"""
Company: {ticker}  Quarter: {quarter_label}
Financial summary: {financials_summary[:500]}
Recent news/headlines: {headlines_text}

Based on the financials and news tone, score this quarter's management sentiment 0.0-1.0.
Reply with ONLY: score|one_word_tone|one_sentence_summary
Example: 0.72|Confident|Management guided upward on AI revenue with strong margin expansion.
"""
    result = route(prompt, system_prompt=SYSTEM, force_tier=1)
    raw = result.content.strip() if result.success else ""

    try:
        parts = raw.split("|")
        score = float(parts[0].strip())
        score = max(0.0, min(1.0, score))
        tone  = parts[1].strip() if len(parts) > 1 else _tone(score)
        note  = parts[2].strip() if len(parts) > 2 else ""
        return {"label": quarter_label, "score": score, "tone": tone, "note": note}
    except Exception:
        return {"label": quarter_label, "score": 0.5, "tone": "Neutral", "note": "Data unavailable"}


def score_all(ticker: str, quarters: list, news: list) -> list:
    """Score sentiment for each quarter. Returns list of sentiment dicts."""
    results = []
    for q in quarters:
        summary = (
            f"Revenue: {q.get('revenue', 'N/A')}, "
            f"Gross Margin: {q.get('gross_margin', 'N/A')}%, "
            f"Op Income: {q.get('op_income', 'N/A')}, "
            f"FCF: {q.get('fcf', 'N/A')}"
        )
        s = score_quarter(ticker, q["label"], news, summary)
        results.append(s)
    return results
