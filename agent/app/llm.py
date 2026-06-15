"""LLM provider factory (OpenAI-compatible)."""
from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

from .config import get_settings


def get_llm(temperature: float = 0.2) -> ChatOpenAI:
    """Return a configured chat model.

    Works with OpenAI or any OpenAI-compatible endpoint via OPENAI_BASE_URL.
    """
    settings = get_settings()

    base_url = (settings.openai_base_url or "").strip()
    # The OpenAI SDK auto-reads OPENAI_BASE_URL from the environment even when
    # we pass base_url=None. An empty/whitespace value yields a schemeless URL
    # and breaks every request, so scrub it when not a real endpoint.
    if not base_url and not os.environ.get("OPENAI_BASE_URL", "").strip():
        os.environ.pop("OPENAI_BASE_URL", None)

    kwargs: dict = {
        "model": settings.openai_model,
        "temperature": temperature,
        "api_key": settings.openai_api_key,
        "timeout": 60,
        "max_retries": 2,
    }
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)
