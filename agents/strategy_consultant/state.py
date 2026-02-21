"""
agents/strategy_consultant/state.py
Engagement state management — folder creation, context doc, index.
"""

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import ENGAGEMENTS_DIR, ENGAGEMENTS_INDEX, ProjectType, Proactivity, WORKSTREAMS


def _slug(text: str) -> str:
    text = text.lower().strip()[:40]
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


class EngagementState:
    """
    Manages all state for a single consulting engagement.
    Persists to disk under engagements/YYYY-MM-DD-{slug}/
    """

    def __init__(self, engagement_id: str):
        self.engagement_id = engagement_id
        self.dir = ENGAGEMENTS_DIR / engagement_id
        self._config: dict = {}
        self._intake: dict = {}

    # ── Factory methods ───────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        title: str,
        project_type: ProjectType = ProjectType.GENERAL,
        proactivity: Proactivity = Proactivity.MEDIUM,
        client_name: str = "",
    ) -> "EngagementState":
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        eid = f"{date_str}-{_slug(title)}"
        state = cls(eid)
        state.dir.mkdir(parents=True, exist_ok=True)
        (state.dir / "data").mkdir(exist_ok=True)
        (state.dir / "workstreams").mkdir(exist_ok=True)
        (state.dir / "comms").mkdir(exist_ok=True)

        state._config = {
            "engagement_id": eid,
            "title": title,
            "client_name": client_name,
            "project_type": project_type.value,
            "proactivity": proactivity.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "intake",
            "stakeholders": [],
        }
        state._save_config()
        state._init_context()

        # Add to index
        _index_add(eid, title, project_type, client_name)
        return state

    @classmethod
    def load(cls, engagement_id: str) -> "EngagementState":
        state = cls(engagement_id)
        cfg_path = state.dir / "config.json"
        if not cfg_path.exists():
            raise FileNotFoundError(f"Engagement not found: {engagement_id}")
        with open(cfg_path) as f:
            state._config = json.load(f)
        intake_path = state.dir / "intake.json"
        if intake_path.exists():
            with open(intake_path) as f:
                state._intake = json.load(f)
        return state

    # ── Config accessors ──────────────────────────────────────────────────────

    @property
    def title(self) -> str:         return self._config.get("title", "")
    @property
    def project_type(self) -> str:  return self._config.get("project_type", "general")
    @property
    def proactivity(self) -> str:   return self._config.get("proactivity", "medium")
    @property
    def client_name(self) -> str:   return self._config.get("client_name", "")
    @property
    def status(self) -> str:        return self._config.get("status", "intake")

    def set_status(self, status: str):
        self._config["status"] = status
        self._save_config()

    def add_stakeholder(self, name: str, role: str, contact: str):
        self._config.setdefault("stakeholders", []).append(
            {"name": name, "role": role, "contact": contact}
        )
        self._save_config()

    # ── Intake ────────────────────────────────────────────────────────────────

    def save_intake(self, intake: dict):
        self._intake = intake
        with open(self.dir / "intake.json", "w") as f:
            json.dump(intake, f, indent=2)

    def get_intake(self) -> dict:
        return self._intake

    # ── Context document ──────────────────────────────────────────────────────

    def _init_context(self):
        ctx = f"""# Engagement Context: {self._config['title']}
Created: {self._config['created_at']}
Client: {self._config.get('client_name', 'TBD')}
Project Type: {self._config['project_type']}
Proactivity: {self._config['proactivity']}

---
## Problem Statement
(To be filled during intake)

## Key Questions
(To be filled during intake)

## Data & Files Provided
(To be populated by Data Processing Agent)

## Workstream Summaries
(To be populated by each agent)
"""
        self.write_context(ctx)

    def read_context(self) -> str:
        ctx_path = self.dir / "context.md"
        if ctx_path.exists():
            return ctx_path.read_text(encoding="utf-8")
        return ""

    def write_context(self, content: str):
        (self.dir / "context.md").write_text(content, encoding="utf-8")

    def append_context(self, section: str, content: str):
        existing = self.read_context()
        self.write_context(existing + f"\n\n## {section}\n{content}")

    # ── Workstream files ──────────────────────────────────────────────────────

    def write_workstream(self, name: str, content: str):
        path = self.dir / "workstreams" / f"{name}.md"
        path.write_text(content, encoding="utf-8")

    def read_workstream(self, name: str) -> str:
        path = self.dir / "workstreams" / f"{name}.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def all_workstreams(self) -> dict:
        result = {}
        for ws in WORKSTREAMS:
            content = self.read_workstream(ws)
            if content:
                result[ws] = content
        return result

    # ── Data files ────────────────────────────────────────────────────────────

    def data_dir(self) -> Path:
        return self.dir / "data"

    def list_data_files(self) -> list:
        return [f.name for f in self.data_dir().iterdir() if f.is_file()]

    def comms_log(self, entry: str):
        log_path = self.dir / "comms" / "log.jsonl"
        with open(log_path, "a") as f:
            f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "entry": entry}) + "\n")

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save_config(self):
        with open(self.dir / "config.json", "w") as f:
            json.dump(self._config, f, indent=2)


# ── Engagement Index ──────────────────────────────────────────────────────────

def _load_index() -> list:
    if ENGAGEMENTS_INDEX.exists():
        with open(ENGAGEMENTS_INDEX) as f:
            return json.load(f)
    return []

def _save_index(index: list):
    ENGAGEMENTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ENGAGEMENTS_INDEX, "w") as f:
        json.dump(index, f, indent=2)

def _index_add(eid: str, title: str, project_type: ProjectType, client: str):
    index = _load_index()
    index.append({
        "engagement_id": eid,
        "title": title,
        "project_type": project_type.value,
        "client": client,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    _save_index(index)

def search_engagements(query: str = "", project_type: str = "") -> list:
    """Search historical engagements by keyword or type."""
    index = _load_index()
    results = []
    for e in index:
        if query and query.lower() not in (e.get("title","") + e.get("client","")).lower():
            continue
        if project_type and e.get("project_type") != project_type:
            continue
        results.append(e)
    return results
