# Architecture

## Overview

Multi-tenant AI lead response and booking system. Each business client
("tenant") gets a row in Supabase plus a config file — no code changes to
onboard a new client.

```
WhatsApp Cloud API  ──┐
Telegram Bot API    ──┼──▶  FastAPI webhooks  ──▶  lead_service (orchestrator)
                       │                              │
                       │                              ├─▶ Supabase (CRM: leads, messages, appointments)
                       │                              ├─▶ GPT-4o (ai_responder: qualify + reply)
                       │                              ├─▶ Google Calendar (availability + booking)
                       │                              └─▶ WhatsApp/Telegram send (outbound reply)
                       │
Next.js dashboard  ────┴──▶  Supabase directly (RLS-scoped reads/realtime)
                             + FastAPI /leads/reply (manual override, needs provider creds)

External scheduler (cron) ──▶ FastAPI /reports/weekly/{tenant_id} ──▶ report_service
                                                                        (email + WhatsApp summary)
```

## Multi-tenancy model

- `tenants` table: one row per business (mortgage broker, dentist, lawyer, ...).
  Routing keys (`whatsapp_phone_number_id`, `telegram_bot_username`) let the
  webhook layer figure out which tenant an inbound message belongs to,
  purely from data — no per-tenant code paths.
- `tenants/<slug>.yaml`: business-specific config that doesn't belong in the
  database — service menu, business hours, AI persona/system prompt,
  appointment duration. Loaded once per process and cached (see
  `backend/app/config.py`).
- `tenant_users`: maps a Supabase Auth user to the tenant(s) they can see in
  the dashboard. Postgres Row Level Security (see `migrations/001_init.sql`)
  enforces that a signed-in owner only ever reads their own tenant's leads,
  messages, and appointments — the dashboard talks to Supabase directly with
  the anon key, so RLS is the only thing standing between tenants.
- The FastAPI backend always uses the Supabase **service role** key (bypasses
  RLS) because it needs to write to whichever tenant a webhook resolves to.

**Onboarding a new client:** insert a `tenants` row, drop a
`tenants/<new-slug>.yaml`, invite their WhatsApp number/Telegram bot, share
their Google Calendar with the service account, add them to `tenant_users`.
Nothing else changes.

## Conversation flow (`backend/app/services/lead_service.py`)

1. Webhook receives a message → resolve tenant → upsert `leads` row (keyed on
   `tenant_id + channel + external_id`) → store inbound `messages` row.
2. If the lead has been handed off to a human (`ai_enabled = false`), stop —
   no auto-reply.
3. Otherwise, fetch open Google Calendar slots for the tenant (respecting
   `business_hours` from the YAML config) and the full message history.
4. Call GPT-4o (`ai_responder.get_ai_response`) with a tool/function-calling
   schema that forces a structured response: reply text, detected language,
   any newly-learned qualification fields (service/budget/timeline), and
   whether the lead just confirmed one of the offered slots.
5. Update the `leads` row with whatever was learned; if a slot was
   confirmed, create the Google Calendar event and an `appointments` row,
   and mark the lead `booked`.
6. Store the outbound `messages` row and send it through the same channel
   the lead messaged in.

## Weekly report (`backend/app/services/report_service.py`)

Aggregates the last 7 days of `leads`/`appointments` per tenant, upserts a
`weekly_reports` row, and sends the summary by email (SMTP) and WhatsApp to
`owner_email`/`owner_whatsapp_number`. Triggered externally (cron, GitHub
Actions schedule, Supabase `pg_cron` calling out via `net.http_post`) hitting
`POST /reports/weekly/{tenant_id}` — this keeps the backend stateless and
lets each tenant's report cadence be reconfigured without redeploying.

## Admin dashboard (`frontend/`)

Next.js App Router + Supabase Auth (email/password). The dashboard reads
`leads`/`messages` straight from Supabase with Realtime subscriptions — RLS
does the tenant scoping, so there's no dashboard-specific backend API for
reads. The one write that needs the backend is sending a manual reply
(`POST /leads/reply`), because that requires the WhatsApp/Telegram provider
credentials the browser must never see; sending it also flips
`ai_enabled = false` on that lead so the AI won't talk over the human.

## Why this split (FastAPI + direct Supabase reads)

- Webhooks and anything touching third-party credentials (OpenAI, WhatsApp,
  Telegram, Google Calendar, SMTP) live in FastAPI, server-side only.
- Dashboard reads go directly to Supabase so the live lead feed is realtime
  "for free" (Postgres change streams) without a bespoke polling API, and
  RLS is the single source of truth for tenant isolation instead of
  duplicating that logic in the backend.
