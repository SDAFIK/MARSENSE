from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MARSENSE_", env_file=ROOT / ".env", extra="ignore"
    )
    environment: Literal["demo", "production"] = "demo"
    database_url: str = f"sqlite:///{ROOT / 'data/runtime/marsense.db'}"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    api_token: str = ""
    auth_users_file: str = ""
    auth_required: bool = False
    read_only: bool = False
    model_path: str = ""
    slope_path: str = ""
    max_upload_bytes: int = 8 * 1024 * 1024

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.environment == "production" and not self.auth_users_file and not self.read_only:
            raise ValueError("Production mutations require an external authentication users file")
        if self.api_token and len(self.api_token) < 32:
            raise ValueError("Service read token must contain at least 32 characters")
        if "*" in self.cors_origins:
            raise ValueError("CORS must list explicit origins")
        return self
