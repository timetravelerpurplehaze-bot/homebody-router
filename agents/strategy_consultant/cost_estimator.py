"""
agents/strategy_consultant/cost_estimator.py
Estimates API cost before running a full engagement.
Shows a per-workstream breakdown and asks for approval.
"""

# ── Pricing (per 1M tokens, USD) ─────────────────────────────────────────────
# Source: Anthropic pricing as of Feb 2026
PRICING = {
    "anthropic/claude-haiku-4-5":   {"input": 0.80,   "output": 4.00},
    "anthropic/claude-sonnet-4-6":  {"input": 3.00,   "output": 15.00},
    "anthropic/claude-opus-4-6":    {"input": 15.00,  "output": 75.00},
    "openai/gpt-4o-mini":           {"input": 0.15,   "output": 0.60},
    "openai/gpt-4o":                {"input": 2.50,   "output": 10.00},
    "openai/gpt-4-turbo":           {"input": 10.00,  "output": 30.00},
    "gemini/gemini-2.0-flash":      {"input": 0.075,  "output": 0.30},
    "gemini/gemini-2.0-pro":        {"input": 1.25,   "output": 5.00},
}

def _cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING.get(model, {"input": 3.0, "output": 15.0})
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000

# ── Workstream token estimates ────────────────────────────────────────────────
# (input_tokens, output_tokens, model, n_calls, can_escalate_to_opus)
WORKSTREAM_ESTIMATES = {
    "intake": {
        "calls": [
            {"model": "anthropic/claude-sonnet-4-6", "input": 1500, "output": 1500, "label": "Problem framing + brief"},
        ],
        "escalation_risk": "medium",
    },
    "research": {
        "calls": [
            {"model": "anthropic/claude-haiku-4-5",  "input": 2000, "output": 800,  "label": "Market intel synthesis"},
            {"model": "anthropic/claude-sonnet-4-6", "input": 2000, "output": 1000, "label": "Competitor intel x3"},
        ],
        "escalation_risk": "low",
    },
    "frameworks": {
        "calls": [
            {"model": "anthropic/claude-sonnet-4-6", "input": 2000, "output": 2000, "label": "Framework x3 (Porter's, Value Chain, Ansoff)"},
            {"model": "anthropic/claude-opus-4-6",   "input": 4000, "output": 1500, "label": "Cross-framework synthesis"},
        ],
        "escalation_risk": "high",
    },
    "financial": {
        "calls": [
            {"model": "anthropic/claude-sonnet-4-6", "input": 2000, "output": 2000, "label": "TAM/SAM/SOM + ROI + scenarios"},
            {"model": "anthropic/claude-opus-4-6",   "input": 3000, "output": 2000, "label": "Scenario model (Opus)"},
        ],
        "escalation_risk": "high",
    },
    "benchmarks": {
        "calls": [
            {"model": "anthropic/claude-sonnet-4-6", "input": 2000, "output": 1500, "label": "Industry benchmarks + peer comparison"},
        ],
        "escalation_risk": "low",
    },
    "red_team": {
        "calls": [
            {"model": "anthropic/claude-sonnet-4-6", "input": 4000, "output": 2000, "label": "Assumption challenge + blind spots"},
            {"model": "anthropic/claude-opus-4-6",   "input": 3000, "output": 1500, "label": "Steelman opposition (Opus)"},
        ],
        "escalation_risk": "medium",
    },
    "synthesis": {
        "calls": [
            {"model": "anthropic/claude-opus-4-6",   "input": 6000, "output": 3000, "label": "Full synthesis (Opus)"},
            {"model": "anthropic/claude-opus-4-6",   "input": 3000, "output": 800,  "label": "Executive summary (Opus)"},
        ],
        "escalation_risk": "n/a",
    },
    "writer": {
        "calls": [
            {"model": "anthropic/claude-sonnet-4-6", "input": 3000, "output": 2000, "label": "Slide outline + PDF sections"},
        ],
        "escalation_risk": "low",
    },
    "communications": {
        "calls": [
            {"model": "anthropic/claude-haiku-4-5",  "input": 1000, "output": 500,  "label": "Delivery formatting"},
        ],
        "escalation_risk": "none",
    },
}


