"""Fetch news / investor-relations content from the company's own website."""
from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from ..config import get_settings
from ..models import Source

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockPredictorBot/0.1)"}

# Common paths that host press releases / financial results.
_IR_HINTS = ("investor", "ir.", "press", "news", "media", "financial", "results")


def _fetch(client: httpx.Client, url: str) -> str | None:
    try:
        resp = client.get(url, headers=_HEADERS, follow_redirects=True)
        if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
            return resp.text
    except Exception as exc:  # noqa: BLE001
        logger.debug("fetch failed for %s: %s", url, exc)
    return None


def _clean_text(html: str, limit: int = 1200) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return text[:limit]


def fetch_company_news(website: str, company_name: str) -> tuple[str, list[Source]]:
    """Return (extracted_text, sources) from the company site + IR pages."""
    if not website:
        return "", []

    settings = get_settings()
    base = website if website.startswith("http") else f"https://{website}"
    domain = urlparse(base).netloc

    collected_text: list[str] = []
    sources: list[Source] = []

    with httpx.Client(timeout=settings.http_timeout) as client:
        home_html = _fetch(client, base)
        if home_html:
            collected_text.append(_clean_text(home_html, 800))
            sources.append(
                Source(title=f"{company_name} — official site", url=base,
                       publisher=domain, snippet="Company homepage", kind="company")
            )

            # Discover investor / press links from the homepage.
            soup = BeautifulSoup(home_html, "lxml")
            candidate_links: list[str] = []
            for a in soup.find_all("a", href=True):
                href = a["href"].lower()
                text = a.get_text(" ").lower()
                if any(h in href or h in text for h in _IR_HINTS):
                    full = urljoin(base, a["href"])
                    if urlparse(full).netloc.endswith(domain.split(".", 1)[-1]):
                        candidate_links.append(full)

            for link in list(dict.fromkeys(candidate_links))[:3]:
                page = _fetch(client, link)
                if page:
                    collected_text.append(_clean_text(page, 800))
                    sources.append(
                        Source(title=f"{company_name} — investor/news page", url=link,
                               publisher=urlparse(link).netloc,
                               snippet="Investor relations / press content", kind="company")
                    )

    return "\n\n".join(t for t in collected_text if t), sources
