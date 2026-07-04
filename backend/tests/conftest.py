import pytest

from app.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="test-service-role-key",
        OPENAI_API_KEY="test-openai-key",
        WHATSAPP_ACCESS_TOKEN="test-whatsapp-token",
        WHATSAPP_VERIFY_TOKEN="test-verify-token",
        TELEGRAM_BOT_TOKEN="test-telegram-token",
    )
