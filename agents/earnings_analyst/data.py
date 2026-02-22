"""
agents/earnings_analyst/data.py
Fetches quarterly financial data, estimates, and news via yfinance + web.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import yfinance as yf
import httpx
from bs4 import BeautifulSoup

WORKSPACE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE))

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EarningsBot/1.0)"}


def get_ticker(company: str) -> str:
    """Resolve company name to ticker if not already one."""
    # If it looks like a ticker already, return as-is uppercased
    if len(company) <= 5 and company.isalpha():
        return company.upper()
    # Try to resolve via yfinance search
    try:
        results = yf.Search(company, max_results=1).quotes
        if results:
            return results[0].get("symbol", company.upper())
    except Exception:
        pass
    return company.upper()


def fetch_financials(ticker_str: str, n_quarters: int = 4) -> dict:
    """
    Pull quarterly financials, balance sheet, and metadata for a ticker.
    Returns a structured dict ready for charting.
    """
    t = yf.Ticker(ticker_str)
    info = t.info or {}

    # --- Income statement ---
    try:
        inc = t.quarterly_income_stmt
        inc = inc[sorted(inc.columns, reverse=True)[:n_quarters]]
    except Exception:
        inc = pd.DataFrame()

    # --- Cash flow ---
    try:
        cf = t.quarterly_cashflow
        cf = cf[sorted(cf.columns, reverse=True)[:n_quarters]]
    except Exception:
        cf = pd.DataFrame()

    # --- EPS history ---
    try:
        eps_hist = t.earnings_history
        if eps_hist is not None and not eps_hist.empty:
            eps_hist = eps_hist.sort_index(ascending=False).head(n_quarters)
        else:
            eps_hist = pd.DataFrame()
    except Exception:
        eps_hist = pd.DataFrame()

    # --- Stock history ---
    try:
        hist = t.history(period="1y", interval="1mo")
    except Exception:
        hist = pd.DataFrame()

    # --- Recent news ---
    try:
        news = t.news or []
        news_headlines = [n.get("content", {}).get("title", "") for n in news[:8]]
    except Exception:
        news_headlines = []

    # --- Parse quarters ---
    quarters = []
    if not inc.empty:
        for col in sorted(inc.columns, reverse=True)[:n_quarters]:
            label = col.strftime("%b '%y") if hasattr(col, "strftime") else str(col)[:7]
            def _get(df, row):
                try:
                    return float(df.loc[row, col]) if row in df.index else None
                except Exception:
                    return None

            revenue    = _get(inc, "Total Revenue")
            gross      = _get(inc, "Gross Profit")
            op_income  = _get(inc, "Operating Income")
            net_income = _get(inc, "Net Income")
            rd         = _get(inc, "Research And Development")
            fcf        = _get(cf, "Free Cash Flow")

            gross_margin = (gross / revenue * 100) if gross and revenue else None
            op_margin    = (op_income / revenue * 100) if op_income and revenue else None

            quarters.append({
                "label":        label,
                "date":         col,
                "revenue":      revenue,
                "gross_profit": gross,
                "op_income":    op_income,
                "net_income":   net_income,
                "gross_margin": gross_margin,
                "op_margin":    op_margin,
                "rd_spend":     rd,
                "fcf":          fcf,
            })

    # --- EPS ---
    eps_data = []
    if not eps_hist.empty:
        for idx, row in eps_hist.iterrows():
            label = idx.strftime("%b '%y") if hasattr(idx, "strftime") else str(idx)[:7]
            eps_data.append({
                "label":    label,
                "actual":   row.get("epsActual"),
                "estimate": row.get("epsEstimate"),
                "surprise": row.get("surprisePercent"),
            })

    return {
        "ticker":       ticker_str,
        "company_name": info.get("longName", ticker_str),
        "sector":       info.get("sector", ""),
        "industry":     info.get("industry", ""),
        "market_cap":   info.get("marketCap"),
        "currency":     info.get("financialCurrency", "USD"),
        "description":  info.get("longBusinessSummary", "")[:500],
        "quarters":     quarters,
        "eps_data":     eps_data,
        "stock_hist":   hist,
        "news":         news_headlines,
        "info":         info,
    }


def _fmt(val, scale=1e9, suffix="B") -> str:
    if val is None:
        return "N/A"
    v = val / scale
    return f"${v:.1f}{suffix}"
