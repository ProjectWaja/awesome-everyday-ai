"""Configuration: category taxonomy, models, and runtime settings.

Everything tunable lives here so the rest of the package stays declarative.
Environment variables (optionally loaded from a local .env) override defaults.
"""

from __future__ import annotations

import os

# --- Models -----------------------------------------------------------------
# Classification is a fast, high-volume task, so the default Claude model is
# Haiku. Override with TRIAGE_CLAUDE_MODEL if you want more nuanced sorting.
CLAUDE_MODEL = os.environ.get("TRIAGE_CLAUDE_MODEL", "claude-haiku-4-5")

# Any locally-pulled Ollama model works; llama3.2 is small and quick.
OLLAMA_MODEL = os.environ.get("TRIAGE_OLLAMA_MODEL", "llama3.2")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Gmail labels created by --apply are nested under this parent, e.g. "Triage/Urgent".
LABEL_PREFIX = os.environ.get("TRIAGE_LABEL_PREFIX", "Triage")

# --- Taxonomy ----------------------------------------------------------------
# `key` is the stable token the model returns. `label` is the Gmail sub-label.
CATEGORIES: list[dict[str, str]] = [
    {
        "key": "URGENT",
        "label": "Urgent",
        "emoji": "🔴",
        "desc": "Time-sensitive and needs action today: deadlines, outages, "
        "anything with real consequences if ignored for 24h.",
    },
    {
        "key": "ACTION",
        "label": "Action",
        "emoji": "🟠",
        "desc": "Needs a reply or a task from you, but is not time-critical. "
        "Questions directed at you, requests, things awaiting your input.",
    },
    {
        "key": "FYI",
        "label": "FYI",
        "emoji": "🔵",
        "desc": "Informational, no action required. Announcements, confirmations, "
        "things you only need to be aware of.",
    },
    {
        "key": "NEWSLETTER",
        "label": "Newsletter",
        "emoji": "📰",
        "desc": "Subscribed newsletters, digests, and content roundups.",
    },
    {
        "key": "PROMOTION",
        "label": "Promotion",
        "emoji": "🛍️",
        "desc": "Marketing, sales, discounts, and promotional offers.",
    },
    {
        "key": "RECEIPT",
        "label": "Receipt",
        "emoji": "🧾",
        "desc": "Orders, receipts, invoices, payment and shipping confirmations.",
    },
    {
        "key": "SOCIAL",
        "label": "Social",
        "emoji": "💬",
        "desc": "Notifications from social networks and community platforms.",
    },
    {
        "key": "JUNK",
        "label": "Junk",
        "emoji": "🗑️",
        "desc": "Likely spam, cold outreach, or unwanted mail with no value to you.",
    },
]

CATEGORY_KEYS = [c["key"] for c in CATEGORIES]
CATEGORY_BY_KEY = {c["key"]: c for c in CATEGORIES}
DEFAULT_CATEGORY = "FYI"  # fallback when the model returns an unknown key

PRIORITIES = ["high", "medium", "low"]
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
DEFAULT_PRIORITY = "medium"
PRIORITY_BADGE = {"high": "‼️ HIGH", "medium": "•  MED", "low": "·  LOW"}

# Gmail OAuth scopes — least privilege: read-only unless you ask to apply labels.
SCOPE_READONLY = "https://www.googleapis.com/auth/gmail.readonly"
SCOPE_MODIFY = "https://www.googleapis.com/auth/gmail.modify"


def normalize_category(value: str | None) -> str:
    """Coerce a model-returned category to a known key (defensive)."""
    if value and value.upper() in CATEGORY_BY_KEY:
        return value.upper()
    return DEFAULT_CATEGORY


def normalize_priority(value: str | None) -> str:
    if value and value.lower() in PRIORITY_RANK:
        return value.lower()
    return DEFAULT_PRIORITY
