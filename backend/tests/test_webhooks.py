from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import get_supabase
from app.main import app


@pytest.fixture
def client(settings):
    app.dependency_overrides[get_settings] = lambda: settings
    fake_db = MagicMock()
    app.dependency_overrides[get_supabase] = lambda: fake_db
    with TestClient(app) as c:
        yield c, fake_db
    app.dependency_overrides.clear()


def test_whatsapp_verification_success(client):
    c, _ = client
    response = c.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify-token",
            "hub.challenge": "1234",
        },
    )
    assert response.status_code == 200
    assert response.text == "1234"


def test_whatsapp_verification_failure(client):
    c, _ = client
    response = c.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "1234",
        },
    )
    assert response.status_code == 403


def test_whatsapp_webhook_skips_unregistered_tenant(client):
    c, fake_db = client
    fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "unknown-id"},
                            "contacts": [{"wa_id": "16475551234", "profile": {"name": "Test Lead"}}],
                            "messages": [{"from": "16475551234", "type": "text", "text": {"body": "hi"}}],
                        }
                    }
                ]
            }
        ]
    }
    response = c.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_telegram_webhook_unknown_bot_returns_404(client):
    c, fake_db = client
    fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []

    response = c.post(
        "/webhooks/telegram/UnknownBot",
        json={"message": {"chat": {"id": 42}, "from": {"first_name": "Test"}, "text": "hi"}},
    )
    assert response.status_code == 404
