# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

---

## 🤖 Model Tiering Strategy

**Default escalation ladder (use the cheapest that works):**

| Tier | Model | Use When |
|------|-------|----------|
| 1 — Haiku | `anthropic/claude-haiku-4-5` | Simple tasks: answering questions, formatting, quick lookups, summaries, heartbeats, light coding |
| 2 — Sonnet | `anthropic/claude-sonnet-4-6` | Medium tasks: multi-step reasoning, code debugging, research synthesis, drafting |
| 3 — Opus | `anthropic/claude-opus-4-6` | Hard tasks: complex planning, deep analysis, architectural decisions, anything that failed at lower tiers |

**Rules:**
- **Heartbeats always use Haiku** — set via `agents.defaults.heartbeat.model` in config
- **Start at Haiku** for all sub-agents and cron tasks unless clearly complex
- **Escalate to Sonnet** if the task needs multi-step reasoning or the output matters a lot
- **Escalate to Opus** sparingly — only when Sonnet isn't enough or the stakes are high
- **Main session** (direct chat with Hazy) defaults to Sonnet — it's the conversational sweet spot
- Always use the **latest available version** of each tier

**In practice:**
- Spawning a sub-agent? → start with `model: "anthropic/claude-haiku-4-5"`
- Complex research or coding task? → `model: "anthropic/claude-sonnet-4-6"`
- Deep architectural work, hard reasoning, or last resort? → `model: "anthropic/claude-opus-4-6"`

---

## 🔀 Model Router (`router/`)

Complexity-aware routing across all LLM providers. Built on LiteLLM + RouteLLM.

**Location:** `C:\Users\timet\.openclaw\workspace\router\`

**Quick use:**
```python
from router import route
result = route("Your query here")
print(result.content, result.model_used)
```

**CLI:**
```bash
cd C:\Users\timet\.openclaw\workspace
python -m router.cli status                        # see available models
python -m router.cli "Your query"                  # auto-route
python -m router.cli --classify-only "Query"       # just get tier
python -m router.cli --tier 1 "Simple question"    # force tier
```

**Tiers:**
- Tier 1: haiku / gpt-4o-mini / gemini-flash (fast, cheap)
- Tier 2: sonnet / gpt-4o / gemini-pro (balanced)
- Tier 3: opus / gpt-4-turbo / gemini-ultra (powerful)

**Classifier backends:** `llm` (default, calls Tier-1), `heuristic` (free, regex), `routellm` (pre-trained)

**To activate:** add API keys to `router/.env` (copy from `router/.env.example`)

**Adding providers:** edit `TIERS` and `PROVIDER_API_KEYS` in `router/config.py`

---

## 📊 Earnings Analyst Skill (`agents/earnings_analyst/`)

**Trigger:** Any request to summarize a company, get an external view, earnings report, financial snapshot.

**Run:**
```bash
python agents/earnings_analyst/run.py AAPL
python agents/earnings_analyst/run.py "Microsoft" --quarters 5
```

**Output:** Dark-mode PDF (charts: revenue, margins, EPS, income/FCF, stock, sentiment) → Telegram

**Skill file:** `agents/earnings_analyst/SKILL.md`

---

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

---

Add whatever helps you do your job. This is your cheat sheet.
