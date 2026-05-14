"""F31 — `Settings.validate_for_deployment` enforces cloud-mode safety at boot."""

from __future__ import annotations

import pytest

from tikko.settings import DeployMode, Settings


def _cloud_settings(**overrides: object) -> Settings:
    """Build a Settings instance for cloud mode without reading env/.env."""
    base: dict[str, object] = {
        "deploy_mode": DeployMode.CLOUD,
        "jwt_secret": "openssl-rand-hex-32-equivalent-very-long-secret",
        "database_url": "postgresql+psycopg://u:p@db.example.com:5432/tikko",
        "cors_origins": ["https://tikko.example.com"],
    }
    base.update(overrides)
    return Settings.model_validate(base)


def test_lan_defaults_validate_cleanly() -> None:
    """LAN mode is the permissive default — none of the rules apply."""
    settings = Settings.model_validate({})  # defaults
    # Should not raise.
    settings.validate_for_deployment()


def test_lan_mode_allows_default_jwt_secret() -> None:
    settings = Settings.model_validate({"jwt_secret": "change-me"})
    settings.validate_for_deployment()


def test_cloud_mode_rejects_default_jwt_secret() -> None:
    settings = _cloud_settings(jwt_secret="change-me")
    with pytest.raises(ValueError, match="TIKKO_JWT_SECRET"):
        settings.validate_for_deployment()


def test_cloud_mode_rejects_sqlite_database_url() -> None:
    settings = _cloud_settings(database_url="sqlite+aiosqlite:///./tikko-dev.db")
    with pytest.raises(ValueError, match="TIKKO_DATABASE_URL"):
        settings.validate_for_deployment()


def test_cloud_mode_rejects_default_localhost_cors() -> None:
    settings = _cloud_settings(cors_origins=["http://localhost:3000"])
    with pytest.raises(ValueError, match="TIKKO_CORS_ORIGINS"):
        settings.validate_for_deployment()


def test_cloud_mode_with_all_safe_values_validates_cleanly() -> None:
    _cloud_settings().validate_for_deployment()


def test_cloud_mode_reports_every_problem_in_one_error() -> None:
    """Operators get one clear message listing everything wrong, not one-at-a-time."""
    settings = _cloud_settings(
        jwt_secret="change-me",
        database_url="sqlite+aiosqlite:///./tikko-dev.db",
        cors_origins=["http://localhost:3000"],
    )
    with pytest.raises(ValueError) as exc:
        settings.validate_for_deployment()
    msg = str(exc.value)
    assert "TIKKO_JWT_SECRET" in msg
    assert "TIKKO_DATABASE_URL" in msg
    assert "TIKKO_CORS_ORIGINS" in msg
