"""Lead feed + manual override for the admin dashboard.

The dashboard reads leads/messages directly from Supabase (RLS-scoped to the
signed-in owner's tenant) for the live feed. These endpoints cover the one
action the dashboard can't do safely client-side: sending an outbound
message through the actual WhatsApp/Telegram channel, which requires the
backend's provider credentials.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.config import Settings, get_settings
from app.database import get_supabase
from app.models import ManualReplyRequest
from app.services.telegram_client import send_telegram_message
from app.services.tenant_service import resolve_tenant_by_id
from app.services.whatsapp_client import send_whatsapp_message

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("/reply")
async def send_manual_reply(
    body: ManualReplyRequest,
    settings: Settings = Depends(get_settings),
    db: Client = Depends(get_supabase),
):
    """Send a human-authored reply and switch the lead off autopilot."""
    lead_result = db.table("leads").select("*").eq("id", body.lead_id).limit(1).execute()
    if not lead_result.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead = lead_result.data[0]

    tenant = resolve_tenant_by_id(db, lead["tenant_id"])
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if lead["channel"] == "whatsapp":
        await send_whatsapp_message(settings, tenant.config.whatsapp_phone_number_id, lead["external_id"], body.text)
    else:
        await send_telegram_message(settings, lead["external_id"], body.text)

    db.table("messages").insert(
        {
            "tenant_id": lead["tenant_id"],
            "lead_id": lead["id"],
            "direction": "out",
            "channel": lead["channel"],
            "body": body.text,
            "ai_generated": False,
        }
    ).execute()

    # A human just took over — stop the AI from auto-replying to this lead going forward.
    db.table("leads").update({"ai_enabled": False}).eq("id", lead["id"]).execute()

    return {"status": "sent"}


@router.post("/{lead_id}/resume-ai")
async def resume_ai(lead_id: str, db: Client = Depends(get_supabase)):
    """Hand the conversation back to the AI responder."""
    db.table("leads").update({"ai_enabled": True}).eq("id", lead_id).execute()
    return {"status": "ai_resumed"}
