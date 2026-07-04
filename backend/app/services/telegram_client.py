"""Outbound messaging via the Telegram Bot API."""
from __future__ import annotations

import httpx

from app.config import Settings


async def send_telegram_message(settings: Settings, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
