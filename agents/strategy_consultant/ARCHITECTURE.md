# Strategy Consulting Multi-Agent System
## Architecture Design v1.0

---

## System Overview

A multi-agent system that operates as a senior strategy consulting team
specializing in tech & AI. Modeled on how elite consulting firms (McKinsey,
BCG, Bain) actually run engagements — not a chatbot, a team.

---

## Agent Roster

```
                        ┌──────────────────────────────────────┐
                        │       CLIENT / USER INPUT            │
                        │  (question, documents, data files)   │
                        └─────────────────┬────────────────────┘
                                          │
                                          ▼
                        ┌──────────────────────────────────────┐
                        │       ENGAGEMENT PARTNER             │  ← Opus
                        │  Master orchestrator & final judge   │
                        │  - Frames the problem                │
                        │  - Sets proactivity level (H/M/L)    │
                        │  - Creates workplan & assigns agents  │
                        │  - Final sign-off on all output      │
                        │  - Decides what external comms fire  │
                        └───┬─────────────────┬────────────────┘
                            │                 │
               ┌────────────▼──────┐    ┌─────▼──────────────────────┐
               │  INTAKE AGENT     │    │  DATA PROCESSING AGENT     │  ← Sonnet
               │  (Sonnet)         │    │  - Excel → DataFrames      │
               │  Domain-specific  │    │  - Word → structured text  │
               │  Q&A, requests    │    │  - PowerPoint → key slides │
               │  docs & context   │    │  - PDF → extracted content │
               │  per project type │    │  - Images → described      │
               └────────────┬──────┘    └─────┬──────────────────────┘
                            │                 │
                            └────────┬────────┘
                                     │  shared context doc
                         ┌───────────▼──────────────────────────┐
                         │         SHARED CONTEXT STORE         │
                         │  engagement/YYYY-MM-DD-slug/         │
                         │  ├── intake.json                     │
                         │  ├── data/  (uploaded files)         │
                         │  ├── context.md  (live brief)        │
                         │  ├── workstreams/                    │
                         │  └── final_report.pdf                │
                         └───┬──────┬──────┬──────┬────────────┘
                             │      │      │      │
              ┌──────────────┘  ┌───┘  ┌──┘  ┌──┘
              ▼                 ▼      ▼     ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │  RESEARCH    │  │  FRAMEWORKS  │  │  FINANCIAL   │  │  BENCHMARK   │
   │  AGENT       │  │  ANALYST     │  │  MODELER     │  │  AGENT       │
   │  (Haiku)     │  │  (Sonnet)    │  │  (Sonnet)    │  │  (Sonnet)    │
   │              │  │              │  │              │  │              │
   │ Web research │  │ Porter's 5   │  │ TAM/SAM/SOM  │  │ Industry KPIs│
   │ Papers/news  │  │ SWOT         │  │ ROI/NPV      │  │ Gartner data │
   │ Competitor   │  │ Wardley Maps │  │ Unit econ.   │  │ Comp metrics │
   │ intel        │  │ BCG Matrix   │  │ Scenarios    │  │ VC/M&A comps │
   │ Lab reports  │  │ Jobs-to-done │  │ Sensitivity  │  │ Tech bench-  │
   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │ marks        │
          │                 │                  │          └──────┬───────┘
          └─────────────────┼──────────────────┼────────────────┘
                            │    all outputs   │
                            ▼                  ▼
                   ┌────────────────────────────────┐
                   │       RED TEAM AGENT           │  ← Sonnet
                   │  Adversarial review of ALL     │
                   │  workstream outputs             │
                   │  - Challenges every assumption  │
                   │  - Stress-tests financials      │
                   │  - Devil's advocate             │
                   │  - "What did we miss?"          │
                   └────────────────┬───────────────┘
                                    │
                                    ▼
                   ┌────────────────────────────────┐
                   │      SYNTHESIS AGENT           │  ← Opus
                   │  - Integrates all workstreams  │
                   │  - Applies senior judgment     │
                   │  - Resolves contradictions     │
                   │  - Produces recommendation     │
                   └────────────────┬───────────────┘
                                    │
                   ┌────────────────┴───────────────┐
                   │                                │
                   ▼                                ▼
      ┌────────────────────────┐     ┌──────────────────────────┐
      │    WRITER AGENT        │     │  COMMUNICATIONS AGENT    │
      │    (Sonnet)            │     │  (Haiku)                 │
      │  - Executive summary   │     │  - Email (SMTP)          │
      │  - Full report PDF     │     │  - Telegram/WhatsApp     │
      │  - Slide deck outline  │     │  - Voice brief (TTS)     │
      │  - One-pager           │     │  - Stakeholder routing   │
      └───────────┬────────────┘     └──────────────────────────┘
                  │
                  ▼
            Final PDF → Telegram
```

---

## Project Types & Intake Questions

The Intake Agent detects project type and asks targeted questions:

