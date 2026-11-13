from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MARSENSE_", env_file=ROOT / ".env", extra="ignore"
    )
    environment: Literal["demo", "production", "showcase"] = "demo"
    database_url: str = f"sqlite:///{ROOT / 'data/runtime/marsense.db'}"
    runtime_dir: Path = ROOT / "data/runtime"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    api_token: str = ""
    auth_users_file: str = ""
    auth_required: bool = False
    read_only: bool = False
    model_path: str = ""
    slope_path: str = ""
    max_upload_bytes: int = 8 * 1024 * 1024
    cloud_database_url: SecretStr = SecretStr("")
    cloud_supabase_url: str = ""
    cloud_publishable_key: SecretStr = SecretStr("")
    cloud_storage_key: SecretStr = SecretStr("")
    cloud_storage_bucket: str = "marsense-private"
    cloud_public_origin: str = ""

    @property
    def cloud_enabled(self) -> bool:
        return bool(self.cloud_database_url.get_secret_value())

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.environment == "showcase":
            if not self.auth_users_file or self.read_only or self.api_token:
                raise ValueError(
                    "Showcase requires dedicated identities and writable authenticated access"
                )
            if not self.database_url.endswith("/showcase.db"):
                raise ValueError("Showcase requires a dedicated showcase.db database")
        if self.cloud_enabled:
            if self.environment != "production" or self.read_only or self.model_path:
                raise ValueError("Cloud runtime requires production, writable data and CPU CV mode")
            if not all((self.cloud_supabase_url, self.cloud_publishable_key.get_secret_value(),
                        self.cloud_storage_key.get_secret_value(), self.cloud_public_origin)):
                raise ValueError("Cloud runtime requires database, identity, storage and public origin")
            for value in (self.cloud_supabase_url, self.cloud_public_origin):
                url = urlsplit(value)
                if url.scheme != "https" or not url.hostname or url.path not in ("", "/") or (
                    url.query or url.fragment or url.username or url.password
                ):
                    raise ValueError("Cloud endpoints must be exact HTTPS origins")
            if self.cloud_public_origin.rstrip("/") not in self.cors_origins:
                raise ValueError("Cloud public origin must appear in the explicit CORS allowlist")
            if self.cloud_storage_bucket != "marsense-private":
                raise ValueError("Cloud storage must use the dedicated private MARSENSE bucket")
        if (self.environment == "production" and not self.auth_users_file
                and not self.read_only and not self.cloud_enabled):
            raise ValueError("Production mutations require an external authentication users file")
        if self.api_token and len(self.api_token) < 32:
            raise ValueError("Service read token must contain at least 32 characters")
        if "*" in self.cors_origins:
            raise ValueError("CORS must list explicit origins")
        return self
