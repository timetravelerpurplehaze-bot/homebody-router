"""
agents/ai_research/fetch.py
Fetches latest AI research papers and news from multiple sources.
Returns a list of Paper dataclasses.
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("ai_research.fetch")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HomebodyResearchBot/1.0)"
}
TIMEOUT = 20


@dataclass
class Paper:
    title: str
    url: str
    source: str
    authors: str = ""
    abstract: str = ""
    summary: str = ""        # filled in by summarizer
    published: str = ""
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# HuggingFace Daily Papers  (best single source for trending papers)
# ---------------------------------------------------------------------------

def fetch_huggingface_papers(limit: int = 12) -> list[Paper]:
    papers = []
    try:
        r = httpx.get("https://huggingface.co/papers", headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        articles = soup.select("article") or soup.select("div.paper")
        for art in articles[:limit]:
            a = art.find("a", href=True)
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a["href"]
            if href.startswith("/"):
                href = "https://huggingface.co" + href
            # Abstract snippet if present
            abstract_el = art.find("p")
            abstract = abstract_el.get_text(strip=True) if abstract_el else ""
            if title and len(title) > 5:
                papers.append(Paper(
                    title=title,
                    url=href,
                    source="HuggingFace Daily Papers",
                    abstract=abstract[:600],
                ))
    except Exception as e:
        logger.warning(f"HuggingFace fetch failed: {e}")
    return papers


# ---------------------------------------------------------------------------
# ArXiv recent listings  (cs.AI, cs.LG, cs.CL)
# ---------------------------------------------------------------------------

def fetch_arxiv(category: str = "cs.LG", limit: int = 8) -> list[Paper]:
    papers = []
    try:
        url = f"https://arxiv.org/list/{category}/recent"
        r = httpx.get(url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        entries = soup.select("div.list-title, dl dt")
        # ArXiv uses <dt>/<dd> pairs
        dts = soup.select("dl dt")
        dds = soup.select("dl dd")
        for dt, dd in zip(dts[:limit], dds[:limit]):
            a = dt.find("a", href=re.compile(r"/abs/"))
            if not a:
                continue
            paper_url = "https://arxiv.org" + a["href"]
            title_el = dd.find("div", class_="list-title")
            title = title_el.get_text(strip=True).replace("Title:", "").strip() if title_el else a.get_text(strip=True)
            authors_el = dd.find("div", class_="list-authors")
            authors = authors_el.get_text(strip=True).replace("Authors:", "").strip() if authors_el else ""
            abstract_el = dd.find("p", class_="mathjax")
            abstract = abstract_el.get_text(strip=True) if abstract_el else ""
            if title:
                papers.append(Paper(
                    title=title[:200],
                    url=paper_url,
                    source=f"arXiv {category}",
                    authors=authors[:200],
                    abstract=abstract[:600],
                    tags=[category],
                ))
    except Exception as e:
        logger.warning(f"ArXiv {category} fetch failed: {e}")
    return papers


# ---------------------------------------------------------------------------
# Lab blogs
# ---------------------------------------------------------------------------

def fetch_openai_blog(limit: int = 4) -> list[Paper]:
    papers = []
    try:
        r = httpx.get("https://openai.com/news", headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=re.compile(r"/index/|/research/|/blog/")):
            title = a.get_text(strip=True)
            href = a["href"]
            if not href.startswith("http"):
                href = "https://openai.com" + href
            if len(title) > 10:
                papers.append(Paper(title=title, url=href, source="OpenAI Blog"))
            if len(papers) >= limit:
                break
    except Exception as e:
        logger.warning(f"OpenAI blog fetch failed: {e}")
    return papers


def fetch_anthropic_blog(limit: int = 4) -> list[Paper]:
    papers = []
    try:
        r = httpx.get("https://www.anthropic.com/news", headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=re.compile(r"/news/")):
            title = a.get_text(strip=True)
            href = a["href"]
            if not href.startswith("http"):
                href = "https://www.anthropic.com" + href
            if len(title) > 10:
                papers.append(Paper(title=title, url=href, source="Anthropic"))
            if len(papers) >= limit:
                break
    except Exception as e:
        logger.warning(f"Anthropic blog fetch failed: {e}")
    return papers


def fetch_deepmind_blog(limit: int = 4) -> list[Paper]:
    papers = []
    try:
        r = httpx.get("https://deepmind.google/discover/blog/", headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=re.compile(r"/discover/blog/")):
            title_el = a.find(["h2", "h3", "span"])
            title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
            href = a["href"]
            if not href.startswith("http"):
                href = "https://deepmind.google" + href
            if len(title) > 10:
                papers.append(Paper(title=title, url=href, source="Google DeepMind"))
            if len(papers) >= limit:
                break
    except Exception as e:
        logger.warning(f"DeepMind blog fetch failed: {e}")
    return papers


# ---------------------------------------------------------------------------
# Master fetcher
# ---------------------------------------------------------------------------

def fetch_all(max_papers: int = 30) -> list[Paper]:
    """Fetch from all sources, deduplicate, return up to max_papers."""
    all_papers: list[Paper] = []

    all_papers += fetch_huggingface_papers(limit=12)
    all_papers += fetch_arxiv("cs.LG", limit=6)
    all_papers += fetch_arxiv("cs.CL", limit=4)
    all_papers += fetch_openai_blog(limit=4)
    all_papers += fetch_anthropic_blog(limit=4)
    all_papers += fetch_deepmind_blog(limit=4)

    # Deduplicate by URL
    seen = set()
    unique = []
    for p in all_papers:
        if p.url not in seen and p.title:
            seen.add(p.url)
            unique.append(p)

    logger.info(f"Fetched {len(unique)} unique papers/posts from {len(all_papers)} raw items")
    return unique[:max_papers]
