# Setup: MVP for one test client (mortgage broker)

This walks through standing up the system for a single tenant end-to-end.
Multi-tenant onboarding after that is just "repeat step 2 and 3 with a new
slug" — see `docs/ARCHITECTURE.md`.

## 1. Supabase project

1. Create a project at supabase.com.
2. Run `migrations/001_init.sql` in the SQL editor (or via the Supabase CLI:
   `supabase db push`).
3. In Authentication, create the business owner's user (email/password or
   invite link).
4. Insert their tenant row:

   ```sql
   insert into tenants (slug, business_name, whatsapp_phone_number_id, telegram_bot_username, google_calendar_id, owner_email, owner_whatsapp_number)
   values ('mortgage-broker-demo', 'Parsa Mortgages', '<whatsapp phone_number_id>', 'ParsaMortgagesBot', '<calendar id>', 'owner@example.com', '+16475551234');

   insert into tenant_users (tenant_id, user_id, role)
   values ((select id from tenants where slug = 'mortgage-broker-demo'), '<owner auth.users id>', 'owner');
   ```
5. Copy the Project URL, `service_role` key (backend), and `anon` key
   (frontend) from Settings → API.

## 2. Tenant config file

Copy `tenants/mortgage-broker-demo.yaml` and edit it for the real client:
business name, services, business hours, AI persona, and the
`whatsapp_phone_number_id` / `telegram_bot_username` / `google_calendar_id`
values matching the Supabase row above. The `slug` in the YAML **must**
match the `tenants.slug` row exactly — that's the join key.

## 3. WhatsApp Business API (Meta Cloud API)

1. Create a Meta app, add the WhatsApp product, and get a test phone number
   (or your verified business number).
2. Set the webhook URL to `https://<your-backend>/webhooks/whatsapp` and the
   verify token to whatever you set as `WHATSAPP_VERIFY_TOKEN`.
3. Subscribe to the `messages` field.
4. Put the phone number's `phone_number_id` in both the tenant's Supabase
   row and its YAML config.

## 4. Telegram bot

1. Create a bot with @BotFather, get its token → `TELEGRAM_BOT_TOKEN`.
2. Register the webhook (one bot = one tenant in this MVP; the URL includes
   the bot's username so one FastAPI deployment can serve multiple bots):

   ```
   curl "https://api.telegram.org/bot<token>/setWebhook?url=https://<your-backend>/webhooks/telegram/<bot_username>"
   ```

## 5. Google Calendar

1. Create a Google Cloud service account, enable the Calendar API, download
   its JSON key → `GOOGLE_CALENDAR_CREDENTIALS_JSON` (as a one-line JSON
   string).
2. Share the tenant's Google Calendar with the service account's email
   (`...@...iam.gserviceaccount.com`), "Make changes to events" permission.

## 6. Backend

```
cd backend
cp .env.example .env   # fill in the values from steps 1, 3, 4, 5, plus OPENAI_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run the test suite: `pytest` (uses mocked external calls, no live creds
needed).

Docker: `docker build -f backend/Dockerfile -t lead-booking-backend .` (run
from the repo root so the `tenants/` directory is in the build context).

## 7. Frontend

```
cd frontend
cp .env.example .env.local   # NEXT_PUBLIC_SUPABASE_URL / ANON_KEY / API_BASE_URL
npm install
npm run dev
```

Sign in with the owner account created in step 1.4.

## 8. Weekly report

Schedule something to call this weekly, e.g. a GitHub Actions cron:

```
curl -X POST https://<your-backend>/reports/weekly/<tenant-id> \
  -H "X-Cron-Secret: <REPORT_CRON_SECRET>"
```

## Adding the next client (multi-tenant, no code changes)

1. Insert a new `tenants` row + `tenant_users` row.
2. Add `tenants/<new-slug>.yaml`.
3. Point their WhatsApp number/Telegram bot webhook at the same backend URL.
4. Share their Google Calendar with the same service account.

The backend and dashboard code do not change.
