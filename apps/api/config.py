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
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

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
    stripe_starter_price_id: str = "price_starter"
    stripe_growth_price_id: str = "price_growth"

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
