"""
agents/earnings_analyst/run.py
Main entry point. Given a company name or ticker, produces a chart-heavy
earnings PDF and sends it to Telegram.

Usage:
    python agents/earnings_analyst/run.py AAPL
    python agents/earnings_analyst/run.py "Microsoft"
    python agents/earnings_analyst/run.py NVDA --quarters 5
"""

import argparse
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE))

import httpx

from agents.earnings_analyst.data import get_ticker, fetch_financials
from agents.earnings_analyst.charts import (
    chart_revenue, chart_margins, chart_eps,
    chart_income_fcf, chart_stock, chart_sentiment, cleanup
)
from agents.earnings_analyst.sentiment import score_all
from agents.earnings_analyst.pdf_gen import generate
from router import route

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("earnings")

TELEGRAM_CHAT_ID = "8296787175"


def _get_token() -> str:
    try:
        with open(Path.home() / ".openclaw" / "openclaw.json") as f:
            cfg = json.load(f)
        return cfg.get("channels", {}).get("telegram", {}).get("botToken", "")
    except Exception:
        return os.environ.get("TELEGRAM_BOT_TOKEN", "")


def _send_pdf(pdf_path: str, caption: str):
    token = _get_token()
    if not token:
        log.warning("No Telegram token — PDF not sent")
        return
    with open(pdf_path, "rb") as f:
        httpx.post(
            f"https://api.telegram.org/bot{token}/sendDocument",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={"document": (Path(pdf_path).name, f, "application/pdf")},
            timeout=60,
        )
    log.info("PDF sent to Telegram")


def _llm_summary(data: dict, sentiment: list) -> str:
    """One-paragraph AI summary of the company's recent trajectory."""
    q = data["quarters"]
    s = sentiment

    def _rev(qi):
        r = qi.get("revenue")
        return f"${r/1e9:.1f}B" if r else "N/A"
    def _gm(qi):
        g = qi.get("gross_margin")
        return f"{g:.1f}%" if g else "N/A"
    qs_text = " | ".join(f"{qi['label']}: Rev {_rev(qi)}, GM {_gm(qi)}" for qi in q[:4])
    sent_text = " | ".join(f"{si['label']}: {si['tone']} ({si['score']:.2f})" for si in s)

    prompt = (
        f"Company: {data['company_name']} ({data['ticker']})\n"
        f"Quarterly financials: {qs_text}\n"
        f"Management sentiment: {sent_text}\n\n"
        "Write a 2-sentence executive assessment of this company's recent trajectory. "
        "Be direct. Lead with momentum direction (accelerating/decelerating/stable). "
        "End with the single biggest thing to watch next quarter."
    )
    result = route(prompt, force_tier=1)
    return result.content.strip() if result.success else ""


def run(company: str, n_quarters: int = 4):
    log.info(f"Starting earnings analysis: {company}")

    # 1. Resolve ticker + fetch data
    ticker = get_ticker(company)
    log.info(f"Ticker: {ticker}")
    data = fetch_financials(ticker, n_quarters)
    log.info(f"Fetched {len(data['quarters'])} quarters for {data['company_name']}")

    if not data["quarters"]:
        _send_pdf.__doc__  # silence lint
        token = _get_token()
        if token:
            httpx.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": f"No financial data found for: {company} ({ticker})"},
                timeout=15,
            )
        return

    chart_paths = {}
    img_files   = []

    # 2. Score sentiment
    log.info("Scoring sentiment...")
    sentiment = score_all(ticker, data["quarters"], data["news"])

    # 3. LLM summary
    log.info("Generating summary...")
    summary = _llm_summary(data, sentiment)

    # 4. Generate charts
    log.info("Generating charts...")
    try:
        p = chart_revenue(data["quarters"])
        chart_paths["revenue"] = p; img_files.append(p)
    except Exception as e:
        log.warning(f"Revenue chart failed: {e}")

    try:
        p = chart_margins(data["quarters"])
        chart_paths["margins"] = p; img_files.append(p)
    except Exception as e:
        log.warning(f"Margins chart failed: {e}")

    if data["eps_data"]:
        try:
            p = chart_eps(data["eps_data"])
            chart_paths["eps"] = p; img_files.append(p)
        except Exception as e:
            log.warning(f"EPS chart failed: {e}")

    try:
        p = chart_income_fcf(data["quarters"])
        chart_paths["income_fcf"] = p; img_files.append(p)
    except Exception as e:
        log.warning(f"Income/FCF chart failed: {e}")

    if not data["stock_hist"].empty:
        try:
            p = chart_stock(data["stock_hist"], data["company_name"])
            chart_paths["stock"] = p; img_files.append(p)
        except Exception as e:
            log.warning(f"Stock chart failed: {e}")

    if sentiment:
        try:
            p = chart_sentiment(list(reversed(sentiment)))
            chart_paths["sentiment"] = p; img_files.append(p)
        except Exception as e:
            log.warning(f"Sentiment chart failed: {e}")

    # 5. Generate PDF
    pdf_path = str(Path(tempfile.gettempdir()) / f"earnings_{ticker}.pdf")
    log.info(f"Generating PDF: {pdf_path}")
    generate(data, chart_paths, sentiment, summary, pdf_path)

    # 6. Send to Telegram
    latest = data["quarters"][0] if data["quarters"] else {}
    caption = (
        f"<b>{data['company_name']} ({ticker}) — Earnings Snapshot</b>\n"
        f"{data.get('sector','')} | {n_quarters} quarters\n\n"
        f"{summary}"
    )
    _send_pdf(pdf_path, caption)

    # 7. Cleanup
    cleanup(img_files)
    try:
        os.remove(pdf_path)
    except Exception:
        pass

    log.info("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("company", help="Company name or ticker (e.g. AAPL or 'Apple')")
    parser.add_argument("--quarters", type=int, default=4, help="Number of quarters (default 4)")
    args = parser.parse_args()
    run(args.company, args.quarters)
