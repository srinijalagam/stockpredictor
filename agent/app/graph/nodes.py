"""Graph node implementations."""
from __future__ import annotations

import json
import logging
from datetime import date

from ..config import get_settings
from ..llm import get_llm
from ..models import Prediction
from ..tools.company_site import fetch_company_news
from ..tools.web_search import search_company_intel
from ..tools.yahoo_finance import gather_yahoo_data, resolve_ticker
from .state import AgentState

logger = logging.getLogger(__name__)


def resolve_node(state: AgentState) -> AgentState:
    query = state["query"]
    ticker, name = resolve_ticker(query)
    return {
        "ticker": ticker,
        "company_name": name,
        "steps": [f"Resolved '{query}' to ticker {ticker} ({name})."],
    }


def yahoo_node(state: AgentState) -> AgentState:
    ticker = state["ticker"]
    data = gather_yahoo_data(ticker)
    return {
        "yahoo": data,
        "company_name": data.get("company_name") or state.get("company_name", ""),
        "website": data.get("website", ""),
        "sources": data.get("sources", []),
        "steps": ["Gathered Yahoo Finance data: price history, fundamentals, analyst targets, news."],
    }


def web_node(state: AgentState) -> AgentState:
    name = state.get("company_name", state["ticker"])
    ticker = state["ticker"]
    sources = search_company_intel(name, ticker)
    step = (
        f"Searched trusted sources for analyst ratings & news ({len(sources)} results)."
        if sources
        else "Trusted-source web search returned no results."
    )
    return {"sources": sources, "steps": [step]}


def company_node(state: AgentState) -> AgentState:
    website = state.get("website", "")
    name = state.get("company_name", state["ticker"])
    if not website:
        return {"steps": ["No company website available; skipped IR/press scan."]}
    text, sources = fetch_company_news(website, name)
    step = (
        f"Read company website / investor pages ({len(sources)} pages)."
        if sources
        else "Could not read company website content."
    )
    return {"company_text": text, "sources": sources, "steps": [step]}


_SYSTEM_PROMPT = """You are a rigorous equity research analyst AI.
You produce a grounded buy/sell timing plan for a single stock.

Hard rules:
- Ground EVERY claim in the provided data (Yahoo Finance, trusted news/analyst
  sources, and the company's own disclosures). Do NOT invent numbers.
- Only trust the sources provided. If evidence is thin or conflicting, lower the
  confidence and say so in the risks.
- Provide concrete ENTRY and EXIT plans, each with a price range (low/high in the
  stock's currency) and a time window (human readable + approximate start/end dates).
- Base price ranges on current price, 52-week range, moving averages, and analyst
  price targets. Base time windows on catalysts (earnings, guidance, news cadence).
- 'strong_reasons' must be specific and cite the kind of evidence (e.g. "analyst
  mean target $X implies Y% upside", "trades below 200d avg", "Q_ earnings beat").
- Keep thought_process as a concise ordered list of the analytical steps you took.
- recommendation must be one of: STRONG_BUY, BUY, ACCUMULATE, HOLD, WAIT, SELL, AVOID.
"""


def _build_context(state: AgentState) -> str:
    yahoo = state.get("yahoo", {})
    sources = state.get("sources", [])
    web_sources = [s for s in sources if s.kind in {"web", "filing"}]
    company_sources = [s for s in sources if s.kind == "company"]

    parts: list[str] = []
    parts.append(f"TICKER: {state.get('ticker')}")
    parts.append(f"COMPANY: {state.get('company_name')}")
    parts.append(f"AS_OF: {date.today().isoformat()}")
    parts.append(f"CURRENCY: {yahoo.get('currency', 'USD')}")
    parts.append(f"BUSINESS: {yahoo.get('business_summary', '')}")
    parts.append("PRICE_HISTORY: " + json.dumps(yahoo.get("price_history", {})))
    parts.append("ANALYST_TARGETS: " + json.dumps(yahoo.get("price_targets", {})))
    parts.append("FUNDAMENTALS: " + json.dumps(yahoo.get("fundamentals", {})))

    if yahoo.get("news"):
        parts.append("YAHOO_NEWS:")
        for n in yahoo["news"][:6]:
            parts.append(f"- [{n.get('publisher','')}] {n.get('title','')}: {n.get('summary','')[:200]}")

    if web_sources:
        parts.append("TRUSTED_WEB_SOURCES:")
        for s in web_sources[:10]:
            parts.append(f"- [{s.publisher}] {s.title}: {s.snippet}")

    if company_sources or state.get("company_text"):
        parts.append("COMPANY_DISCLOSURES:")
        for s in company_sources[:4]:
            parts.append(f"- {s.title} ({s.url})")
        if state.get("company_text"):
            parts.append("COMPANY_SITE_EXCERPT: " + state["company_text"][:1500])

    return "\n".join(parts)


def predict_node(state: AgentState) -> AgentState:
    settings = get_settings()
    yahoo = state.get("yahoo", {})

    if not settings.has_llm:
        pred = Prediction(
            ticker=state.get("ticker", ""),
            company_name=state.get("company_name", ""),
            as_of=date.today().isoformat(),
            current_price=yahoo.get("current_price"),
            currency=yahoo.get("currency", "USD"),
            recommendation="HOLD",
            confidence=0.0,
            summary="LLM is not configured. Set OPENAI_API_KEY to enable predictions.",
            thought_process=["Collected data but no LLM key configured to analyze it."],
        )
        return {
            "prediction": pred,
            "warnings": ["OPENAI_API_KEY is not set; returned data-only response."],
            "steps": ["Skipped LLM analysis (no API key)."],
        }

    context = _build_context(state)
    llm = get_llm(temperature=0.2)
    structured = llm.with_structured_output(Prediction)

    try:
        pred: Prediction = structured.invoke(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Analyze the following evidence and produce the timing plan.\n\n"
                        + context
                    ),
                },
            ]
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("LLM prediction failed")
        pred = Prediction(
            ticker=state.get("ticker", ""),
            company_name=state.get("company_name", ""),
            as_of=date.today().isoformat(),
            current_price=yahoo.get("current_price"),
            currency=yahoo.get("currency", "USD"),
            summary=f"Analysis failed: {exc}",
        )
        return {
            "prediction": pred,
            "warnings": [f"LLM analysis error: {exc}"],
            "steps": ["LLM analysis raised an error."],
        }

    # Backfill fields the model may have left blank.
    pred.ticker = pred.ticker or state.get("ticker", "")
    pred.company_name = pred.company_name or state.get("company_name", "")
    pred.as_of = pred.as_of or date.today().isoformat()
    if pred.current_price is None:
        pred.current_price = yahoo.get("current_price")
    pred.currency = yahoo.get("currency", pred.currency)

    return {"prediction": pred, "steps": ["Synthesized grounded prediction with the LLM."]}
