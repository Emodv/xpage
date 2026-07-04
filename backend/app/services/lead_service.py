"""Core orchestration: inbound message -> lead/message rows -> AI reply -> outbound send.

This is the single place that ties together the CRM (Supabase), the AI
responder (GPT-4o), calendar availability/booking, and the outbound channel
clients. Both webhook handlers (WhatsApp, Telegram) call into this.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from supabase import Client

from app.config import Settings
from app.models import InboundMessage
from app.services import calendar_service
from app.services.ai_responder import get_ai_response
from app.services.telegram_client import send_telegram_message
from app.services.tenant_service import ResolvedTenant
from app.services.whatsapp_client import send_whatsapp_message

logger = logging.getLogger(__name__)


def _get_or_create_lead(db: Client, tenant: ResolvedTenant, inbound: InboundMessage) -> dict:
    existing = (
        db.table("leads")
        .select("*")
        .eq("tenant_id", tenant.id)
        .eq("channel", inbound.channel.value)
        .eq("external_id", inbound.external_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        return existing.data[0]

    created = (
        db.table("leads")
        .insert(
            {
                "tenant_id": tenant.id,
                "channel": inbound.channel.value,
                "external_id": inbound.external_id,
                "display_name": inbound.display_name,
                "phone": inbound.phone,
                "status": "new",
            }
        )
        .execute()
    )
    return created.data[0]


def _store_message(db: Client, tenant_id: str, lead_id: str, direction: str, channel: str, body: str, ai_generated: bool) -> None:
    db.table("messages").insert(
        {
            "tenant_id": tenant_id,
            "lead_id": lead_id,
            "direction": direction,
            "channel": channel,
            "body": body,
            "ai_generated": ai_generated,
        }
    ).execute()


def _conversation_history(db: Client, lead_id: str) -> list[dict]:
    result = (
        db.table("messages")
        .select("direction, body")
        .eq("lead_id", lead_id)
        .order("created_at")
        .execute()
    )
    return [
        {"role": "user" if m["direction"] == "in" else "assistant", "content": m["body"]}
        for m in result.data
    ]


async def handle_inbound_message(db: Client, settings: Settings, tenant: ResolvedTenant, inbound: InboundMessage) -> None:
    lead = _get_or_create_lead(db, tenant, inbound)
    _store_message(db, tenant.id, lead["id"], "in", inbound.channel.value, inbound.text, ai_generated=False)

    if not lead.get("ai_enabled", True):
        logger.info("AI disabled for lead %s (human took over); skipping auto-reply", lead["id"])
        return

    open_slots = []
    if tenant.config.google_calendar_id and settings.google_calendar_credentials_json:
        try:
            open_slots = calendar_service.find_open_slots(settings, tenant.config)
        except Exception:
            logger.exception("Failed to fetch calendar availability for tenant %s", tenant.slug)

    history = _conversation_history(db, lead["id"])
    result = await get_ai_response(settings, tenant.config, history, open_slots)

    updates = {
        "language": result.language,
        "status": result.lead_status.value,
    }
    if result.service_needed:
        updates["service_needed"] = result.service_needed
    if result.budget:
        updates["budget"] = result.budget
    if result.timeline:
        updates["timeline"] = result.timeline
    db.table("leads").update(updates).eq("id", lead["id"]).execute()

    if result.ready_to_book and result.chosen_slot_index and open_slots:
        idx = result.chosen_slot_index - 1
        if 0 <= idx < len(open_slots):
            chosen = open_slots[idx]
            try:
                event_id = calendar_service.book_appointment(
                    settings,
                    tenant.config,
                    chosen,
                    summary=f"{tenant.config.business_name}: {lead.get('display_name') or lead['external_id']}",
                    description=f"Service: {result.service_needed or lead.get('service_needed', '')}",
                )
                db.table("appointments").insert(
                    {
                        "tenant_id": tenant.id,
                        "lead_id": lead["id"],
                        "calendar_event_id": event_id,
                        "start_time": chosen.isoformat(),
                        "end_time": (
                            chosen + timedelta(minutes=tenant.config.appointment_duration_minutes)
                        ).isoformat(),
                        "status": "scheduled",
                    }
                ).execute()
                db.table("leads").update({"status": "booked"}).eq("id", lead["id"]).execute()
            except Exception:
                logger.exception("Failed to create calendar booking for lead %s", lead["id"])

    _store_message(db, tenant.id, lead["id"], "out", inbound.channel.value, result.reply_text, ai_generated=True)

    if inbound.channel.value == "whatsapp":
        await send_whatsapp_message(
            settings, tenant.config.whatsapp_phone_number_id, inbound.external_id, result.reply_text
        )
    else:
        await send_telegram_message(settings, inbound.external_id, result.reply_text)
