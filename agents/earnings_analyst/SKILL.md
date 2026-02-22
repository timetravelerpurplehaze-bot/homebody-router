# Skill: Earnings Analyst

## When to use this skill

Use this skill automatically whenever Hazy asks anything like:
- "Summarize [company]"
- "External view on [company]"
- "How is [company] doing?"
- "Earnings summary for [company]"
- "Give me a report on [company]"
- "What's the latest on [company]'s financials?"
- Any request for a company overview, quarterly performance, or financial snapshot

## What it does

Fetches 3-4 quarters of financial data, scores earnings call sentiment via AI,
generates 6 charts (revenue, margins, EPS, income/FCF, stock, sentiment),
composes a dark-mode PDF, and sends it directly to Telegram.

## How to run it

```bash
cd C:\Users\timet\.openclaw\workspace
python agents/earnings_analyst/run.py AAPL
python agents/earnings_analyst/run.py "Microsoft"
python agents/earnings_analyst/run.py NVDA --quarters 5
```

Or from Python:
```python
from agents.earnings_analyst.run import run
run("Apple")
run("NVDA", n_quarters=5)
```

## Output

- Dark-mode PDF, chart-heavy, minimal text
- Page 1: Metric summary boxes + Revenue + Margins
- Page 2: EPS surprise + Operating Income/FCF + Stock performance
- Page 3: Sentiment scores per quarter + news headlines
- Delivered to Telegram automatically

## Notes

- Works with company names OR tickers ("Apple" or "AAPL")
- Requires ANTHROPIC_API_KEY in router/.env (for sentiment scoring)
- Data source: Yahoo Finance (public companies only)
- Private companies will return no data — handle gracefully
