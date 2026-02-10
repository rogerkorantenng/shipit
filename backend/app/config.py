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

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
