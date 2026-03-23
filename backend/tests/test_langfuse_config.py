import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import Settings


def test_langfuse_settings_defaults(monkeypatch):
    monkeypatch.delenv("LANGFUSE_ENABLED", raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_ENV", raising=False)
    monkeypatch.delenv("LANGFUSE_SAMPLE_RATE_DEV", raising=False)
    monkeypatch.delenv("LANGFUSE_SAMPLE_RATE_STAGING", raising=False)
    monkeypatch.delenv("LANGFUSE_SAMPLE_RATE_PROD", raising=False)

    settings = Settings(_env_file=None)

    assert settings.langfuse_enabled is False
    assert settings.langfuse_host == ""
    assert settings.langfuse_public_key == ""
    assert settings.langfuse_secret_key == ""
    assert settings.langfuse_env == "dev"
    assert settings.langfuse_sample_rate_dev == 1.0
    assert settings.langfuse_sample_rate_staging == 1.0
    assert settings.langfuse_sample_rate_prod == 0.2


def test_langfuse_settings_env_overrides(monkeypatch):
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_ENV", "prod")
    monkeypatch.setenv("LANGFUSE_SAMPLE_RATE_DEV", "0.5")
    monkeypatch.setenv("LANGFUSE_SAMPLE_RATE_STAGING", "0.6")
    monkeypatch.setenv("LANGFUSE_SAMPLE_RATE_PROD", "0.75")

    settings = Settings(_env_file=None)

    assert settings.langfuse_enabled is True
    assert settings.langfuse_host == "https://cloud.langfuse.com"
    assert settings.langfuse_public_key == "pk-test"
    assert settings.langfuse_secret_key == "sk-test"
    assert settings.langfuse_env == "prod"
    assert settings.langfuse_sample_rate_dev == 0.5
    assert settings.langfuse_sample_rate_staging == 0.6
    assert settings.langfuse_sample_rate_prod == 0.75
