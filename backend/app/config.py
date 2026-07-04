"""Application settings and per-tenant config loading.

Tenants are onboarded by dropping a YAML file in `tenants/<slug>.yaml` and
inserting a matching row in the `tenants` Supabase table — no code changes.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
# Override with TENANTS_DIR env var when the layout differs from the repo checkout
# (e.g. inside the Docker image, where tenants/ is copied alongside app/).
TENANTS_DIR = Path(os.environ.get("TENANTS_DIR", str(REPO_ROOT / "tenants")))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", alias="OPENAI_MODEL")

    whatsapp_access_token: str = Field("", alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_verify_token: str = Field("", alias="WHATSAPP_VERIFY_TOKEN")
    whatsapp_api_version: str = Field("v20.0", alias="WHATSAPP_API_VERSION")

    telegram_bot_token: str = Field("", alias="TELEGRAM_BOT_TOKEN")

    google_calendar_credentials_json: str = Field("", alias="GOOGLE_CALENDAR_CREDENTIALS_JSON")

    smtp_host: str = Field("", alias="SMTP_HOST")
    smtp_port: int = Field(587, alias="SMTP_PORT")
    smtp_user: str = Field("", alias="SMTP_USER")
    smtp_password: str = Field("", alias="SMTP_PASSWORD")

    report_cron_secret: str = Field("", alias="REPORT_CRON_SECRET")


@lru_cache
def get_settings() -> Settings:
    return Settings()


class TenantConfig:
    """In-memory view of a tenant's YAML config, keyed by slug."""

    def __init__(self, data: dict):
        self.slug: str = data["slug"]
        self.business_name: str = data["business_name"]
        self.timezone: str = data.get("timezone", "America/Toronto")
        self.whatsapp_phone_number_id: Optional[str] = data.get("whatsapp_phone_number_id")
        self.telegram_bot_username: Optional[str] = data.get("telegram_bot_username")
        self.google_calendar_id: Optional[str] = data.get("google_calendar_id")
        self.owner_email: Optional[str] = data.get("owner_email")
        self.owner_whatsapp_number: Optional[str] = data.get("owner_whatsapp_number")
        self.business_hours: dict = data.get("business_hours", {})
        self.appointment_duration_minutes: int = data.get("appointment_duration_minutes", 30)
        self.services: list = data.get("services", [])
        self.ai_persona: str = data.get("ai_persona", "")
        self.raw = data


@lru_cache
def _load_all_tenant_configs() -> dict[str, TenantConfig]:
    configs = {}
    if not TENANTS_DIR.exists():
        return configs
    for path in TENANTS_DIR.glob("*.yaml"):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        configs[data["slug"]] = TenantConfig(data)
    return configs


def get_tenant_config(slug: str) -> Optional[TenantConfig]:
    return _load_all_tenant_configs().get(slug)


def all_tenant_configs() -> dict[str, TenantConfig]:
    return _load_all_tenant_configs()
