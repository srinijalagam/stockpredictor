"""Yahoo Finance data gathering via yfinance."""
from __future__ import annotations

import logging
from typing import Any

import yfinance as yf
from curl_cffi import requests as curl_requests

from ..models import Source

logger = logging.getLogger(__name__)


def _session():
    """A browser-impersonating session to avoid Yahoo's 429 rate limiting.

    Yahoo aggressively throttles plain/datacenter requests; impersonating a
    real Chrome client dramatically improves reliability.
    """
    try:
        return curl_requests.Session(impersonate="chrome")
    except Exception as exc:  # noqa: BLE001
        logger.warning("could not create curl_cffi session: %s", exc)
        return None


def _safe(fn, default=None):
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - yfinance raises many ad-hoc errors
        logger.debug("yfinance call failed: %s", exc)
        return default


def resolve_ticker(query: str) -> tuple[str, str]:
    """Resolve a free-text query (ticker or company name) to (ticker, name).

    Tries a direct ticker lookup first, then Yahoo's search endpoint.
    """
    query = query.strip()
    session = _session()

    # 1) Try as a direct ticker symbol.
    try:
        t = yf.Ticker(query, session=session)
        info = t.info or {}
        if info.get("regularMarketPrice") is not None or info.get("symbol"):
            symbol = info.get("symbol", query.upper())
            name = info.get("longName") or info.get("shortName") or symbol
            return symbol, name
    except Exception as exc:  # noqa: BLE001
        logger.debug("direct ticker lookup failed for %s: %s", query, exc)

    # 2) Fall back to Yahoo search (company name -> ticker).
    try:
        search = yf.Search(query, max_results=5, session=session)
        quotes = getattr(search, "quotes", []) or []
        for q in quotes:
            if q.get("quoteType") in {"EQUITY", "ETF"} and q.get("symbol"):
                return q["symbol"], q.get("longname") or q.get("shortname") or q["symbol"]
        if quotes:
            q = quotes[0]
            return q.get("symbol", query.upper()), q.get("longname") or q.get("shortname") or query
    except Exception as exc:  # noqa: BLE001
        logger.debug("yahoo search failed for %s: %s", query, exc)

    return query.upper(), query


def _round(value: Any, ndigits: int = 2):
    try:
        return round(float(value), ndigits)
    except (TypeError, ValueError):
        return None


def gather_yahoo_data(ticker: str) -> dict[str, Any]:
    """Pull a broad snapshot of Yahoo Finance data for a ticker."""
    t = yf.Ticker(ticker, session=_session())
    info: dict[str, Any] = _safe(lambda: t.info, {}) or {}

    # Price history summary (1y).
    hist_summary: dict[str, Any] = {}
    hist = _safe(lambda: t.history(period="1y", interval="1d"))
    if hist is not None and not hist.empty:
        closes = hist["Close"].dropna()
        if not closes.empty:
            hist_summary = {
                "last_close": _round(closes.iloc[-1]),
                "low_52w": _round(closes.min()),
                "high_52w": _round(closes.max()),
                "avg_50d": _round(closes.tail(50).mean()),
                "avg_200d": _round(closes.tail(200).mean()),
                "pct_change_1m": _round(
                    (closes.iloc[-1] / closes.iloc[-22] - 1) * 100 if len(closes) > 22 else None
                ),
                "pct_change_6m": _round(
                    (closes.iloc[-1] / closes.iloc[-126] - 1) * 100 if len(closes) > 126 else None
                ),
                "pct_change_1y": _round((closes.iloc[-1] / closes.iloc[0] - 1) * 100),
            }

    # Analyst recommendations / price targets.
    price_targets = {
        "current": info.get("currentPrice") or info.get("regularMarketPrice"),
        "target_mean": info.get("targetMeanPrice"),
        "target_low": info.get("targetLowPrice"),
        "target_high": info.get("targetHighPrice"),
        "target_median": info.get("targetMedianPrice"),
        "num_analysts": info.get("numberOfAnalystOpinions"),
        "recommendation_key": info.get("recommendationKey"),
        "recommendation_mean": info.get("recommendationMean"),
    }

    fundamentals = {
        "market_cap": info.get("marketCap"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "peg_ratio": info.get("pegRatio"),
        "price_to_book": info.get("priceToBook"),
        "profit_margins": info.get("profitMargins"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "debt_to_equity": info.get("debtToEquity"),
        "return_on_equity": info.get("returnOnEquity"),
        "free_cashflow": info.get("freeCashflow"),
        "beta": info.get("beta"),
        "dividend_yield": info.get("dividendYield"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
    }

    # Recent Yahoo-aggregated news (used as sources too).
    news_items = _safe(lambda: t.news, []) or []
    news: list[dict[str, Any]] = []
    sources: list[Source] = []
    for item in news_items[:8]:
        content = item.get("content", item) if isinstance(item, dict) else {}
        title = content.get("title") or item.get("title", "")
        provider = ""
        prov = content.get("provider") or {}
        if isinstance(prov, dict):
            provider = prov.get("displayName", "")
        url = ""
        canonical = content.get("canonicalUrl") or content.get("clickThroughUrl") or {}
        if isinstance(canonical, dict):
            url = canonical.get("url", "")
        url = url or item.get("link", "")
        summary = content.get("summary", "") or content.get("description", "")
        if title:
            news.append({"title": title, "publisher": provider, "url": url, "summary": summary})
            sources.append(
                Source(title=title, url=url, publisher=provider or "Yahoo Finance",
                       snippet=summary[:280], kind="yahoo")
            )

    return {
        "ticker": ticker,
        "company_name": info.get("longName") or info.get("shortName") or ticker,
        "website": info.get("website", ""),
        "currency": info.get("currency", "USD"),
        "current_price": price_targets["current"],
        "business_summary": (info.get("longBusinessSummary") or "")[:1500],
        "price_history": hist_summary,
        "price_targets": price_targets,
        "fundamentals": fundamentals,
        "news": news,
        "sources": sources,
    }
