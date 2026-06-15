"""Pydantic schemas shared across the API and the agent graph."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Recommendation = Literal["STRONG_BUY", "BUY", "ACCUMULATE", "HOLD", "WAIT", "SELL", "AVOID"]


class PredictRequest(BaseModel):
    query: str = Field(..., description="Stock ticker symbol or company name")


class Source(BaseModel):
    title: str = ""
    url: str = ""
    publisher: str = ""
    snippet: str = ""
    kind: Literal["yahoo", "web", "company", "filing"] = "web"


class PriceRange(BaseModel):
    low: float | None = None
    high: float | None = None
    currency: str = "USD"


class TradePlan(BaseModel):
    """An entry or exit recommendation with price + time windows."""

    price_range: PriceRange = Field(default_factory=PriceRange)
    time_window: str = Field("", description="Human readable time window, e.g. 'next 2-4 weeks'")
    start_date: str | None = None
    end_date: str | None = None
    rationale: str = ""


class Prediction(BaseModel):
    ticker: str = ""
    company_name: str = ""
    as_of: str = ""
    current_price: float | None = None
    currency: str = "USD"
    recommendation: Recommendation = "HOLD"
    confidence: float = Field(0.0, ge=0.0, le=1.0)

    entry: TradePlan = Field(default_factory=TradePlan)
    exit: TradePlan = Field(default_factory=TradePlan)

    strong_reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    thought_process: list[str] = Field(default_factory=list)

    summary: str = ""
    disclaimer: str = (
        "This is an AI-generated analysis for educational purposes only and is "
        "not financial advice. Markets are risky; do your own research."
    )


class PredictResponse(BaseModel):
    prediction: Prediction
    sources: list[Source] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
