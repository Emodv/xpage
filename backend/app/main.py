"""FastAPI entrypoint for the multi-tenant AI lead response and booking system."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import appointments, leads, reports, webhooks

app = FastAPI(title="AI Lead Response & Booking System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the dashboard's origin(s) in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks.router)
app.include_router(leads.router)
app.include_router(appointments.router)
app.include_router(reports.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
