-- Multi-tenant AI lead response and booking system
-- Every business client is a row in `tenants`; everything else hangs off tenant_id.
-- Onboarding a new client = inserting a tenants row + a tenant config file, no code changes.

create extension if not exists "pgcrypto";

create type lead_status as enum ('new', 'qualified', 'booked', 'lost');
create type message_direction as enum ('in', 'out');
create type message_channel as enum ('whatsapp', 'telegram');
create type appointment_status as enum ('scheduled', 'completed', 'no_show', 'cancelled');
create type tenant_role as enum ('owner', 'staff');

-- ---------------------------------------------------------------------------
-- tenants: one row per business client (mortgage broker, dentist, lawyer, ...)
-- ---------------------------------------------------------------------------
create table tenants (
    id uuid primary key default gen_random_uuid(),
    slug text unique not null,                 -- e.g. "mortgage-broker-demo", used to load tenants/<slug>.yaml
    business_name text not null,
    timezone text not null default 'America/Toronto',
    whatsapp_phone_number_id text unique,      -- WhatsApp Cloud API phone_number_id, used to route inbound webhooks
    telegram_bot_username text unique,         -- Telegram bot @username, used to route inbound webhooks
    google_calendar_id text,                   -- calendar to read/write availability on
    owner_email text,
    owner_whatsapp_number text,                -- where the weekly report gets sent
    is_active boolean not null default true,
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- tenant_users: maps Supabase auth users to the tenant(s) they can see in the dashboard
-- ---------------------------------------------------------------------------
create table tenant_users (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    role tenant_role not null default 'owner',
    created_at timestamptz not null default now(),
    unique (tenant_id, user_id)
);

-- ---------------------------------------------------------------------------
-- leads: one row per prospective client conversation
-- ---------------------------------------------------------------------------
create table leads (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    channel message_channel not null,
    external_id text not null,                 -- WhatsApp wa_id or Telegram chat_id
    display_name text,
    phone text,
    language text,                              -- 'fa' or 'en', set on first inbound message
    service_needed text,
    budget text,
    timeline text,
    status lead_status not null default 'new',
    ai_enabled boolean not null default true,    -- false once a human takes over the conversation
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (tenant_id, channel, external_id)
);

create index leads_tenant_status_idx on leads (tenant_id, status);

-- ---------------------------------------------------------------------------
-- messages: full conversation history per lead
-- ---------------------------------------------------------------------------
create table messages (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    lead_id uuid not null references leads(id) on delete cascade,
    direction message_direction not null,
    channel message_channel not null,
    body text not null,
    ai_generated boolean not null default false,
    created_at timestamptz not null default now()
);

create index messages_lead_idx on messages (lead_id, created_at);

-- ---------------------------------------------------------------------------
-- appointments: bookings created on the tenant's Google Calendar
-- ---------------------------------------------------------------------------
create table appointments (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    lead_id uuid not null references leads(id) on delete cascade,
    calendar_event_id text,
    start_time timestamptz not null,
    end_time timestamptz not null,
    status appointment_status not null default 'scheduled',
    revenue_amount numeric(10, 2),
    created_at timestamptz not null default now()
);

create index appointments_tenant_start_idx on appointments (tenant_id, start_time);

-- ---------------------------------------------------------------------------
-- weekly_reports: generated owner summaries, kept for audit/history
-- ---------------------------------------------------------------------------
create table weekly_reports (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    period_start date not null,
    period_end date not null,
    leads_received int not null default 0,
    leads_booked int not null default 0,
    no_shows int not null default 0,
    revenue_attributed numeric(10, 2) not null default 0,
    summary_text text,
    sent_at timestamptz,
    created_at timestamptz not null default now(),
    unique (tenant_id, period_start, period_end)
);

-- ---------------------------------------------------------------------------
-- updated_at trigger for leads
-- ---------------------------------------------------------------------------
create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger leads_set_updated_at
before update on leads
for each row execute function set_updated_at();

-- ---------------------------------------------------------------------------
-- Row Level Security: dashboard users only ever see their own tenant's data.
-- The backend (FastAPI) talks to Supabase with the service role key and bypasses RLS.
-- ---------------------------------------------------------------------------
alter table tenants enable row level security;
alter table tenant_users enable row level security;
alter table leads enable row level security;
alter table messages enable row level security;
alter table appointments enable row level security;
alter table weekly_reports enable row level security;

create or replace function is_tenant_member(check_tenant_id uuid)
returns boolean as $$
    select exists (
        select 1 from tenant_users
        where tenant_id = check_tenant_id and user_id = auth.uid()
    );
$$ language sql security definer stable;

create policy "tenant members can read their tenant" on tenants
    for select using (is_tenant_member(id));

create policy "tenant members can read their memberships" on tenant_users
    for select using (user_id = auth.uid());

create policy "tenant members can read their leads" on leads
    for select using (is_tenant_member(tenant_id));

create policy "tenant members can update their leads" on leads
    for update using (is_tenant_member(tenant_id));

create policy "tenant members can read their messages" on messages
    for select using (is_tenant_member(tenant_id));

create policy "tenant members can insert messages (manual override)" on messages
    for insert with check (is_tenant_member(tenant_id));

create policy "tenant members can read their appointments" on appointments
    for select using (is_tenant_member(tenant_id));

create policy "tenant members can read their reports" on weekly_reports
    for select using (is_tenant_member(tenant_id));
