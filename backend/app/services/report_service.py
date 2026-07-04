"""Weekly owner report: leads received, leads booked, no-shows, revenue attributed.

Generates one row in `weekly_reports` per tenant per period and sends the
summary by email (SMTP) and WhatsApp. Intended to be triggered by an
external scheduler (cron) hitting POST /reports/weekly/{tenant_id} weekly.
"""
from __future__ import annotations

import smtplib
from datetime import date, timedelta
from email.mime.text import MIMEText

from supabase import Client

from app.config import Settings
from app.services.tenant_service import ResolvedTenant
from app.services.whatsapp_client import send_whatsapp_message


def _week_bounds(today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    period_end = today
    period_start = today - timedelta(days=7)
    return period_start, period_end


def _build_summary_text(tenant: ResolvedTenant, stats: dict, period_start: date, period_end: date) -> str:
    return (
        f"Weekly report for {tenant.config.business_name}\n"
        f"{period_start.isoformat()} to {period_end.isoformat()}\n\n"
        f"Leads received: {stats['leads_received']}\n"
        f"Leads booked: {stats['leads_booked']}\n"
        f"No-shows: {stats['no_shows']}\n"
        f"Revenue attributed: ${stats['revenue_attributed']:.2f}"
    )


def _gather_stats(db: Client, tenant_id: str, period_start: date, period_end: date) -> dict:
    leads = (
        db.table("leads")
        .select("id", count="exact")
        .eq("tenant_id", tenant_id)
        .gte("created_at", period_start.isoformat())
        .lt("created_at", period_end.isoformat())
        .execute()
    )
    booked_leads = (
        db.table("leads")
        .select("id", count="exact")
        .eq("tenant_id", tenant_id)
        .eq("status", "booked")
        .gte("created_at", period_start.isoformat())
        .lt("created_at", period_end.isoformat())
        .execute()
    )
    appointments = (
        db.table("appointments")
        .select("status, revenue_amount")
        .eq("tenant_id", tenant_id)
        .gte("start_time", period_start.isoformat())
        .lt("start_time", period_end.isoformat())
        .execute()
    )
    no_shows = sum(1 for a in appointments.data if a["status"] == "no_show")
    revenue = sum(float(a["revenue_amount"] or 0) for a in appointments.data if a["status"] == "completed")

    return {
        "leads_received": leads.count or 0,
        "leads_booked": booked_leads.count or 0,
        "no_shows": no_shows,
        "revenue_attributed": revenue,
    }


def _send_email(settings: Settings, to_email: str, subject: str, body: str) -> None:
    if not settings.smtp_host or not to_email:
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user
    msg["To"] = to_email

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_user, [to_email], msg.as_string())


async def generate_and_send_weekly_report(db: Client, settings: Settings, tenant: ResolvedTenant) -> dict:
    period_start, period_end = _week_bounds()
    stats = _gather_stats(db, tenant.id, period_start, period_end)
    summary = _build_summary_text(tenant, stats, period_start, period_end)

    report = (
        db.table("weekly_reports")
        .upsert(
            {
                "tenant_id": tenant.id,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                **stats,
                "summary_text": summary,
            },
            on_conflict="tenant_id,period_start,period_end",
        )
        .execute()
    )

    if tenant.config.owner_email:
        _send_email(settings, tenant.config.owner_email, f"Weekly report: {tenant.config.business_name}", summary)

    if tenant.config.owner_whatsapp_number and tenant.config.whatsapp_phone_number_id:
        await send_whatsapp_message(
            settings, tenant.config.whatsapp_phone_number_id, tenant.config.owner_whatsapp_number, summary
        )

    db.table("weekly_reports").update({"sent_at": "now()"}).eq("tenant_id", tenant.id).eq(
        "period_start", period_start.isoformat()
    ).eq("period_end", period_end.isoformat()).execute()

    return report.data[0] if report.data else {"summary_text": summary, **stats}
