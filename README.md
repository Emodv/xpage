# AI Lead Response & Booking System

AI-powered lead response and appointment booking for solo/small service
businesses (mortgage brokers, lawyers, dentists, insurance brokers) serving
the Iranian-Canadian community in Toronto/Vancouver. Captures inbound
WhatsApp/Telegram messages, qualifies the lead with GPT-4o in Farsi or
English, offers open appointment slots, books confirmed appointments on
Google Calendar, and gives the business owner a live dashboard plus a
weekly performance report.

Built multi-tenant from day one: onboarding a new business is a database
row + a config file (`tenants/<slug>.yaml`), not a code change.

## Repo layout

```
backend/    FastAPI service: webhooks, GPT-4o responder, Calendar/WhatsApp/
            Telegram integrations, CRM API, weekly report generator
frontend/   Next.js admin dashboard (Supabase Auth, live lead feed, manual override)
migrations/ Supabase SQL schema (tenants, leads, messages, appointments, RLS)
tenants/    Per-client config (business name, services, hours, AI persona)
docs/       Architecture and setup guides
```

## Docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — how the pieces fit together
- [`docs/SETUP.md`](docs/SETUP.md) — step-by-step setup for the first test client

## Quick start

See `docs/SETUP.md` for the full walkthrough (Supabase, WhatsApp, Telegram,
Google Calendar, backend, frontend). In short:

```
# Backend
cd backend && cp .env.example .env && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && cp .env.example .env.local && npm install && npm run dev
```

## Status

MVP built for one test client (`tenants/mortgage-broker-demo.yaml`, a
Toronto mortgage broker). The schema, webhook routing, and config loading
are already multi-tenant — adding client #2 is config, not code (see
"Adding the next client" in `docs/SETUP.md`).
