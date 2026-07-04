"""Google Calendar integration: find open slots and book confirmed appointments.

Auth uses a single service account (credentials JSON in
GOOGLE_CALENDAR_CREDENTIALS_JSON) that has been granted "Make changes to
events" access on each tenant's calendar. This keeps onboarding config-only:
share the calendar with the service account email, drop the calendar ID in
the tenant's YAML, done.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build
from zoneinfo import ZoneInfo

from app.config import Settings, TenantConfig

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_calendar_client(settings: Settings):
    info = json.loads(settings.google_calendar_credentials_json)
    credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def _business_hours_for_day(tenant: TenantConfig, day: datetime) -> tuple[str, str] | None:
    weekday_key = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][day.weekday()]
    hours = tenant.business_hours.get(weekday_key)
    if not hours:
        return None
    return hours[0], hours[1]


def find_open_slots(
    settings: Settings,
    tenant: TenantConfig,
    count: int = 3,
    days_ahead: int = 7,
) -> list[datetime]:
    """Return up to `count` open appointment start times within business hours,
    skipping anything that overlaps an existing event on the tenant's calendar."""
    tz = ZoneInfo(tenant.timezone)
    now = datetime.now(tz)
    client = _get_calendar_client(settings)
    duration = timedelta(minutes=tenant.appointment_duration_minutes)

    window_start = now
    window_end = now + timedelta(days=days_ahead)

    freebusy = client.freebusy().query(
        body={
            "timeMin": window_start.isoformat(),
            "timeMax": window_end.isoformat(),
            "timeZone": tenant.timezone,
            "items": [{"id": tenant.google_calendar_id}],
        }
    ).execute()
    busy_periods = freebusy["calendars"][tenant.google_calendar_id]["busy"]
    busy_ranges = [
        (datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"]))
        for b in busy_periods
    ]

    slots: list[datetime] = []
    day_cursor = now.date()
    for _ in range(days_ahead + 1):
        day_start_dt = datetime.combine(day_cursor, datetime.min.time(), tzinfo=tz)
        hours = _business_hours_for_day(tenant, day_start_dt)
        if hours:
            open_time, close_time = hours
            oh, om = map(int, open_time.split(":"))
            ch, cm = map(int, close_time.split(":"))
            slot_time = day_start_dt.replace(hour=oh, minute=om)
            day_close = day_start_dt.replace(hour=ch, minute=cm)
            while slot_time + duration <= day_close and len(slots) < count:
                if slot_time > now and not _overlaps(slot_time, slot_time + duration, busy_ranges):
                    slots.append(slot_time)
                slot_time += duration
        day_cursor += timedelta(days=1)
        if len(slots) >= count:
            break

    return slots[:count]


def _overlaps(start: datetime, end: datetime, busy_ranges: list[tuple[datetime, datetime]]) -> bool:
    return any(start < b_end and end > b_start for b_start, b_end in busy_ranges)


def book_appointment(
    settings: Settings,
    tenant: TenantConfig,
    start_time: datetime,
    summary: str,
    description: str = "",
) -> str:
    """Create the calendar event and return its event ID."""
    client = _get_calendar_client(settings)
    duration = timedelta(minutes=tenant.appointment_duration_minutes)
    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_time.isoformat(), "timeZone": tenant.timezone},
        "end": {"dateTime": (start_time + duration).isoformat(), "timeZone": tenant.timezone},
    }
    created = client.events().insert(calendarId=tenant.google_calendar_id, body=event).execute()
    return created["id"]
