# Model Router

Complexity-aware LLM routing with automatic fallback.
Built on [LiteLLM](https://github.com/BerriAI/litellm) + [RouteLLM](https://github.com/lm-sys/RouteLLM).

## Architecture

```
query
  │
  ▼
ComplexityClassifier  ←── backend: "llm" | "heuristic" | "routellm"
  │
  ▼  tier (1 / 2 / 3)
ModelSelector  ─── available models for tier (filtered by API keys present)
  │
  ▼
LiteLLM call  ──► success → RouteResult
  │ fail
  ▼
next model in tier → next tier (escalation) → error
```

## Tiers

| Tier | Intent | Current Models |
|------|--------|----------------|
| 1 — Fast | Simple lookups, formatting, short code | claude-haiku, gpt-4o-mini, gemini-flash |
| 2 — Balanced | Reasoning, moderate coding, drafts | claude-sonnet, gpt-4o, gemini-pro |
| 3 — Powerful | Deep analysis, architecture, hard problems | claude-opus, gpt-4-turbo, gemini-ultra |

## Setup

```bash
cp router/.env.example router/.env
# Edit .env with your API keys
```

## Usage

### As a library

```python
from router import route

# Auto-classify and route
result = route("Explain the CAP theorem and when to violate it")
print(result.content)
print(f"Used: {result.model_used} (tier {result.tier_used})")

# Force a tier
result = route("Format this as JSON", force_tier=1)

# With system prompt and custom config
from router import ModelRouter
from router.config import RouterConfig

r = ModelRouter(RouterConfig(
    classifier_backend="heuristic",   # no API call for classification
    allow_escalation=True,            # try higher tiers on failure
    log_file="router_log.jsonl",      # log all decisions
))
result = r.route("Your query", system_prompt="You are a data engineer.")
```

### From the CLI

```bash
# Check which models are available
python -m router.cli status

# Route a query
python -m router.cli "Design a distributed caching layer for 10M users"

# Just classify complexity without calling a model
python -m router.cli --classify-only "What is 2 + 2?"

# Force tier 1, JSON output
python -m router.cli --tier 1 --json "Summarize this in one sentence: ..."

# Use heuristic classifier (no API call) with no escalation
python -m router.cli --backend heuristic --no-escalation "Your query"
```

## Classifier Backends

| Backend | How it works | Cost | Accuracy |
|---------|-------------|------|----------|
| `llm` (default) | Calls cheapest Tier-1 model, asks it to score 1–3 | ~$0.00003 | High |
| `heuristic` | Regex + word count rules | Free | Moderate |
| `routellm` | RouteLLM pre-trained matrix-factorization router | Free (local) | High (research-grade) |

## Adding New Models

Edit `router/config.py` → `TIERS` dict. Any LiteLLM-supported model works.
Add the provider's API key env var to `PROVIDER_API_KEYS` if it's a new provider.

## Fallback Behavior

1. Try each model in the target tier (in priority order)
2. If all fail and `allow_escalation=True`, escalate to next tier
3. If all tiers exhausted, return `RouteResult(error=...)`

Each attempt is recorded in `RouteResult.attempts` for debugging.
