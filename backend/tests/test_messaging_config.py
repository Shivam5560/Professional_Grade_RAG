import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import Settings
from app.services import messaging


def test_rabbitmq_url_can_be_overridden_from_environment(monkeypatch):
    expected_url = "amqp://nexus:test-password@nexus-rabbitmq:5672/"
    monkeypatch.setenv("RABBITMQ_URL", expected_url)

    configured = Settings(_env_file=None)

    assert configured.rabbitmq_url == expected_url


@pytest.mark.asyncio
async def test_connection_uses_configured_rabbitmq_url(monkeypatch):
    expected_url = "amqp://nexus:test-password@nexus-rabbitmq:5672/"
    observed = {}
    connection = object()

    async def fake_connect_robust(url):
        observed["url"] = url
        return connection

    monkeypatch.setattr(
        messaging,
        "settings",
        SimpleNamespace(rabbitmq_url=expected_url),
        raising=False,
    )
    monkeypatch.setattr(messaging.aio_pika, "connect_robust", fake_connect_robust)

    result = await messaging.get_rabbitmq_connection()

    assert observed["url"] == expected_url
    assert result is connection
