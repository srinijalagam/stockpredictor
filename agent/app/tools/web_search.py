"""Trusted-source web search.

Uses Tavily when TAVILY_API_KEY is configured, otherwise falls back to a
keyless DuckDuckGo search. In both cases results are filtered to the trusted
domain allowlist so the agent only grounds on reputable sources.
"""
from __future__ import annotations

import logging
from urllib.parse import urlparse

from ..config import get_settings
from ..models import Source

logger = logging.getLogger(__name__)


def _domain_of(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:  # noqa: BLE001
        return ""


def _is_trusted(url: str, trusted: list[str]) -> bool:
    domain = _domain_of(url)
    return any(domain == d or domain.endswith("." + d) for d in trusted)


def _tavily_search(query: str, max_results: int, trusted: list[str]) -> list[Source]:
    from tavily import TavilyClient

    settings = get_settings()
    client = TavilyClient(api_key=settings.tavily_api_key)
    resp = client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
        include_domains=trusted,
    )
    out: list[Source] = []
    for r in resp.get("results", []):
        url = r.get("url", "")
        if not _is_trusted(url, trusted):
            continue
        out.append(
            Source(
                title=r.get("title", ""),
                url=url,
                publisher=_domain_of(url),
                snippet=(r.get("content", "") or "")[:400],
                kind="web",
            )
        )
    return out


def _ddg_search(query: str, max_results: int, trusted: list[str]) -> list[Source]:
    from ddgs import DDGS

    out: list[Source] = []
    with DDGS() as ddgs:
        # Over-fetch because we filter aggressively to trusted domains.
        results = list(ddgs.text(query, max_results=max_results * 5))
    for r in results:
        url = r.get("href") or r.get("url", "")
        if not url or not _is_trusted(url, trusted):
            continue
        out.append(
            Source(
                title=r.get("title", ""),
                url=url,
                publisher=_domain_of(url),
                snippet=(r.get("body", "") or "")[:400],
                kind="web",
            )
        )
        if len(out) >= max_results:
            break
    return out


def trusted_web_search(query: str) -> list[Source]:
    """Run a single search query, returning only trusted-source results."""
    settings = get_settings()
    trusted = settings.trusted_domain_list
    max_results = settings.max_search_results

    if settings.tavily_api_key:
        try:
            return _tavily_search(query, max_results, trusted)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Tavily search failed (%s); falling back to DuckDuckGo", exc)

    try:
        return _ddg_search(query, max_results, trusted)
    except Exception as exc:  # noqa: BLE001
        logger.warning("DuckDuckGo search failed: %s", exc)
        return []


def search_company_intel(company_name: str, ticker: str) -> list[Source]:
    """Search several angles: analyst ratings, news, earnings — trusted only."""
    queries = [
        f"{company_name} ({ticker}) analyst rating price target",
        f"{company_name} stock news latest",
        f"{ticker} earnings results guidance outlook",
    ]
    seen: set[str] = set()
    collected: list[Source] = []
    for q in queries:
        for src in trusted_web_search(q):
            if src.url and src.url not in seen:
                seen.add(src.url)
                collected.append(src)
    return collected
