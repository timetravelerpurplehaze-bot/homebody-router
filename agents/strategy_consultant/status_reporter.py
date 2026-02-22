"""
agents/strategy_consultant/status_reporter.py
Background thread that sends a Telegram status update every N minutes during an engagement.
"""

import json
import threading
import time
import httpx
from datetime import datetime, timezone
from pathlib import Path


def _get_telegram_token() -> str:
    token = ""
    try:
        with open(Path.home() / ".openclaw" / "openclaw.json") as f:
            cfg = json.load(f)
        token = cfg.get("channels", {}).get("telegram", {}).get("botToken", "")
    except Exception:
        pass
    return token


def _send(token: str, chat_id: str, text: str):
    try:
        httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=15,
        )
    except Exception:
        pass


class StatusReporter:
    """
    Runs in a background daemon thread.
    Every `interval_s` seconds, fires a Telegram message with current engagement status.

    Usage:
        reporter = StatusReporter(chat_id="8296787175", title="BCG Deck Builder")
        reporter.start()
        reporter.set_phase("analysis", ["research", "frameworks"])
        reporter.complete_workstream("research")
        reporter.stop()
    """

    PHASE_LABELS = {
        "intake":    "Phase 1/7: Intake",
        "data":      "Phase 2/7: Data Processing",
        "analysis":  "Phase 3/7: Parallel Analysis",
        "red_team":  "Phase 4/7: Red Team Review",
        "synthesis": "Phase 5/7: Synthesis",
        "writing":   "Phase 6/7: Writing Report",
        "delivered": "Phase 7/7: Delivered",
    }

    def __init__(self, chat_id: str, title: str, engagement_id: str = "",
                 interval_s: int = 300):
        self.chat_id       = chat_id
        self.title         = title
        self.engagement_id = engagement_id
        self.interval_s    = interval_s
        self.token         = _get_telegram_token()

        self._phase        = "intake"
        self._running_ws   = []
        self._done_ws      = []
        self._failed_ws    = []
        self._start_time   = time.monotonic()
        self._last_sent    = 0.0

        self._lock         = threading.Lock()
        self._stop_event   = threading.Event()
        self._thread       = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        if not self.token:
            return  # no token, silently skip
        self._thread.start()
        self._send_update(force=True)   # immediate "started" message

    def stop(self):
        self._stop_event.set()

    def set_phase(self, phase: str, running_workstreams: list = None):
        with self._lock:
            self._phase = phase
            self._running_ws = running_workstreams or []
        self._send_update()

    def complete_workstream(self, name: str):
        with self._lock:
            if name in self._running_ws:
                self._running_ws.remove(name)
            if name not in self._done_ws:
                self._done_ws.append(name)

    def fail_workstream(self, name: str):
        with self._lock:
            if name in self._running_ws:
                self._running_ws.remove(name)
            if name not in self._failed_ws:
                self._failed_ws.append(name)

    def _elapsed(self) -> str:
        secs = int(time.monotonic() - self._start_time)
        return f"{secs // 60}m {secs % 60}s" if secs >= 60 else f"{secs}s"

    def _build_message(self) -> str:
        with self._lock:
            phase      = self._phase
            running_ws = list(self._running_ws)
            done_ws    = list(self._done_ws)
            failed_ws  = list(self._failed_ws)

        phase_label = self.PHASE_LABELS.get(phase, phase)
        elapsed     = self._elapsed()

        lines = [
            f"<b>Engagement Update</b>",
            f"<i>{self.title}</i>",
            f"",
            f"<b>Status:</b> {phase_label}",
            f"<b>Elapsed:</b> {elapsed}",
        ]

        if done_ws:
            lines.append(f"<b>Done:</b> {', '.join(done_ws)}")
        if running_ws:
            lines.append(f"<b>Running:</b> {', '.join(running_ws)}")
        if failed_ws:
            lines.append(f"<b>Issues:</b> {', '.join(failed_ws)} (retrying/escalating)")

        # Progress bar
        total_ws = ["intake","research","frameworks","financial","benchmarks","red_team","synthesis","writer","communications"]
        done_count = len([w for w in done_ws if w in total_ws])
        bar_filled = int((done_count / len(total_ws)) * 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        lines.append(f"<b>Progress:</b> [{bar}] {done_count}/{len(total_ws)}")

        if phase == "delivered":
            lines.append("")
            lines.append("Report delivered to Telegram.")

        return "\n".join(lines)

    def _send_update(self, force: bool = False):
        now = time.monotonic()
        if not force and (now - self._last_sent) < self.interval_s:
            return
        msg = self._build_message()
        _send(self.token, self.chat_id, msg)
        self._last_sent = now

    def _loop(self):
        while not self._stop_event.wait(timeout=30):
            self._send_update()
