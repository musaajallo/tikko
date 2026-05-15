"""Application settings loaded from the environment.

All env vars use the `TIKKO_` prefix (see `.env.example` at the repo root).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeployMode(StrEnum):
    """Single-deployable contract: same image runs on LAN or VPS.

    The mode only affects bindings, TLS, and defaults — never business logic.
    """

    LAN = "lan"
    CLOUD = "cloud"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TIKKO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deploy_mode: DeployMode = DeployMode.LAN
    api_base_url: str = "http://localhost:8000"

    database_url: str = "postgresql+psycopg://tikko:tikko@localhost:5432/tikko"

    jwt_secret: str = "change-me"
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 30

    default_poll_interval_sec: int = 60
    zk_connect_timeout_sec: int = 10

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    log_level: str = "info"

    # Resend email integration. When `resend_api_key` is empty, the email
    # module logs sends and skips the HTTP call — keeps dev environments
    # from accidentally emailing real users.
    resend_api_key: str = ""
    from_email: str = "no-reply@tikko.local"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv_origins(cls, value: object) -> object:
        """Accept either a JSON array or a plain comma-separated string from env."""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                return value  # leave for pydantic's JSON parser
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    def validate_for_deployment(self) -> None:
        """Raise if the current settings are unsafe for the chosen deploy_mode.

        LAN mode is permissive on purpose — that's the local-network deploy where
        the defaults are fine. Cloud mode is where misconfiguration becomes a
        production incident, so we surface every problem we know about in one
        combined error rather than fail-fast on the first.
        """
        if self.deploy_mode != DeployMode.CLOUD:
            return

        problems: list[str] = []
        if self.jwt_secret == "change-me":
            problems.append(
                "TIKKO_JWT_SECRET must be set to a real value in cloud mode "
                "(generate with `openssl rand -hex 32`); the default 'change-me' "
                "is rejected."
            )
        if "sqlite" in self.database_url.lower():
            problems.append(
                "TIKKO_DATABASE_URL must point at Postgres in cloud mode; "
                "SQLite is only supported for local development."
            )
        if self.cors_origins == ["http://localhost:3000"]:
            problems.append(
                "TIKKO_CORS_ORIGINS must be set explicitly in cloud mode "
                "(default localhost-only value is rejected)."
            )

        if problems:
            joined = "\n  - ".join(problems)
            raise ValueError(
                f"invalid configuration for deploy_mode=cloud:\n  - {joined}"
            )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return a cached Settings instance. Tests may override by patching this."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
