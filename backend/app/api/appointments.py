"""Appointment status updates (completed / no-show + revenue attribution).

Reads are done directly from Supabase by the dashboard (RLS-scoped); this
endpoint exists because marking outcomes feeds the weekly report numbers
and is simplest to keep server-side alongside validation.
"""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from app.database import get_supabase

router = APIRouter(prefix="/appointments", tags=["appointments"])


class AppointmentOutcomeUpdate(BaseModel):
    status: Literal["completed", "no_show", "cancelled"]
    revenue_amount: Optional[float] = None


@router.patch("/{appointment_id}/outcome")
async def update_appointment_outcome(
    appointment_id: str,
    body: AppointmentOutcomeUpdate,
    db: Client = Depends(get_supabase),
):
    existing = db.table("appointments").select("id").eq("id", appointment_id).limit(1).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Appointment not found")

    updates: dict = {"status": body.status}
    if body.revenue_amount is not None:
        updates["revenue_amount"] = body.revenue_amount

    result = db.table("appointments").update(updates).eq("id", appointment_id).execute()
    return result.data[0]
