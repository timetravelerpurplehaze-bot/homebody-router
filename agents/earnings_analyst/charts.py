"""
agents/earnings_analyst/charts.py
Generates all matplotlib charts as PNG files for the earnings PDF.
Design: data-dense, minimal text, professional financial report style.
"""

import os
import tempfile
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from pathlib import Path

# ── Style constants ──────────────────────────────────────────────────────────

BG       = "#0f1117"
SURFACE  = "#1a1d27"
ACCENT   = "#4f8ef7"
GREEN    = "#22c55e"
RED      = "#ef4444"
AMBER    = "#f59e0b"
TEXT     = "#e2e8f0"
SUBTEXT  = "#94a3b8"
GRID     = "#2d3148"
WHITE    = "#ffffff"

plt.rcParams.update({
    "figure.facecolor":  BG,
    "axes.facecolor":    SURFACE,
    "axes.edgecolor":    GRID,
    "axes.labelcolor":   SUBTEXT,
    "axes.titlecolor":   TEXT,
    "axes.titlesize":    9,
    "axes.labelsize":    7,
    "axes.titlepad":     8,
    "xtick.color":       SUBTEXT,
    "ytick.color":       SUBTEXT,
    "xtick.labelsize":   7,
    "ytick.labelsize":   7,
    "grid.color":        GRID,
    "grid.linewidth":    0.5,
    "text.color":        TEXT,
    "font.family":       "DejaVu Sans",
    "font.size":         7,
})

TMPDIR = Path(tempfile.mkdtemp(prefix="earnings_"))


def _save(fig, name: str) -> str:
    path = str(TMPDIR / f"{name}.png")
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=BG, edgecolor="none")
    plt.close(fig)
    return path


def _bar_colors(values):
    return [GREEN if (v or 0) >= 0 else RED for v in values]


def _fmt_b(val):
    if val is None: return ""
    if abs(val) >= 1e9:  return f"${val/1e9:.1f}B"
    if abs(val) >= 1e6:  return f"${val/1e6:.0f}M"
    return f"${val:.0f}"


# ── Chart 1: Revenue trend ───────────────────────────────────────────────────

def chart_revenue(quarters: list) -> str:
    qs   = list(reversed(quarters))
    lbls = [q["label"] for q in qs]
    revs = [q["revenue"] for q in qs]
    revs_b = [(r / 1e9 if r else 0) for r in revs]

    # YoY growth
    yoy = [None]
    for i in range(1, len(revs)):
        if revs[i-1] and revs[i]:
            yoy.append((revs[i] - revs[i-1]) / abs(revs[i-1]) * 100)
        else:
            yoy.append(None)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 3.5), gridspec_kw={"height_ratios": [3, 1]})
    fig.subplots_adjust(hspace=0.35)

    # Revenue bars
    bars = ax1.bar(lbls, revs_b, color=ACCENT, width=0.55, zorder=3)
    ax1.set_title("Revenue (Quarterly)", fontweight="bold")
    ax1.set_ylabel("USD Billions", fontsize=6)
    ax1.yaxis.grid(True, zorder=0)
    for bar, val in zip(bars, revs):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                 _fmt_b(val), ha="center", va="bottom", fontsize=6.5, color=TEXT)

    # YoY growth line
    valid = [(i, v) for i, v in enumerate(yoy) if v is not None]
    if valid:
        xi, yi = zip(*valid)
        colors = [GREEN if v >= 0 else RED for v in yi]
        ax2.bar(xi, yi, color=colors, width=0.55, zorder=3)
        ax2.axhline(0, color=GRID, linewidth=0.8)
        ax2.set_xticks(range(len(lbls)))
        ax2.set_xticklabels(lbls)
        ax2.set_title("YoY Revenue Growth %", fontsize=7)
        ax2.yaxis.grid(True, zorder=0)
        for x, v in zip(xi, yi):
            ax2.text(x, v + (0.5 if v >= 0 else -1.5), f"{v:.1f}%",
                     ha="center", fontsize=6, color=GREEN if v >= 0 else RED)

    return _save(fig, "revenue")


