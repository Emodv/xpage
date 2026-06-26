# API Keys Inventory

Names and purposes only — **no real values stored here**. Actual secrets belong in a password manager or a local, git-ignored `.env` file, never in this repo or in chat.

> ⚠️ Every key below was pasted in plaintext into a chat session. Treat all of them as **compromised** and rotate at the source dashboard before relying on this list for anything live.

## Status legend
- 🔁 **Rotate** — exposed in chat, regenerate before use
- 🗑️ **Dedupe** — duplicate of another entry, pick one and drop the rest
- ❓ **Gap** — referenced as needed but no value was ever provided

---

## Google
| Env var | Purpose | Status |
|---|---|---|
| `GOOGLE_CLIENT_ID_1` / `GOOGLE_CLIENT_SECRET_1` | OAuth client 1 | 🔁 |
| `GOOGLE_CLIENT_ID_2` / `GOOGLE_CLIENT_SECRET_2` | OAuth client 2 | 🔁 |
| `GOOGLE_CLIENT_ID_3` / `GOOGLE_CLIENT_SECRET_3` | OAuth client 3 | 🔁 |
| `GOOGLE_CLIENT_ID_4` / `GOOGLE_CLIENT_SECRET_4` | OAuth client 4 | 🔁 |
| `GOOGLE_CLIENT_ID_5` | OAuth client 5 | ❓ no matching secret was ever given |
| `GOOGLE_REFRESH_TOKEN` | OAuth refresh token for Gmail/Calendar draft creator | ❓ never provided |
| `GOOGLE_APP_PASSWORD` | App password for `emod@banoo.marketing` (SMTP-style access) | 🔁 highest priority — this is a real account password |
| `GOOGLE_API_KEY_1` | General Google API key | 🔁 |
| `GOOGLE_API_KEY_2` | General Google API key | 🔁 |
| `GOOGLE_MAPS_API_KEY` | Maps API | 🗑️ same value as `GOOGLE_API_KEY_2` — pick one name |
| `GOOGLE_ADS_API_KEY` | Ads API | 🗑️ same value as `GOOGLE_API_KEY_1` — pick one name |

**Recommendation:** 5 OAuth clients under one project (`lead-gen-ai-457318`) is a lot to track — confirm which one is actually wired into the Deal Engine and archive/delete the unused ones in Google Cloud Console rather than keeping them all live.

## AI Providers
| Env var | Purpose | Status |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API (email writer, web research) | 🔁 — also listed twice with identical purpose across pastes |
| `OPENAI_API_KEY` | OpenAI API | 🔁 |
| `AI_GATEWAY_API_KEY` | Vercel AI Gateway | 🔁 |

## Outbound / Leadgen
| Env var | Purpose | Status |
|---|---|---|
| `APOLLO_API_KEY` | Apollo.io prospect search | 🔁 — appeared once blank (template) and once with a real value; use the real one |
| `SEMRUSH_API_KEY` | SEO/competitive data | 🔁 |
| `SCRAPEGRAPHAI_API_KEY` | Web scraping | 🗑️ same value as `SGAI_API_KEY` — pick one name |

## Payments
| Env var | Purpose | Status |
|---|---|---|
| `STRIPE_PUBLISHABLE_KEY` | Stripe client-side | 🔁 |
| `STRIPE_SECRET_KEY` | Stripe server-side | 🔁 highest priority among Stripe |

## Social / Messaging
| Env var | Purpose | Status |
|---|---|---|
| `X_API_KEY` / `X_API_KEY_SECRET` | X (Twitter) app | 🔁 |
| `X_BEARER_TOKEN` | X API v2 app-only auth | 🔁 |
| `X_ACCESS_TOKEN` / `X_ACCESS_TOKEN_SECRET` | X user-context auth | 🔁 |
| `X_OAUTH2_CLIENT_ID` / `X_OAUTH2_CLIENT_SECRET` | X OAuth2 client | 🔁 |
| `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` | Telegram MTProto app | 🔁 — repeated identically twice |
| `TELEGRAM_APP_TITLE` / `TELEGRAM_APP_SHORT_NAME` | App display metadata (not secret) | — |
| `TELEGRAM_TEST_*` / `TELEGRAM_PRODUCTION_*` | MTProto DC connection params (public Telegram server constants, not secrets) | — |

## Infra / Misc
| Env var | Purpose | Status |
|---|---|---|
| `VERCEL_USER_ID` | Vercel account identifier | low sensitivity, but rotate if paired with the AI Gateway key |
| `FLY_API_TOKEN_1`, `FLY_API_TOKEN_2` | Fly.io deploy tokens | 🔁 — two tokens, unclear if both needed |
| `IMPROVMX_API_KEY` | ImprovMX email forwarding | 🔁 |
| `IMPROVMX_PROVIDER` | Config value (`improvmx`), not a secret | — |
| `CALCOM_USERNAME` / `CALCOM_URL` | Cal.com public profile info, not secret | — |

---

## Action items
1. **Rotate everything marked 🔁** at the provider dashboard — Stripe, OpenAI, Anthropic Console, Apollo, Google Cloud (OAuth clients + API keys), X Developer Portal, Fly.io, ImprovMX, ScrapeGraphAI. Highest priority: `GOOGLE_APP_PASSWORD` and `STRIPE_SECRET_KEY`.
2. **Dedupe** the 🗑️ items — `GOOGLE_MAPS_API_KEY`/`GOOGLE_ADS_API_KEY` vs `GOOGLE_API_KEY_1/2`, and `SCRAPEGRAPHAI_API_KEY` vs `SGAI_API_KEY`. Keep one name per value.
3. **Store real values** in a password manager (1Password/Bitwarden) or a local `.env` file added to `.gitignore` — never in this repo or in chat.
4. Once rotated, the new values can populate a `.env` file locally for the Deal Engine build; I'll scaffold `.env.example` with these var names as empty placeholders when you're ready to build.
