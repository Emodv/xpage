"""GPT-4o powered lead responder.

Given a tenant's persona/service menu, the open appointment slots, and the
conversation history, asks GPT-4o for a structured decision: what language to
reply in, what we've learned about the lead (service/budget/timeline), the
reply text itself, and whether the lead just confirmed a specific slot.
"""
from __future__ import annotations

import json
from datetime import datetime

from openai import AsyncOpenAI

from app.config import Settings, TenantConfig
from app.models import AIQualification

_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "respond_to_lead",
        "description": "Compose the reply to send to the lead and record what was learned about them.",
        "parameters": {
            "type": "object",
            "properties": {
                "reply_text": {
                    "type": "string",
                    "description": "The message to send back to the lead, in their language.",
                },
                "language": {
                    "type": "string",
                    "enum": ["fa", "en"],
                    "description": "Language of the lead's most recent message: Farsi or English.",
                },
                "service_needed": {"type": "string", "description": "Service the lead is asking about, if known."},
                "budget": {"type": "string", "description": "Lead's stated budget/price range, if known."},
                "timeline": {"type": "string", "description": "How soon the lead wants to move forward, if known."},
                "ready_to_book": {
                    "type": "boolean",
                    "description": "True once the lead has given enough info AND has been offered slots.",
                },
                "chosen_slot_index": {
                    "type": ["integer", "null"],
                    "description": "1-based index of the offered slot the lead just confirmed, if any this turn.",
                },
                "lead_status": {
                    "type": "string",
                    "enum": ["new", "qualified", "booked", "lost"],
                    "description": "new = still gathering info, qualified = info gathered/slots offered, "
                    "booked = lead confirmed a slot this turn, lost = lead is not interested.",
                },
            },
            "required": ["reply_text", "language", "ready_to_book", "lead_status"],
        },
    },
}


def _build_system_prompt(tenant: TenantConfig, slots: list[datetime]) -> str:
    services_list = "\n".join(f"- {s['name']} / {s.get('name_fa', '')}" for s in tenant.services)
    if slots:
        slot_lines = "\n".join(
            f"{i + 1}. {slot.strftime('%A %b %d, %I:%M %p')} ({tenant.timezone})"
            for i, slot in enumerate(slots)
        )
        slots_block = (
            "Available appointment slots you may offer (reference by number):\n" + slot_lines
        )
    else:
        slots_block = "No appointment slots are available to offer right now."

    return f"""{tenant.ai_persona}

Business: {tenant.business_name}
Services offered:
{services_list}

{slots_block}

Rules:
- Always reply in the same language as the lead's latest message (Farsi or English).
- Ask only for what's still missing: service needed, budget, timeline. Don't re-ask what you already know.
- Once you know the service and roughly the timeline, offer 2-3 of the slots above and ask them to pick one.
- If the lead's message clearly selects one of the offered slots (by number, time, or day), set
  chosen_slot_index to that slot's number and lead_status to "booked".
- If the lead says they're not interested or asks to stop, set lead_status to "lost".
- Keep replies short (2-4 sentences), warm, and professional. No emojis unless the lead uses them first.
- You must always call the respond_to_lead function with your answer."""


async def get_ai_response(
    settings: Settings,
    tenant: TenantConfig,
    conversation_history: list[dict],
    open_slots: list[datetime],
) -> AIQualification:
    """conversation_history: list of {"role": "user"|"assistant", "content": str}, oldest first."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    messages = [
        {"role": "system", "content": _build_system_prompt(tenant, open_slots)},
        *conversation_history,
    ]

    completion = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        tools=[_TOOL_SCHEMA],
        tool_choice={"type": "function", "function": {"name": "respond_to_lead"}},
    )

    tool_call = completion.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    return AIQualification(**args)