# ── Chart 2: Margins ─────────────────────────────────────────────────────────

def chart_margins(quarters: list) -> str:
    qs   = list(reversed(quarters))
    lbls = [q["label"] for q in qs]
    gm   = [q["gross_margin"] for q in qs]
    om   = [q["op_margin"] for q in qs]

    fig, ax = plt.subplots(figsize=(5, 2.8))
    x = range(len(lbls))
    if any(v is not None for v in gm):
        ax.plot(x, gm, "o-", color=GREEN, linewidth=2, markersize=5, label="Gross Margin %", zorder=3)
        for xi, v in zip(x, gm):
            if v: ax.text(xi, v + 0.5, f"{v:.1f}%", ha="center", fontsize=6, color=GREEN)
    if any(v is not None for v in om):
        ax.plot(x, om, "s--", color=ACCENT, linewidth=2, markersize=5, label="Operating Margin %", zorder=3)
        for xi, v in zip(x, om):
            if v: ax.text(xi, v - 1.8, f"{v:.1f}%", ha="center", fontsize=6, color=ACCENT)
    ax.axhline(0, color=GRID, linewidth=0.7)
    ax.set_xticks(list(x))
    ax.set_xticklabels(lbls)
    ax.set_title("Gross & Operating Margins", fontweight="bold")
    ax.set_ylabel("%", fontsize=6)
    ax.yaxis.grid(True, zorder=0)
    ax.legend(fontsize=6, loc="best")
    return _save(fig, "margins")


# ── Chart 3: EPS Actual vs Estimate ─────────────────────────────────────────

def chart_eps(eps_data: list) -> str:
    eps = list(reversed(eps_data))
    lbls    = [e["label"] for e in eps]
    actuals = [e.get("actual") for e in eps]
    ests    = [e.get("estimate") for e in eps]
    surprises = [e.get("surprise") for e in eps]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 3.5), gridspec_kw={"height_ratios": [3, 1]})
    fig.subplots_adjust(hspace=0.4)
    x = np.arange(len(lbls))
    w = 0.35

    ax1.bar(x - w/2, actuals,  width=w, color=GREEN,  label="Actual EPS",   zorder=3)
    ax1.bar(x + w/2, ests,     width=w, color=SUBTEXT, label="Est. EPS", zorder=3, alpha=0.7)
    ax1.set_xticks(x)
    ax1.set_xticklabels(lbls)
    ax1.set_title("EPS: Actual vs Estimate", fontweight="bold")
    ax1.set_ylabel("USD", fontsize=6)
    ax1.yaxis.grid(True, zorder=0)
    ax1.legend(fontsize=6)
    for xi, a in zip(x, actuals):
        if a is not None:
            ax1.text(xi - w/2, a + 0.01, f"${a:.2f}", ha="center", fontsize=6, color=TEXT)

    # Surprise %
    if any(s is not None for s in surprises):
        s_colors = [GREEN if (s or 0) >= 0 else RED for s in surprises]
        ax2.bar(x, [s or 0 for s in surprises], color=s_colors, width=0.55, zorder=3)
        ax2.axhline(0, color=GRID, linewidth=0.7)
        ax2.set_xticks(x)
        ax2.set_xticklabels(lbls)
        ax2.set_title("EPS Surprise %", fontsize=7)
        ax2.yaxis.grid(True, zorder=0)
        for xi, s in zip(x, surprises):
            if s is not None:
                ax2.text(xi, s + (0.3 if s >= 0 else -1.2), f"{s:.1f}%",
                         ha="center", fontsize=6, color=GREEN if s >= 0 else RED)
    return _save(fig, "eps")


# ── Chart 4: Operating Income & FCF ─────────────────────────────────────────