| Project Type | Key Questions Asked |
|---|---|
| **Build vs Buy vs Partner** | Budget, timeline, existing capabilities, team size, IP sensitivity |
| **Market Entry** | Target market, beachhead, competitive moat, regulatory exposure |
| **AI Capability Assessment** | Current stack, data assets, talent, maturity level, competitors' moves |
| **M&A / Investment** | Target profile, strategic rationale, synergy thesis, integration capacity |
| **Product Strategy** | User segments, prior product history, tech constraints, GTM motion |
| **Competitive Response** | Competitor move, your position, available plays, speed constraints |
| **Digital Transformation** | Org size, current state, change capacity, budget, board mandate |

For each type, Intake Agent also asks:
- "Do you have any relevant internal data? (financials, product metrics, org charts)"
- "Any prior studies, RFPs, or strategy decks we should absorb?"
- "Who are the key stakeholders and what do they care about?"
- "What does success look like in 12 months? 3 years?"

---

## Proactivity Levels

Set per engagement. Controls how aggressively the system pushes back & follows up.

| Level | Behavior |
|---|---|
| **HIGH** | Challenges problem framing, asks follow-up questions mid-engagement, sends status updates, surfaces things client didn't ask about, recommends scope changes |
| **MEDIUM** | Asks clarifying questions upfront, delivers what was asked, flags major assumptions, one status check |
| **LOW** | Works with what's given, minimal interruption, delivers final output only |

---

## Data Processing Capabilities

The Data Processing Agent handles:

| Format | Library | Extracts |
|---|---|---|
| Excel (.xlsx, .xls) | openpyxl + pandas | Tables, named ranges, charts metadata |
| Word (.docx) | python-docx | Text, tables, headings structure |
| PowerPoint (.pptx) | python-pptx | Slide text, titles, speaker notes |
| PDF | pdfplumber | Text, tables, page structure |
| Images | vision model | Described and summarized |
| CSV | pandas | Structured data analysis |

All extracted content is normalized into `context.md` for downstream agents.

---

## Memory & History

```
workspace/
  engagements/
    YYYY-MM-DD-{slug}/          ← one folder per engagement
      intake.json               ← structured intake form
      config.json               ← proactivity level, client info, team
      data/                     ← uploaded raw files
      context.md                ← live running brief (all agents write here)
      workstreams/
        research.md
        frameworks.md
        financial.md
        benchmarks.md
        redteam.md
        synthesis.md
      comms/
        emails_sent.log
        messages_sent.log
      final_report.pdf
      slide_outline.md
    index.json                  ← searchable index of all engagements
```

On new engagement start, Engagement Partner searches `index.json` for
relevant prior engagements and surfaces them to the user.

---

## External Communication

The Communications Agent supports:

| Channel | Method | Use Case |
|---|---|---|
| **Telegram** | OpenClaw message tool | Status updates, PDF delivery, quick Q&A |
| **WhatsApp** | OpenClaw message tool | Same as Telegram |
| **Email** | SMTP (smtplib) | Formal deliverables, stakeholder briefings |
| **Voice** | TTS (OpenClaw tts tool) | Executive summaries read aloud |
| **Webhook** | httpx POST | Integration with Slack, Teams, custom systems |

Comms are gated — the Engagement Partner decides what goes out and to whom,
based on the stakeholder map collected during intake.

---

## External Benchmarking Sources

The Benchmarking Agent pulls from:

- **Gartner / Forrester**: web fetch of publicly available reports & press releases
- **Crunchbase / PitchBook**: funding rounds, valuations (web fetch)
- **arXiv / Semantic Scholar**: technical benchmarks for AI claims
- **CB Insights**: market maps, unicorn data
- **SEC EDGAR**: public company financials
- **LinkedIn / job postings**: talent signal, org change indicators
- **GitHub**: open source activity, developer mindshare
- **HuggingFace**: model benchmarks, adoption metrics

---

## Model Routing

Every agent call goes through the router:

| Agent | Default Tier | Escalates To |
|---|---|---|
| Engagement Partner | 3 (Opus) | — |
| Intake Agent | 2 (Sonnet) | 3 if complex domain |
| Data Processing | 1 (Haiku) | 2 for complex tables |
| Research | 1 (Haiku) | 2 for synthesis |
| Frameworks | 2 (Sonnet) | 3 for novel problems |
| Financial Modeler | 2 (Sonnet) | 3 for complex scenarios |
| Benchmarking | 1 (Haiku) | 2 for analysis |
| Red Team | 2 (Sonnet) | 3 for high-stakes |
| Synthesis | 3 (Opus) | — |
| Writer | 2 (Sonnet) | — |
| Communications | 1 (Haiku) | — |

---

## Build Plan (phases)

**Phase 1 — Core skeleton**
- Engagement folder structure + index
- Intake Agent with project type detection + question bank
- Data Processing Agent (Excel, Word, PPT, PDF)
- Engagement Partner orchestrator

**Phase 2 — Research & analysis workstreams**
- Research Agent
- Frameworks Analyst
- Financial Modeler
- Benchmarking Agent

**Phase 3 — Judgment & output**
- Red Team Agent
- Synthesis Agent
- Writer Agent (PDF output)

**Phase 4 — Communications**
- Telegram/WhatsApp delivery
- Email (SMTP)
- Voice summary
- Webhook stubs for Slack/Teams

**Phase 5 — Memory & learning**
- Engagement index
- Cross-engagement pattern recognition
- Client profile building
