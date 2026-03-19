"""
Application configuration using pydantic-settings.

Loads from environment variables with sensible defaults for development.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import json


class Settings(BaseSettings):
    # App
    app_name: str = "AgentReadiness API"
    app_version: str = "0.2.0"
    debug: bool = False
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://agentreadiness-web.onrender.com",
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Accept both JSON list and comma-separated string."""
        if isinstance(v, str):
            v = v.strip()
            # Try JSON first (e.g. '["http://...", "http://..."]')
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fall back to comma-separated (e.g. "http://...,http://...")
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentreadiness"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7  # 1 week
    github_client_id: str = ""
    github_client_secret: str = ""

    # OpenAI
    openai_api_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    # Dynamic pricing (EUR)
    # Price = max(min_price, ceil(estimated_api_cost * margin_multiplier))
    # estimated_api_cost = base_cost + per_page_cost * page_count
    pricing_base_cost: float = 5.0        # Fixed overhead: query gen, scoring, recommendations
    pricing_per_page_cost: float = 0.40   # Per-page: embedding, RAG simulation, evaluation
    pricing_margin_multiplier: float = 3.0  # 3x margin on API costs
    pricing_min_eur: int = 49              # Minimum price (entry point, appealing)
    pricing_max_eur: int = 499             # Cap for very large docs

    # Crawler
    max_crawl_pages: int = 100
    crawl_delay_seconds: float = 1.0

    # Rate limiting
    rate_limit_per_minute: int = 60

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
