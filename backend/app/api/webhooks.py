"""Inbound webhook intake for WhatsApp Business API and Telegram Bot API.

Each handler parses the provider-specific payload into a channel-agnostic
`InboundMessage`, resolves the owning tenant purely from config (phone
number ID / bot username), and hands off to lead_service for the rest of
the pipeline. New tenants "just work" here as long as their identifiers are
registered in `tenants` + `tenants/<slug>.yaml` — no code changes.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from supabase import Client

from app.config import Settings, get_settings
from app.database import get_supabase
from app.models import Channel, InboundMessage
from app.services import lead_service
from app.services.tenant_service import resolve_tenant_by_telegram_bot, resolve_tenant_by_whatsapp_phone_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
    settings: Settings = Depends(get_settings),
):
    """Meta's one-time webhook verification handshake."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    settings: Settings = Depends(get_settings),
    db: Client = Depends(get_supabase),
):
    payload = await request.json()

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            if not phone_number_id:
                continue

            tenant = resolve_tenant_by_whatsapp_phone_id(db, phone_number_id)
            if not tenant:
                logger.warning("No tenant registered for WhatsApp phone_number_id=%s", phone_number_id)
                continue

            contacts = {c["wa_id"]: c for c in value.get("contacts", [])}
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                wa_id = message["from"]
                contact = contacts.get(wa_id, {})
                inbound = InboundMessage(
                    tenant_slug=tenant.slug,
                    channel=Channel.whatsapp,
                    external_id=wa_id,
                    display_name=contact.get("profile", {}).get("name"),
                    phone=wa_id,
                    text=message["text"]["body"],
                )
                await lead_service.handle_inbound_message(db, settings, tenant, inbound)

    # WhatsApp requires a fast 200 OK regardless of processing outcome.
    return {"status": "ok"}


@router.post("/telegram/{bot_username}")
async def telegram_webhook(
    bot_username: str,
    request: Request,
    settings: Settings = Depends(get_settings),
    db: Client = Depends(get_supabase),
):
    """Telegram sends updates to a per-bot URL you set once via setWebhook;
    `bot_username` in the path lets one FastAPI deployment serve many tenants' bots."""
    payload = await request.json()
    message = payload.get("message")
    if not message or "text" not in message:
        return {"status": "ignored"}

    tenant = resolve_tenant_by_telegram_bot(db, bot_username)
    if not tenant:
        logger.warning("No tenant registered for Telegram bot=%s", bot_username)
        raise HTTPException(status_code=404, detail="Unknown tenant")

    chat = message["chat"]
    from_user = message.get("from", {})
    display_name = " ".join(filter(None, [from_user.get("first_name"), from_user.get("last_name")])) or None

    inbound = InboundMessage(
        tenant_slug=tenant.slug,
        channel=Channel.telegram,
        external_id=str(chat["id"]),
        display_name=display_name,
        phone=None,
        text=message["text"],
    )
    await lead_service.handle_inbound_message(db, settings, tenant, inbound)
    return {"status": "ok"}
