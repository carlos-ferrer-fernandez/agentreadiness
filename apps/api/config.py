"""
Application configuration using pydantic-settings.

Loads from environment variables with sensible defaults for development.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "AgentReadiness API"
    app_version: str = "0.2.0"
    debug: bool = False

    # Stored as comma-separated string to avoid pydantic-settings JSON parsing.
    # Use the .cors_origins property to get the parsed list.
    allowed_origins: str = "http://localhost:3000,http://localhost:5173,https://agentreadiness-web.onrender.com"

    @property
    def cors_origins(self) -> list[str]:
        """Parse allowed_origins string into a list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

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
    openai_model: str = "gpt-5.4"  # Model for doc optimization (falls back to gpt-4o if unavailable)

    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    # Dynamic pricing (EUR)
    # Price = max(min_price, ceil(estimated_api_cost * margin_multiplier))
    # estimated_api_cost = base_cost + per_page_cost * page_count
    # Costs based on GPT-5.4: $2.50/1M input, $15.00/1M output
    # ~6K tokens in + ~3K tokens out per page = ~$0.06/page
    pricing_base_cost: float = 3.0        # Fixed overhead: assessment scan, server, Stripe fees
    pricing_per_page_cost: float = 0.08   # Per-page optimization ($0.06 actual + buffer)
    pricing_margin_multiplier: float = 3.0  # 3x margin on API costs
    pricing_min_eur: int = 89              # Minimum price ($99 USD / €89 EUR)
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
