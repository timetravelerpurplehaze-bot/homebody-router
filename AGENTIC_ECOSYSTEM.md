# Agentic Ecosystem — Vision & Roadmap
**Owner:** Hazy  
**Maintained by:** Homebody (AI assistant)  
**Last updated:** 2026-02-21

This document captures everything built, everything discussed, and everything planned
for the agentic ecosystem. Update it as new ideas emerge.

---

## What's Built (as of Feb 2026)

### 1. Model Router (`router/`)
**Repo:** https://github.com/timetravelerpurplehaze-bot/homebody-router  
**Purpose:** Complexity-aware LLM routing with automatic fallback across providers.

**How it works:**
- Query → ComplexityClassifier (heuristic / LLM / RouteLLM) → Tier (1/2/3)
- Routes to best available model for that tier
- Falls back within tier, then escalates to next tier on failure
- Logs every decision for debugging

**Tiers:**
- Tier 1 (Fast/Cheap): Haiku, GPT-4o-mini, Gemini Flash
- Tier 2 (Balanced): Sonnet, GPT-4o, Gemini Pro
- Tier 3 (Powerful): Opus, GPT-4-turbo, Gemini Ultra

**Classifier backends:** `llm` (default), `heuristic` (free), `routellm` (pre-trained, research-grade)

**Status:** Complete. Needs API keys in `router/.env` to activate.

---

### 2. AI Research Digest Agent (`agents/ai_research/`)
**Purpose:** Every 2 days, fetches latest AI papers, summarizes via router, sends PDF to Telegram.

**Sources:**
- HuggingFace Daily Papers
- arXiv (cs.LG, cs.CL)
- OpenAI blog
- Anthropic news
- Google DeepMind blog

**Pipeline:** fetch → summarize (router) → PDF (fpdf2) → Telegram

**Cron:** Every 2 days at 9 AM Pacific (`0 9 */2 * *`)

**Status:** Complete and running. Summaries need `ANTHROPIC_API_KEY` in `router/.env`.

---

### 3. Strategy Consulting Multi-Agent System (`agents/strategy_consultant/`)
**Purpose:** Functions as a senior strategy consulting team for tech/AI engagements.
Modeled on McKinsey/BCG/Bain engagement structure.

**11 Agents:**

| Agent | Model | Role |
|---|---|---|
| Engagement Partner (orchestrator) | Opus | Master brain, workplan, final sign-off |
| Intake Agent | Sonnet | Senior partner discovery — domain-specific Q&A, requests docs |
| Data Processing Agent | Haiku | Excel, Word, PPT, PDF, CSV, image parsing |
| Research Agent | Haiku→Sonnet | Web intel, competitor tracking, arXiv |
| Frameworks Analyst | Sonnet | Porter's 5, SWOT, Wardley Maps, BCG, JTBD, Ansoff, Value Chain |
| Financial Modeler | Sonnet→Opus | TAM/SAM/SOM, ROI, unit economics, 3-scenario model |
| Benchmarking Agent | Sonnet | Gartner, Crunchbase, arXiv, SEC EDGAR, GitHub benchmarks |
| Red Team Agent | Sonnet→Opus | Adversarial review, assumption challenges, blind spots |
| Synthesis Agent | Opus | SCR narrative, final recommendation, executive summary |
| Writer Agent | Sonnet | PDF report + slide deck outline |
| Communications Agent | Haiku | Email, Telegram, WhatsApp, Voice, Webhook |

**Key features built:**
- Cost + time estimate shown before any API call fires (user must approve)
- Telegram status update every 5 minutes during engagement
- Proactivity levels: High / Medium / Low per engagement
- Parallel analysis workstreams (research + frameworks + financial + benchmarks run simultaneously)
- Per-engagement folder with all workstream outputs, data files, comms log, final PDF
- Historical engagement index — searchable across past engagements
- Project type auto-detection: Build vs Buy, Market Entry, AI Capability, M&A, Product Strategy, Competitive Response, Digital Transformation, Go-to-Market, Org Design
- Full validation suite — test each agent independently

**Validation:**
```bash
python -m agents.strategy_consultant.validate           # all agents
python -m agents.strategy_consultant.validate synthesis # one agent
```

**CLI:**
```bash
python -m agents.strategy_consultant.cli estimate --proactivity high --competitors "..."
python -m agents.strategy_consultant.cli engage "problem..." --client "..." --proactivity high
python -m agents.strategy_consultant.cli questions "problem..."
python -m agents.strategy_consultant.cli history
```

**Status:** Built and tested. First real engagement run: BCG — AI Deck Builder Build vs Buy.

---

## Ideas Discussed — Not Yet Built

### 4. Data Processing Extensions
- **Structured database inputs**: PostgreSQL / SQLite connectors so agents can query live data
- **Real-time data**: Pull live market data (Bloomberg, Refinitiv) as an input to financial modeling
- **Voice input**: Transcribe a client call and feed it directly into the intake agent

### 5. Strategy Consulting — Deeper Capabilities

**Intake improvements:**
- Multi-turn interview mode — agent asks questions over several messages, waits for answers, then proceeds
- Document upload via Telegram (user drops a file in chat, it auto-routes to data processing)
- Client profile persistence — builds a knowledge base per client over time

