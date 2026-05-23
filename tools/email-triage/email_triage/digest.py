"""Render classified emails as a terminal report and a markdown file."""

from __future__ import annotations

from typing import Any

from . import config


def _group(emails: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {k: [] for k in config.CATEGORY_KEYS}
    for e in emails:
        groups[e["category"]].append(e)
    for key in groups:
        groups[key].sort(key=lambda e: config.PRIORITY_RANK.get(e["priority"], 1))
    return groups


def _truncate(text: str, width: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1] + "…"


def render_terminal(emails: list[dict[str, Any]]) -> str:
    groups = _group(emails)
    lines = ["", "=" * 60, f"  EMAIL TRIAGE  —  {len(emails)} unread sorted", "=" * 60]

    high = sum(1 for e in emails if e["priority"] == "high")
    lines.append(f"  ‼️  {high} high-priority   ·   {len(emails) - high} can wait")

    for cat in config.CATEGORIES:
        items = groups[cat["key"]]
        if not items:
            continue
        lines.append("")
        lines.append(f"{cat['emoji']}  {cat['label'].upper()}  ({len(items)})")
        lines.append("-" * 60)
        for e in items:
            badge = config.PRIORITY_BADGE[e["priority"]]
            sender = _truncate(e.get("sender", ""), 28)
            subject = _truncate(e.get("subject", ""), 44)
            lines.append(f"  {badge}  {sender:<28}  {subject}")
            lines.append(f"          ↳ {_truncate(e['reason'], 64)}")
    lines.append("")
    return "\n".join(lines)


def render_markdown(emails: list[dict[str, Any]]) -> str:
    groups = _group(emails)
    high = sum(1 for e in emails if e["priority"] == "high")
    out = [
        "# Email Triage Report",
        "",
        f"**{len(emails)} unread** · **{high} high-priority** · {len(emails) - high} can wait",
        "",
    ]
    for cat in config.CATEGORIES:
        items = groups[cat["key"]]
        if not items:
            continue
        out.append(f"## {cat['emoji']} {cat['label']} ({len(items)})")
        out.append("")
        out.append("| Priority | From | Subject | Why |")
        out.append("|---|---|---|---|")
        for e in items:
            sender = e.get("sender", "").replace("|", "/")
            subject = e.get("subject", "").replace("|", "/")
            reason = e["reason"].replace("|", "/")
            out.append(f"| {e['priority']} | {sender} | {subject} | {reason} |")
        out.append("")
    return "\n".join(out)
