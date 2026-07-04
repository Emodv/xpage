"""Outbound messaging via the WhatsApp Cloud API (Meta)."""
from __future__ import annotations

import httpx

from app.config import Settings


async def send_whatsapp_message(settings: Settings, phone_number_id: str, to: str, text: str) -> None:
    url = f"https://graph.facebook.com/{settings.whatsapp_api_version}/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
