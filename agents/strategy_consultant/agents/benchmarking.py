"""
agents/strategy_consultant/agents/benchmarking.py
Benchmarking Agent — external validation against industry data, peers, and research.
"""

import httpx
from bs4 import BeautifulSoup
from .base import BaseAgent

SYSTEM = """You are a benchmarking analyst. Your job is to validate client assumptions
and claims against external market data, peer comparisons, and research.
Be specific about sources and data recency. Flag where benchmarks are unavailable or unreliable.
Don't make up numbers — note data gaps explicitly."""

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BenchmarkBot/1.0)"}

BENCHMARK_SOURCES = {
    "saas_metrics": [
        "https://www.saastr.com/",
        "https://openviewpartners.com/blog/",
    ],
    "ai_benchmarks": [
        "https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard",
        "https://paperswithcode.com/sota",
    ],
    "vc_market": [
        "https://news.crunchbase.com/",
        "https://techcrunch.com/startups/",
    ],
    "enterprise_tech": [
        "https://www.gartner.com/en/newsroom",
        "https://www.forrester.com/blogs/",
    ],
}


class BenchmarkingAgent(BaseAgent):
    name = "benchmarking"
    default_tier = 1

    def _default_system(self): return SYSTEM

    def _fetch(self, url: str) -> str:
        try:
            r = httpx.get(url, headers=HEADERS, timeout=12, follow_redirects=True)
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)[:3000]
        except Exception as e:
            return f"[Fetch failed: {e}]"

    def industry_benchmarks(self, metric: str, industry: str) -> str:
        search_url = f"https://www.google.com/search?q={industry}+{metric}+benchmark+industry+average+site:gartner.com+OR+site:forrester.com+OR+site:mckinsey.com"
        # Fall back to synthesized known benchmarks
        prompt = f"""
Industry: {industry}
Metric being benchmarked: {metric}

Based on well-established industry knowledge, provide:
1. Typical benchmark range for this metric in this industry
2. Top quartile performance
3. Median performance
4. Key factors that drive variance
5. Sources / basis for these benchmarks

Flag if data is >2 years old or if the benchmark varies significantly by sub-segment.
"""
        return self.call(prompt, force_tier=2)

    def peer_comparison(self, company: str, peers: list[str], metrics: list[str]) -> str:
        prompt = f"""
Company being assessed: {company}
Peer companies: {', '.join(peers)}
Metrics to compare: {', '.join(metrics)}

Build a peer comparison table. For each metric:
- Estimate or note known values for each company
- Identify where the company leads, is at parity, or lags
- Note source / confidence level for each data point

Use only publicly available information. Flag estimates vs. verified data.
"""
        return self.call(prompt, force_tier=2)

    def validate_claim(self, claim: str, context: str) -> str:
        """Red-check a specific claim with external evidence."""
        prompt = f"""
Claim to validate: "{claim}"
Context: {context}

Assess this claim:
1. Is it supported by external evidence? (cite what you know)
2. Is it directionally correct but imprecisely stated?
3. Is it overstated, understated, or unfounded?
4. What data would definitively confirm or refute it?

Be honest about uncertainty. Don't validate claims you can't verify.
"""
        return self.call(prompt, force_tier=2)

    def ai_model_benchmarks(self, models: list[str]) -> str:
        content = self._fetch("https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard")
        prompt = f"""
Models to benchmark: {', '.join(models)}
HuggingFace Arena data: {content[:2000]}

Summarize the relative performance of these models on:
- Coding tasks
- Reasoning / math
- Creative / writing
- Cost per token (approximate)
- Context window
- Key tradeoffs

Note data recency.
"""
        return self.call(prompt, force_tier=2)

    def run(self, context: str, claims: list[str] = None, peers: list[str] = None,
            industry: str = "", metrics: list[str] = None) -> str:
        parts = ["# External Benchmarking\n"]

        if industry and metrics:
            parts.append("## Industry Benchmarks")
            for metric in metrics[:4]:
                parts.append(f"\n### {metric}\n" + self.industry_benchmarks(metric, industry))

        if peers and metrics:
            company = context.split("\n")[0][:50]
            parts.append("\n## Peer Comparison\n" + self.peer_comparison(company, peers, metrics or []))

        if claims:
            parts.append("\n## Claim Validation")
            for claim in claims[:5]:
                parts.append(f"\n**Claim:** {claim}\n" + self.validate_claim(claim, context))

        if not parts[1:]:
            parts.append(self.call(
                f"Given this business context, identify the 5 most important external benchmarks "
                f"that should be tracked and what typical ranges look like:\n\n{context[:2000]}",
                force_tier=2
            ))

        return "\n".join(parts)

    def validate(self) -> dict:
        try:
            result = self.industry_benchmarks("NRR (Net Revenue Retention)", "B2B SaaS")
            passed = len(result) > 100
            return {"passed": passed, "output": result[:300], "notes": "Industry benchmark retrieval test (SaaS NRR)"}
        except Exception as e:
            return {"passed": False, "output": "", "notes": str(e)}
