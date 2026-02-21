"""
agents/strategy_consultant/agents/research.py
Research Agent — web intelligence, competitor tracking, news, papers.
"""

import httpx
from bs4 import BeautifulSoup
from .base import BaseAgent

SYSTEM = """You are a research analyst on a consulting team. You have gathered raw web intelligence.
Your job: extract only what is strategically relevant, cite sources, flag recency of data.
No padding. No summaries of summaries. Just signal."""

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}


class ResearchAgent(BaseAgent):
    name = "research"
    default_tier = 1

    def _default_system(self): return SYSTEM

    def _fetch(self, url: str, max_chars: int = 4000) -> str:
        try:
            r = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return text[:max_chars]
        except Exception as e:
            return f"[Fetch failed: {e}]"

    def search_topic(self, topic: str, sources: list[str] = None) -> str:
        """Fetch and synthesize content from multiple sources on a topic."""
        default_sources = [
            f"https://news.ycombinator.com/search?q={topic.replace(' ', '+')}",
            f"https://techcrunch.com/search/{topic.replace(' ', '+')}",
        ]
        targets = sources or default_sources
        raw_parts = []
        for url in targets[:4]:
            content = self._fetch(url)
            if len(content) > 100:
                raw_parts.append(f"Source: {url}\n{content[:2000]}")

        if not raw_parts:
            return f"No research content found for: {topic}"

        combined = "\n\n---\n\n".join(raw_parts)
        return self.call(
            f"Topic: {topic}\n\nRaw research:\n{combined}\n\n"
            f"Extract the 5-8 most strategically relevant findings. Cite sources. Be specific.",
            force_tier=2,
        )

    def competitor_intel(self, company: str) -> str:
        sources = [
            f"https://www.crunchbase.com/organization/{company.lower().replace(' ','-')}",
            f"https://techcrunch.com/search/{company.replace(' ', '+')}",
        ]
        raw = []
        for url in sources:
            content = self._fetch(url)
            if len(content) > 100:
                raw.append(f"[{url}]\n{content[:2000]}")
        combined = "\n\n".join(raw) if raw else f"Limited data available for {company}"
        return self.call(
            f"Company: {company}\n\nIntel gathered:\n{combined}\n\n"
            f"Summarize: funding, products, recent moves, team signals, strategic direction. Flag what's uncertain.",
            force_tier=2,
        )

    def arxiv_research(self, topic: str) -> str:
        url = f"https://arxiv.org/search/?searchtype=all&query={topic.replace(' ', '+')}&start=0"
        content = self._fetch(url)
        return self.call(
            f"Topic: {topic}\n\narXiv search results:\n{content[:3000]}\n\n"
            f"List the 3-5 most relevant papers with title, authors, and one-sentence significance.",
        )

    def run(self, topic: str, competitors: list[str] = None, include_papers: bool = False) -> str:
        parts = []
        parts.append(f"# Research: {topic}\n")
        parts.append("## Market & News Intelligence\n" + self.search_topic(topic))

        if competitors:
            parts.append("\n## Competitor Intelligence")
            for co in competitors[:3]:
                parts.append(f"\n### {co}\n" + self.competitor_intel(co))

        if include_papers:
            parts.append("\n## Academic / Technical Research\n" + self.arxiv_research(topic))

        return "\n\n".join(parts)

    def validate(self) -> dict:
        try:
            result = self.run("AI model routing optimization", competitors=["Anthropic"])
            passed = len(result) > 200
            return {"passed": passed, "output": result[:300], "notes": "Web research + competitor intel test"}
        except Exception as e:
            return {"passed": False, "output": "", "notes": str(e)}
