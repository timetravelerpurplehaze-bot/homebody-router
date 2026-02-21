"""
agents/strategy_consultant/config.py
Constants, project types, proactivity levels, and global configuration.
"""

from enum import Enum

# ── Proactivity ─────────────────────────────────────────────────────────────

class Proactivity(str, Enum):
    HIGH   = "high"    # challenges framing, unsolicited insights, mid-run updates
    MEDIUM = "medium"  # upfront Q&A, flags assumptions, one status check
    LOW    = "low"     # works with what's given, minimal interruption

# ── Project Types ────────────────────────────────────────────────────────────

class ProjectType(str, Enum):
    BUILD_BUY_PARTNER     = "build_buy_partner"
    MARKET_ENTRY          = "market_entry"
    AI_CAPABILITY         = "ai_capability_assessment"
    MA_INVESTMENT         = "ma_investment"
    PRODUCT_STRATEGY      = "product_strategy"
    COMPETITIVE_RESPONSE  = "competitive_response"
    DIGITAL_TRANSFORMATION= "digital_transformation"
    GO_TO_MARKET          = "go_to_market"
    ORGANIZATIONAL_DESIGN = "organizational_design"
    GENERAL               = "general"

PROJECT_TYPE_LABELS = {
    ProjectType.BUILD_BUY_PARTNER:      "Build vs Buy vs Partner",
    ProjectType.MARKET_ENTRY:           "Market Entry",
    ProjectType.AI_CAPABILITY:          "AI Capability Assessment",
    ProjectType.MA_INVESTMENT:          "M&A / Investment",
    ProjectType.PRODUCT_STRATEGY:       "Product Strategy",
    ProjectType.COMPETITIVE_RESPONSE:   "Competitive Response",
    ProjectType.DIGITAL_TRANSFORMATION: "Digital Transformation",
    ProjectType.GO_TO_MARKET:           "Go-to-Market",
    ProjectType.ORGANIZATIONAL_DESIGN:  "Organizational Design",
    ProjectType.GENERAL:                "General Strategy",
}

# ── Workstream names ─────────────────────────────────────────────────────────

WORKSTREAMS = [
    "intake",
    "research",
    "frameworks",
    "financial",
    "benchmarks",
    "redteam",
    "synthesis",
    "final_report",
]

# ── Model assignments ─────────────────────────────────────────────────────────

AGENT_MODELS = {
    "engagement_partner": "anthropic/claude-opus-4-6",
    "intake":             "anthropic/claude-sonnet-4-6",
    "data_processor":     "anthropic/claude-haiku-4-5",
    "research":           "anthropic/claude-haiku-4-5",
    "frameworks":         "anthropic/claude-sonnet-4-6",
    "financial":          "anthropic/claude-sonnet-4-6",
    "benchmarking":       "anthropic/claude-haiku-4-5",
    "red_team":           "anthropic/claude-sonnet-4-6",
    "synthesis":          "anthropic/claude-opus-4-6",
    "writer":             "anthropic/claude-sonnet-4-6",
    "communications":     "anthropic/claude-haiku-4-5",
}

# ── Paths ────────────────────────────────────────────────────────────────────

import os
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent.parent
ENGAGEMENTS_DIR = WORKSPACE / "engagements"
ENGAGEMENTS_INDEX = ENGAGEMENTS_DIR / "index.json"
