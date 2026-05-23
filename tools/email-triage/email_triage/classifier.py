"""Email classification with two interchangeable backends.

- Claude (default when ANTHROPIC_API_KEY is set): best quality. Uses structured
  outputs so the response is guaranteed to match our schema, and a cached system
  prompt carrying the category taxonomy.
- Ollama (fallback): fully local and private. Uses Ollama's JSON schema output.

Both return the same shape: a list of dicts {id, category, priority, reason}.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from pydantic import BaseModel

from . import config


class EmailVerdict(BaseModel):
    id: str
    category: str
    priority: str
    reason: str


class VerdictBatch(BaseModel):
    verdicts: list[EmailVerdict]


# --- Prompt construction -----------------------------------------------------

def build_taxonomy_prompt() -> str:
    """The stable system prompt. Identical across runs, so it caches cleanly."""
    lines = [
        "You are an email triage assistant. For each email you are given, assign "
        "exactly one category and one priority, plus a one-line reason.",
        "",
        "CATEGORIES (return the uppercase key):",
    ]
    for c in config.CATEGORIES:
        lines.append(f"- {c['key']}: {c['desc']}")
    lines += [
        "",
        "PRIORITY (return lowercase):",
        "- high: needs attention today, or notable consequences if missed.",
        "- medium: worth handling soon but not urgent.",
        "- low: no real consequence if it waits or is ignored.",
        "",
        "RULES:",
        "- Choose the single best-fitting category. Marketing beats newsletter when "
        "the intent is to sell. A receipt for a purchase is RECEIPT, not PROMOTION.",
        "- Most NEWSLETTER / PROMOTION / SOCIAL / JUNK mail is low priority.",
        "- A direct question or request addressed to the recipient is usually ACTION "
        "or URGENT, not FYI.",
        "- Return one verdict per input email and preserve each email's `id` exactly.",
    ]
    return "\n".join(lines)


def build_user_payload(emails: list[dict[str, Any]]) -> str:
    slim = [
        {
            "id": e["id"],
            "from": e.get("sender", ""),
            "subject": e.get("subject", ""),
            "snippet": e.get("snippet", ""),
        }
        for e in emails
    ]
    return (
        "Classify the following emails. Return one verdict per email.\n\n"
        + json.dumps(slim, ensure_ascii=False, indent=2)
    )


# --- Claude backend ----------------------------------------------------------

def classify_claude(emails: list[dict[str, Any]], verbose: bool = False) -> list[dict[str, str]]:
    import anthropic  # imported lazily so Ollama-only users don't need the dep

    client = anthropic.Anthropic()
    response = client.messages.parse(
        model=config.CLAUDE_MODEL,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": build_taxonomy_prompt(),
                # Caches the taxonomy prefix. Note: the prefix must exceed the
                # model's minimum cacheable size (~4096 tokens on Haiku) to
                # actually cache — for a short taxonomy this is a no-op, which is
                # harmless. It pays off once you grow the prompt with examples.
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": build_user_payload(emails)}],
        output_format=VerdictBatch,
    )
    if verbose:
        u = response.usage
        cached = getattr(u, "cache_read_input_tokens", 0) or 0
        print(
            f"  [claude] model={config.CLAUDE_MODEL} in={u.input_tokens} "
            f"out={u.output_tokens} cache_read={cached}"
        )
    batch = response.parsed_output
    if batch is None:
        raise RuntimeError("Claude returned no parsed output (possible refusal).")
    return [v.model_dump() for v in batch.verdicts]


# --- Ollama backend ----------------------------------------------------------

def _ollama_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "verdicts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "category": {"type": "string", "enum": config.CATEGORY_KEYS},
                        "priority": {"type": "string", "enum": config.PRIORITIES},
                        "reason": {"type": "string"},
                    },
                    "required": ["id", "category", "priority", "reason"],
                },
            }
        },
        "required": ["verdicts"],
    }


def ollama_available() -> bool:
    try:
        req = urllib.request.Request(f"{config.OLLAMA_HOST}/api/tags")
        with urllib.request.urlopen(req, timeout=2):
            return True
    except (urllib.error.URLError, OSError):
        return False


def classify_ollama(emails: list[dict[str, Any]], verbose: bool = False) -> list[dict[str, str]]:
    payload = {
        "model": config.OLLAMA_MODEL,
        "stream": False,
        "format": _ollama_schema(),
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": build_taxonomy_prompt()},
            {"role": "user", "content": build_user_payload(emails)},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{config.OLLAMA_HOST}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    if verbose:
        print(f"  [ollama] model={config.OLLAMA_MODEL} host={config.OLLAMA_HOST}")
    content = body.get("message", {}).get("content", "{}")
    parsed = json.loads(content)
    return parsed.get("verdicts", [])


# --- Dispatch + normalization ------------------------------------------------

def classify(
    emails: list[dict[str, Any]], backend: str, verbose: bool = False
) -> list[dict[str, Any]]:
    """Classify `emails` and merge verdicts back onto them by id."""
    if not emails:
        return []

    if backend == "claude":
        raw = classify_claude(emails, verbose=verbose)
    elif backend == "ollama":
        raw = classify_ollama(emails, verbose=verbose)
    else:
        raise ValueError(f"Unknown backend: {backend}")

    by_id = {v.get("id"): v for v in raw}
    enriched = []
    for e in emails:
        v = by_id.get(e["id"], {})
        enriched.append(
            {
                **e,
                "category": config.normalize_category(v.get("category")),
                "priority": config.normalize_priority(v.get("priority")),
                "reason": v.get("reason", "").strip() or "(no reason given)",
            }
        )
    return enriched


def choose_backend(prefer: str | None = None) -> str | None:
    """Pick a backend. Explicit `prefer` wins; else auto-detect."""
    import os

    if prefer in ("claude", "ollama"):
        return prefer
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    if ollama_available():
        return "ollama"
    return None