**Workstream improvements:**
- **Primary research agent**: Conduct actual surveys via SurveyMonkey/Typeform, analyze responses
- **Expert network simulation**: Agent drafts the questions you'd ask an expert network (GLG, Tegus)
- **Financial modeling with real data**: Pull SEC EDGAR filings and compute actual comps
- **Wardley Map visualizer**: Generate actual visual Wardley Maps (not just text analysis)
- **Slide deck generator**: Go from outline → actual PowerPoint file (python-pptx)

**Output improvements:**
- Word document output (editable, not just PDF)
- Auto-formatted PowerPoint deck from slide outline
- One-pager executive brief (single page PDF)
- Board memo format

**Communications:**
- **Email integration**: Wire SMTP so the comms agent can actually send emails to stakeholders
- **WhatsApp delivery**: Via Twilio or Meta Business API
- **Voice brief**: TTS audio summary sent to Telegram as voice message
- **Slack/Teams webhook**: Drop deliverables into team channels

### 6. Proactivity System
- **Scheduled check-ins**: Agent sends a Telegram message mid-engagement if a key assumption changes
- **Automated follow-up**: 2 weeks after delivery, agent asks "how did this land? any updates?"
- **Market change alerts**: If a major competitive move happens related to a past engagement, agent flags it

### 7. Knowledge Base / Memory
- **Cross-engagement pattern recognition**: "We've seen this build vs buy question 4 times — here's what we've learned"
- **Client profile builder**: Accumulates context on each client across engagements
- **Industry thesis library**: Agent builds and refines theses on specific industries over time
- **Template library**: Store approved frameworks, slide structures, memo formats per engagement type

### 8. Model Router Extensions
- **OpenAI integration**: Add GPT-4o / GPT-4-turbo once API key is added
- **Gemini integration**: Add Gemini Pro / Ultra once API key is added
- **Local models via Ollama**: Route cheap tasks to local Llama / Mistral to cut costs
- **RouteLLM pre-trained classifiers**: Upgrade from heuristic classifier to research-grade router
- **Cost tracking**: Log actual token usage and cost per engagement, report monthly spend
- **Rate limit management**: Queue and retry on rate limits instead of failing

### 9. New Agents / Skills (Future)

**Research & Intelligence:**
- **Patent Intelligence Agent**: Monitors patent filings in a tech domain, flags strategic signals
- **Talent Signal Agent**: Monitors LinkedIn job postings to infer competitor strategy
- **Regulatory Watch Agent**: Tracks regulatory developments relevant to client industries
- **Social Signal Agent**: Monitors Twitter/Reddit/HN for early signals on tech adoption

**Operations:**
- **Meeting Prep Agent**: Given a meeting agenda, briefs you on participants and talking points
- **Decision Logger**: Captures key decisions made in engagements for audit trail
- **Project Tracker**: Tracks open action items across engagements, sends reminders

**External Communication:**
- **Stakeholder Briefer**: Drafts and sends status emails to external stakeholders
- **Client Portal**: Simple web UI where clients can upload documents and track engagement status

### 10. Infrastructure

**Authentication & Security:**
- Proper API key rotation and secret management (not flat .env files)
- Per-agent rate limiting to prevent runaway costs
- Audit log of all external communications sent

**Monitoring:**
- Cost dashboard: daily/weekly spend by agent/engagement
- Latency tracking: which agents are slow, which are fast
- Error rate monitoring: which models fail most often

**Multi-user:**
- Multiple analysts can run engagements in parallel
- Per-user cost caps
- Shared engagement history across the team

---

## Architecture Principles

1. **Router-first**: Every LLM call goes through the router. No agent hardcodes a model.
2. **Cheapest model that works**: Haiku for simple, Sonnet for medium, Opus only when judgment matters.
3. **Fail gracefully**: Every agent has a fallback. Nothing crashes an engagement silently.
4. **Human in the loop**: Cost + time estimate always shown before API spend. User approves.
5. **Persistent memory**: Every engagement creates a folder. Nothing is lost between sessions.
6. **Composable**: Each agent can be called independently. The orchestrator just wires them together.
7. **Provenance**: Every output traces back to the agent, model, and workstream that produced it.
8. **External comms are gated**: The Engagement Partner decides what leaves the system. Agents don't send independently.

---

## Repository

**GitHub:** https://github.com/timetravelerpurplehaze-bot/homebody-router

```
workspace/
  router/                    ← Model router (LiteLLM + RouteLLM)
  agents/
    ai_research/             ← AI Research Digest (cron, every 2 days)
    strategy_consultant/     ← Strategy consulting multi-agent system
  engagements/               ← One folder per engagement (auto-created)
  AGENTIC_ECOSYSTEM.md       ← This file
  ARCHITECTURE.md            ← Strategy consultant architecture diagram
```

---

## Open Questions / To Explore

- Should the strategy consulting system be exposed as a web API so other tools can trigger engagements?
- Is there a case for a "lite" mode that skips Red Team and Synthesis for quick 15-minute briefings?
- How do we handle engagement confidentiality — should outputs be encrypted at rest?
- Should agents be able to spawn sub-agents recursively (e.g., Research Agent spawning 3 competitor sub-agents in parallel)?
- What does the UI look like eventually — pure Telegram, or a proper dashboard?

---

*Update this document whenever a new idea surfaces or a new agent is built.*
