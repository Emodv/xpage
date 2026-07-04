import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.config import TenantConfig
from app.services.ai_responder import get_ai_response

TENANT_DATA = {
    "slug": "mortgage-broker-demo",
    "business_name": "Parsa Mortgages",
    "timezone": "America/Toronto",
    "whatsapp_phone_number_id": "123",
    "google_calendar_id": "cal-id",
    "business_hours": {"mon": ["09:00", "17:00"]},
    "appointment_duration_minutes": 30,
    "services": [{"name": "Mortgage renewal", "name_fa": "تمدید وام"}],
    "ai_persona": "You are the assistant for Parsa Mortgages.",
}


def _fake_completion(tool_arguments: dict):
    tool_call = type(
        "ToolCall",
        (),
        {"function": type("Function", (), {"arguments": json.dumps(tool_arguments)})()},
    )()
    message = type("Message", (), {"tool_calls": [tool_call]})()
    choice = type("Choice", (), {"message": message})()
    return type("Completion", (), {"choices": [choice]})()


@pytest.mark.asyncio
async def test_get_ai_response_parses_structured_output(settings):
    tenant = TenantConfig(TENANT_DATA)
    slots = [datetime.now() + timedelta(days=1)]

    expected_args = {
        "reply_text": "سلام! چه خدمتی نیاز دارید؟",
        "language": "fa",
        "service_needed": "Mortgage renewal",
        "budget": None,
        "timeline": "1 month",
        "ready_to_book": False,
        "chosen_slot_index": None,
        "lead_status": "new",
    }

    with patch("app.services.ai_responder.AsyncOpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_client.chat.completions.create = AsyncMock(return_value=_fake_completion(expected_args))

        result = await get_ai_response(
            settings,
            tenant,
            [{"role": "user", "content": "سلام"}],
            slots,
        )

    assert result.reply_text == expected_args["reply_text"]
    assert result.language == "fa"
    assert result.service_needed == "Mortgage renewal"
    assert result.lead_status.value == "new"
    mock_client.chat.completions.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_ai_response_marks_booked_on_slot_choice(settings):
    tenant = TenantConfig(TENANT_DATA)
    slots = [datetime.now() + timedelta(days=1), datetime.now() + timedelta(days=2)]

    expected_args = {
        "reply_text": "Great, you're booked for slot 2.",
        "language": "en",
        "ready_to_book": True,
        "chosen_slot_index": 2,
        "lead_status": "booked",
    }

    with patch("app.services.ai_responder.AsyncOpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_client.chat.completions.create = AsyncMock(return_value=_fake_completion(expected_args))

        result = await get_ai_response(
            settings,
            tenant,
            [{"role": "user", "content": "I'll take the second one"}],
            slots,
        )

    assert result.chosen_slot_index == 2
    assert result.lead_status.value == "booked"
