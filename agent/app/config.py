"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str | None = None

    # Search
    tavily_api_key: str = ""
    max_search_results: int = 6

    # Trusted sources (comma separated string in env)
    trusted_domains: str = (
        "reuters.com,bloomberg.com,wsj.com,ft.com,cnbc.com,marketwatch.com,"
        "finance.yahoo.com,sec.gov,nasdaq.com,morningstar.com,fool.com,"
        "seekingalpha.com,barrons.com,investors.com,forbes.com"
    )

    # HTTP
    http_timeout: int = 15
    log_level: str = "info"

    @property
    def trusted_domain_list(self) -> list[str]:
        return [d.strip().lower() for d in self.trusted_domains.split(",") if d.strip()]

    @property
    def has_llm(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
