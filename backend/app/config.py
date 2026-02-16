from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "ShipIt"
    debug: bool = True

    # Database
    database_url: str = "sqlite+aiosqlite:///./shipit.db"

    # Gradient AI
    gradient_api_key: str = ""
    gradient_workspace_id: str = ""
    gradient_agent_endpoint: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Agent Fleet
    agents_enabled: bool = True
    agent_analytics_schedule_hours: int = 24
    agent_review_sla_hours: int = 24

    # Slack
    slack_bot_token: str = ""
    slack_default_channel: str = ""

    # Datadog
    datadog_api_key: str = ""
    datadog_app_key: str = ""

    # Sentry
    sentry_api_token: str = ""

    # Figma
    figma_webhook_secret: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
