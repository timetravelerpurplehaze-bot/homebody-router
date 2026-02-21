"""
agents/ai_research/run.py
Main entry point for the AI Research Digest agent.

Usage:
    python -m agents.ai_research.run
    python agents/ai_research/run.py

Fetches latest AI papers → summarizes via model router → generates PDF → sends to Telegram.
"""

import json
import logging
import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx

# Ensure workspace root is on path
WORKSPACE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE))

from agents.ai_research.fetch import fetch_all
from agents.ai_research.summarize import summarize_all
from agents.ai_research.pdf_gen import generate_pdf

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ai_research")

# ── Config ─────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    "8063539579:AAHALJ2jOLBPo_T4xfnaRsycQHpy8-6U9_M"  # loaded from openclaw config
)
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8296787175")
OPENCLAW_TELEGRAM_CONFIG = Path.home() / ".openclaw" / "openclaw.json"


def _load_telegram_config():
    """Try to load bot token and chat from OpenClaw config."""
    global TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    try:
        with open(OPENCLAW_TELEGRAM_CONFIG) as f:
            cfg = json.load(f)
        token = cfg.get("channels", {}).get("telegram", {}).get("botToken")
        if token:
            TELEGRAM_TOKEN = token
    except Exception:
        pass


def send_telegram_document(pdf_path: str, caption: str) -> bool:
    """Send the PDF as a Telegram document."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    try:
        with open(pdf_path, "rb") as f:
            resp = httpx.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "HTML"},
                files={"document": (Path(pdf_path).name, f, "application/pdf")},
                timeout=60,
            )
        result = resp.json()
        if result.get("ok"):
            logger.info("PDF sent to Telegram successfully")
            return True
        else:
            logger.error(f"Telegram API error: {result}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Telegram document: {e}")
        return False


def send_telegram_message(text: str) -> bool:
    """Send a plain text message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = httpx.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=30,
        )
        return resp.json().get("ok", False)
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def run():
    now = datetime.now(timezone.utc)
    two_days_ago = now - timedelta(days=2)
    date_range = f"{two_days_ago.strftime('%b %d')} – {now.strftime('%b %d, %Y')}"

    logger.info(f"=== AI Research Digest: {date_range} ===")
    _load_telegram_config()

    # 1. Fetch papers
    logger.info("Fetching papers from all sources...")
    papers = fetch_all(max_papers=30)
    if not papers:
        send_telegram_message("⚠️ AI Research Digest: No papers found this run.")
        return

    logger.info(f"Fetched {len(papers)} papers")

    # 2. Summarize via router
    logger.info("Summarizing papers via model router...")
    papers = summarize_all(papers, max_workers=4)

    # 3. Generate PDF
    pdf_path = os.path.join(tempfile.gettempdir(), f"ai_digest_{now.strftime('%Y%m%d_%H%M')}.pdf")
    logger.info(f"Generating PDF → {pdf_path}")
    generate_pdf(papers, pdf_path, date_range)

    # 4. Send to Telegram
    sources = list(dict.fromkeys(p.source for p in papers))
    caption = (
        f"🤖 <b>AI Research Digest</b>\n"
        f"📅 {date_range}\n"
        f"📄 {len(papers)} papers & posts\n"
        f"🔬 Sources: {', '.join(sources[:5])}"
        + (" + more" if len(sources) > 5 else "")
    )
    logger.info("Sending PDF to Telegram...")
    success = send_telegram_document(pdf_path, caption)

    if not success:
        logger.warning("PDF send failed, sending text fallback...")
        lines = [f"🤖 <b>AI Research Digest</b> — {date_range}\n"]
        for p in papers[:10]:
            lines.append(f"• <b>{p.title[:80]}</b>\n  {p.summary[:120]}...\n  {p.url}\n")
        send_telegram_message("\n".join(lines))

    # Cleanup temp file
    try:
        os.remove(pdf_path)
    except Exception:
        pass

    logger.info("=== Done ===")


if __name__ == "__main__":
    run()