def estimate(proactivity: str = "medium", has_data_files: bool = False,
             n_competitors: int = 0) -> dict:
    """
    Returns a full cost estimate broken down by workstream.
    Proactivity=high adds ~30% overhead (more calls, longer outputs).
    """
    multiplier = {"low": 0.7, "medium": 1.0, "high": 1.4}.get(proactivity, 1.0)

    rows = []
    total_low = 0.0
    total_high = 0.0

    for ws_name, ws in WORKSTREAM_ESTIMATES.items():
        ws_low = 0.0
        ws_high = 0.0
        labels = []

        for call in ws["calls"]:
            base = _cost(call["model"], call["input"], call["output"])
            low_cost  = base * multiplier * 0.7   # optimistic (no timeouts/retries)
            high_cost = base * multiplier * 1.5   # pessimistic (retries, escalations)
            ws_low  += low_cost
            ws_high += high_cost
            labels.append(call["label"])

        # Extra competitor research calls
        if ws_name == "research" and n_competitors > 0:
            extra = _cost("anthropic/claude-sonnet-4-6", 2000, 1000) * n_competitors * multiplier
            ws_low  += extra * 0.7
            ws_high += extra * 1.5

        # Data processing is free (no LLM calls for structured files)
        if ws_name == "data" and has_data_files:
            ws_low = ws_high = 0.0

        rows.append({
            "workstream": ws_name,
            "labels": labels,
            "low":  round(ws_low,  4),
            "high": round(ws_high, 4),
            "escalation_risk": ws["escalation_risk"],
        })
        total_low  += ws_low
        total_high += ws_high

    return {
        "rows": rows,
        "total_low":  round(total_low,  3),
        "total_high": round(total_high, 3),
        "proactivity": proactivity,
        "note": "Estimates assume Anthropic-only. Add ~20% for retries and escalation to Opus on complex calls.",
    }


def format_estimate(est: dict) -> str:
    lines = [
        "",
        "=" * 58,
        "  ENGAGEMENT COST ESTIMATE",
        "=" * 58,
        f"  Proactivity: {est['proactivity'].upper()}",
        "",
        f"  {'Workstream':<22} {'Low':>8}  {'High':>8}  {'Escalation Risk'}",
        f"  {'-'*22} {'-'*8}  {'-'*8}  {'-'*15}",
    ]
    for row in est["rows"]:
        lines.append(
            f"  {row['workstream']:<22} ${row['low']:>7.3f}  ${row['high']:>7.3f}  {row['escalation_risk']}"
        )
    lines += [
        f"  {'-'*22} {'-'*8}  {'-'*8}",
        f"  {'TOTAL':<22} ${est['total_low']:>7.3f}  ${est['total_high']:>7.3f}",
        "=" * 58,
        f"  Estimated range: ${est['total_low']:.2f} - ${est['total_high']:.2f} USD",
        f"  {est['note']}",
        "=" * 58,
        "",
    ]
    return "\n".join(lines)


def confirm(est: dict, auto_approve_under: float = None) -> bool:
    """
    Print estimate and ask for user confirmation.
    auto_approve_under: if set, auto-approve if high estimate is under this amount.
    """
    print(format_estimate(est))

    if auto_approve_under and est["total_high"] <= auto_approve_under:
        print(f"  Auto-approved (under ${auto_approve_under:.2f} threshold)\n")
        return True

    try:
        answer = input(f"  Proceed with engagement? [y/N] (est. ${est['total_low']:.2f}-${est['total_high']:.2f}): ")
        return answer.strip().lower() in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False
