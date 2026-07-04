"""Resolves which tenant an inbound webhook belongs to.

Routing key is the channel identifier the message arrived on (WhatsApp
phone_number_id, Telegram bot username) — looked up against the `tenants`
table in Supabase, then merged with that tenant's YAML config for business
rules (services, hours, persona).
"""
from __future__ import annotations

from typing import Optional

from supabase import Client

from app.config import TenantConfig, get_tenant_config


class ResolvedTenant:
    def __init__(self, tenant_row: dict, config: TenantConfig):
        self.id: str = tenant_row["id"]
        self.slug: str = tenant_row["slug"]
        self.row = tenant_row
        self.config = config


def resolve_tenant_by_whatsapp_phone_id(db: Client, phone_number_id: str) -> Optional[ResolvedTenant]:
    result = (
        db.table("tenants")
        .select("*")
        .eq("whatsapp_phone_number_id", phone_number_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return None
    row = result.data[0]
    config = get_tenant_config(row["slug"])
    if not config:
        return None
    return ResolvedTenant(row, config)


def resolve_tenant_by_telegram_bot(db: Client, bot_username: str) -> Optional[ResolvedTenant]:
    result = (
        db.table("tenants")
        .select("*")
        .eq("telegram_bot_username", bot_username)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return None
    row = result.data[0]
    config = get_tenant_config(row["slug"])
    if not config:
        return None
    return ResolvedTenant(row, config)


def resolve_tenant_by_id(db: Client, tenant_id: str) -> Optional[ResolvedTenant]:
    result = db.table("tenants").select("*").eq("id", tenant_id).limit(1).execute()
    if not result.data:
        return None
    row = result.data[0]
    config = get_tenant_config(row["slug"])
    if not config:
        return None
    return ResolvedTenant(row, config)
