# X.page

X.page is the trust and action layer between AI agents and the physical economy.

## Pitch tabs
- https://x.page
- https://x.page/scan
- https://x.page/v1/search?need=plumber&geo=toronto
- https://x.page/llms.txt

`licensed=true` currently returns 0 on purpose. Licence remains unverified until a real registry source is stored.

## Vercel Cron
Project `x-page` → Settings → Cron Jobs

Path:
`/api/cron/refresh?secret=CRON_SECRET`

Schedule:
`0 5 * * * America/Toronto`

Environment variable:
`CRON_SECRET`

Failed homepage fetches decay confidence by `×0.85`; existing phone facts are not deleted.

## Admin
- Demand: `GET /api/admin/demand?secret=ADMIN_KEY`
- Claim confirm: `POST /api/claim/confirm` with header `x-admin-key: ADMIN_KEY`

Required private Vercel environment variables:
- `CRON_SECRET`
- `ADMIN_KEY`
