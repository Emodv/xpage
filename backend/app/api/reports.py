"""Weekly report trigger endpoint — call this from an external scheduler
(cron job, GitHub Actions schedule, Supabase pg_cron via `net.http_post`)
once per tenant per week."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from supabase import Client

from app.config import Settings, get_settings
from app.database import get_supabase
from app.services.report_service import generate_and_send_weekly_report
from app.services.tenant_service import resolve_tenant_by_id

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/weekly/{tenant_id}")
async def trigger_weekly_report(
    tenant_id: str,
    x_cron_secret: str = Header(default=""),
    settings: Settings = Depends(get_settings),
    db: Client = Depends(get_supabase),
):
    if settings.report_cron_secret and x_cron_secret != settings.report_cron_secret:
        raise HTTPException(status_code=403, detail="Invalid cron secret")

    tenant = resolve_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    report = await generate_and_send_weekly_report(db, settings, tenant)
    return {"status": "sent", "report": report}
