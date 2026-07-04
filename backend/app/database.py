"""Supabase client, used server-side with the service role key (bypasses RLS).

The dashboard talks to Supabase directly with the anon key + user JWT so RLS
policies apply there; the backend always acts as a trusted service.
"""
from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
