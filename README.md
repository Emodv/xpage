# CityVerified.ca

CityVerified.ca is the trust and action layer between AI agents and the physical economy.

## Canonical product
- https://cityverified.ca
- https://cityverified.ca/scan
- https://cityverified.ca/llms.txt

The canonical infrastructure is this repository, the existing Vercel production project, and Supabase project `rkjgwibukemohkzmtkkf`. Do not create duplicate infrastructure.

`licensed=true` must only be returned when licence evidence is verified from a real registry source and stored with provenance.

## Vercel Cron
Use the canonical CityVerified production project → Settings → Cron Jobs.

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