def chart_income_fcf(quarters: list) -> str:
    qs   = list(reversed(quarters))
    lbls = [q["label"] for q in qs]
    oi   = [(q["op_income"] or 0) / 1e9 for q in qs]
    fcf  = [(q["fcf"] or 0) / 1e9 for q in qs]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(5, 2.6))
    ax1.bar(lbls, oi, color=_bar_colors(oi), width=0.55, zorder=3)
    ax1.axhline(0, color=GRID, linewidth=0.7)
    ax1.set_title("Operating Income ($B)", fontweight="bold")
    ax1.yaxis.grid(True, zorder=0)
    for i, v in enumerate(oi):
        ax1.text(i, v + 0.02 if v >= 0 else v - 0.15, f"${v:.1f}B",
                 ha="center", fontsize=6, color=GREEN if v >= 0 else RED)

    ax2.bar(lbls, fcf, color=_bar_colors(fcf), width=0.55, zorder=3)
    ax2.axhline(0, color=GRID, linewidth=0.7)
    ax2.set_title("Free Cash Flow ($B)", fontweight="bold")
    ax2.yaxis.grid(True, zorder=0)
    for i, v in enumerate(fcf):
        ax2.text(i, v + 0.02 if v >= 0 else v - 0.15, f"${v:.1f}B",
                 ha="center", fontsize=6, color=GREEN if v >= 0 else RED)
    return _save(fig, "income_fcf")


# ── Chart 5: Stock price ─────────────────────────────────────────────────────

def chart_stock(hist, company_name: str) -> str:
    if hist is None or hist.empty:
        return None
    fig, ax = plt.subplots(figsize=(5, 2.4))
    prices = hist["Close"].dropna()
    start  = prices.iloc[0]
    pct    = (prices / start - 1) * 100
    color  = GREEN if pct.iloc[-1] >= 0 else RED
    ax.plot(pct.index, pct.values, color=color, linewidth=1.8, zorder=3)
    ax.fill_between(pct.index, pct.values, alpha=0.15, color=color, zorder=2)
    ax.axhline(0, color=GRID, linewidth=0.8, linestyle="--")
    ax.set_title(f"{company_name} — 12M Stock Performance", fontweight="bold")
    ax.set_ylabel("% Return", fontsize=6)
    ax.yaxis.grid(True, zorder=0)
    last = pct.iloc[-1]
    ax.text(pct.index[-1], last, f" {last:+.1f}%", va="center", fontsize=7,
            color=color, fontweight="bold")
    return _save(fig, "stock")


# ── Chart 6: Sentiment gauge (horizontal bars) ────────────────────────────────

def chart_sentiment(sentiment_data: list) -> str:
    """sentiment_data: [{"label": "Q3 '24", "score": 0.72, "tone": "Confident"}, ...]"""
    if not sentiment_data:
        return None
    fig, ax = plt.subplots(figsize=(5, 2.4))
    labels = [d["label"] for d in sentiment_data]
    scores = [d["score"] for d in sentiment_data]
    tones  = [d.get("tone", "") for d in sentiment_data]
    colors = [GREEN if s >= 0.6 else (AMBER if s >= 0.4 else RED) for s in scores]

    y = range(len(labels))
    ax.barh(list(y), scores, color=colors, height=0.5, zorder=3)
    ax.axvline(0.5, color=SUBTEXT, linewidth=0.8, linestyle="--")
    ax.set_xlim(0, 1)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Sentiment Score (0 = Negative, 1 = Positive)", fontsize=6)
    ax.set_title("Earnings Call Sentiment by Quarter", fontweight="bold")
    ax.xaxis.grid(True, zorder=0)
    for i, (s, tone) in enumerate(zip(scores, tones)):
        ax.text(s + 0.02, i, f"{s:.2f}  {tone}", va="center", fontsize=6.5, color=TEXT)
    return _save(fig, "sentiment")


def cleanup(paths: list):
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
    try:
        TMPDIR.rmdir()
    except Exception:
        pass
