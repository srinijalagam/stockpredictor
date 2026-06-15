"""Shared graph state."""
from __future__ import annotations

from typing import Annotated, Any, TypedDict

from ..models import Prediction, Source


def _extend(left: list, right: list) -> list:
    return (left or []) + (right or [])


class AgentState(TypedDict, total=False):
    query: str

    ticker: str
    company_name: str
    website: str

    yahoo: dict[str, Any]
    company_text: str

    sources: Annotated[list[Source], _extend]
    steps: Annotated[list[str], _extend]
    warnings: Annotated[list[str], _extend]

    prediction: Prediction
