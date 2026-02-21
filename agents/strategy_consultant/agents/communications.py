"""
agents/strategy_consultant/agents/communications.py
Communications Agent — Email, Telegram, WhatsApp, Voice, Webhooks.
"""

import json
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from .base import BaseAgent

SYSTEM = """You are drafting communications on behalf of a consulting team.
Write clearly, professionally, and concisely.
Adapt tone to channel: email = formal, messaging = direct, voice = conversational."""

# ── Channel config (from env vars) ──────────────────────────────────────────

def _get_telegram_token() -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        try:
            with open(Path.home() / ".openclaw" / "openclaw.json") as f:
                cfg = json.load(f)
            token = cfg.get("channels", {}).get("telegram", {}).get("botToken", "")
        except Exception:
            pass
    return token

SMTP_CONFIG = {
    "host":     os.environ.get("SMTP_HOST", "smtp.gmail.com"),
    "port":     int(os.environ.get("SMTP_PORT", "587")),
    "user":     os.environ.get("SMTP_USER", ""),
    "password": os.environ.get("SMTP_PASSWORD", ""),
}


class CommunicationsAgent(BaseAgent):
    name = "communications"
    default_tier = 1

    def _default_system(self): return SYSTEM

    # ── Draft helpers ─────────────────────────────────────────────────────────

    def draft_email(self, to: str, subject: str, context: str, tone: str = "formal") -> str:
        return self.call(f"""
Recipient: {to}
Subject: {subject}
Context / key points: {context}
Tone: {tone}

Write a professional email. Max 250 words.
Subject line is provided — write only the body.
""")

    def draft_message(self, platform: str, context: str) -> str:
        return self.call(f"""
Platform: {platform}
Context: {context}

Write a concise message (max 3 sentences for messaging apps).
Direct, no fluff.
""", force_tier=1)

    # ── Send methods ──────────────────────────────────────────────────────────

    def send_telegram(self, chat_id: str, text: str, pdf_path: str = None) -> bool:
        import httpx
        token = _get_telegram_token()
        if not token:
            self.logger.warning("No Telegram bot token configured")
            return False
        try:
            if pdf_path and Path(pdf_path).exists():
                with open(pdf_path, "rb") as f:
                    r = httpx.post(
                        f"https://api.telegram.org/bot{token}/sendDocument",
                        data={"chat_id": chat_id, "caption": text[:1024], "parse_mode": "HTML"},
                        files={"document": (Path(pdf_path).name, f, "application/pdf")},
                        timeout=60,
                    )
            else:
                r = httpx.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": text[:4096], "parse_mode": "HTML"},
                    timeout=30,
                )
            ok = r.json().get("ok", False)
            self.logger.info(f"Telegram send {'OK' if ok else 'FAILED'}: {r.json()}")
            return ok
        except Exception as e:
            self.logger.error(f"Telegram error: {e}")
            return False

    def send_whatsapp(self, to: str, text: str) -> bool:
        """Stub — wire to Twilio/360dialog/Meta Business API via env config."""
        import httpx
        wa_url   = os.environ.get("WHATSAPP_API_URL", "")
        wa_token = os.environ.get("WHATSAPP_API_TOKEN", "")
        if not wa_url or not wa_token:
            self.logger.warning("WhatsApp not configured (set WHATSAPP_API_URL + WHATSAPP_API_TOKEN)")
            return False
        try:
            r = httpx.post(
                wa_url,
                headers={"Authorization": f"Bearer {wa_token}"},
                json={"to": to, "type": "text", "text": {"body": text[:4000]}},
                timeout=30,
            )
            return r.status_code == 200
        except Exception as e:
            self.logger.error(f"WhatsApp error: {e}")
            return False

    def send_email(self, to: str, subject: str, body: str, attachment_path: str = None) -> bool:
        if not SMTP_CONFIG["user"]:
            self.logger.warning("SMTP not configured (set SMTP_USER + SMTP_PASSWORD env vars)")
            return False
        try:
            msg = MIMEMultipart()
            msg["From"]    = SMTP_CONFIG["user"]
            msg["To"]      = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            if attachment_path and Path(attachment_path).exists():
                with open(attachment_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={Path(attachment_path).name}")
                msg.attach(part)
            with smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as server:
                server.starttls()
                server.login(SMTP_CONFIG["user"], SMTP_CONFIG["password"])
                server.send_message(msg)
            self.logger.info(f"Email sent to {to}")
            return True
        except Exception as e:
            self.logger.error(f"Email error: {e}")
            return False

    def send_webhook(self, url: str, payload: dict) -> bool:
        import httpx
        try:
            r = httpx.post(url, json=payload, timeout=15)
            ok = r.status_code < 300
            self.logger.info(f"Webhook {'OK' if ok else 'FAILED'}: {url} → {r.status_code}")
            return ok
        except Exception as e:
            self.logger.error(f"Webhook error: {e}")
            return False

    def voice_brief(self, text: str) -> str:
        """Returns a voice-optimized version of the brief (for TTS)."""
        return self.call(f"""
Convert this strategy brief into a 60-second spoken summary.
Write as if you're presenting to an executive verbally — natural speech, no bullet points,
no headers, conversational transitions.

Brief:
{text[:2000]}
""", force_tier=1)

    # ── Orchestrated send ─────────────────────────────────────────────────────

    def run(self, engagement_state, synthesis_result: dict,
            pdf_path: str = None, channels: list = None) -> dict:
        """
        Send the final deliverable to all configured channels.
        channels: list of dicts like [{"type": "telegram", "to": "8296787175"}, ...]
        """
        if not channels:
            channels = [{"type": "telegram", "to": "8296787175"}]

        exec_summary = synthesis_result.get("executive_summary", "")
        caption = (
            f"<b>Strategy Report: {engagement_state.title}</b>\n\n"
            f"{exec_summary[:800]}...\n\n"
            f"<i>Full report attached.</i>"
        )

        results = {}
        for ch in channels:
            ch_type = ch.get("type", "")
            target  = ch.get("to", "")

            if ch_type == "telegram":
                ok = self.send_telegram(target, caption, pdf_path)
                results[f"telegram:{target}"] = ok

            elif ch_type == "whatsapp":
                ok = self.send_whatsapp(target, f"Strategy Report: {engagement_state.title}\n\n{exec_summary[:500]}")
                results[f"whatsapp:{target}"] = ok

            elif ch_type == "email":
                body = self.draft_email(target, f"Strategy Report: {engagement_state.title}", exec_summary)
                ok = self.send_email(target, f"Strategy Report: {engagement_state.title}", body, pdf_path)
                results[f"email:{target}"] = ok

            elif ch_type == "webhook":
                payload = {
                    "engagement": engagement_state.engagement_id,
                    "title": engagement_state.title,
                    "summary": exec_summary,
                    "pdf_available": pdf_path is not None,
                }
                ok = self.send_webhook(target, payload)
                results[f"webhook:{target}"] = ok

        if engagement_state:
            engagement_state.comms_log(str(results))

        return results

    def validate(self) -> dict:
        try:
            result = self.draft_email(
                to="ceo@example.com",
                subject="Strategy Engagement: AI Market Entry Recommendation",
                context="We recommend entering the healthcare AI market via partnerships. Key risk is regulatory. First step: identify 3 partner candidates by end of Q1.",
            )
            passed = len(result) > 80
            return {"passed": passed, "output": result[:300], "notes": "Email draft generation test"}
        except Exception as e:
            return {"passed": False, "output": "", "notes": str(e)}
