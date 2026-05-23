"""Command-line entry point: fetch → classify → report → (optionally) label."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from . import classifier, config, digest


def _load_dotenv() -> None:
    """Best-effort .env loading; no hard dependency."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="email-triage",
        description="Sort your unread email into categories with AI.",
    )
    p.add_argument("--demo", action="store_true", help="Use bundled sample emails (no credentials).")
    p.add_argument("--max", type=int, default=25, help="Max unread emails to fetch (default 25).")
    p.add_argument(
        "--backend",
        choices=["auto", "claude", "ollama"],
        default="auto",
        help="Classification backend (default: auto-detect).",
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="Add category labels in Gmail (shows a dry-run preview and asks first).",
    )
    p.add_argument("--yes", action="store_true", help="Skip the confirmation prompt for --apply.")
    p.add_argument("--report", default="triage_report.md", help="Markdown report path ('' to skip).")
    p.add_argument("--no-report", action="store_true", help="Don't write the markdown report.")
    p.add_argument("-v", "--verbose", action="store_true", help="Show backend/usage details.")
    return p.parse_args(argv)


def _get_emails(args: argparse.Namespace):
    if args.demo:
        from .demo_data import SAMPLE_EMAILS

        return list(SAMPLE_EMAILS), None
    from . import gmail_client

    service = gmail_client.get_service(apply=args.apply)
    emails = gmail_client.fetch_unread(service, max_results=args.max)
    return emails, service


def _apply_labels(service, emails: list[dict[str, Any]], skip_confirm: bool) -> None:
    from . import gmail_client

    plan = [
        (e, f"{config.LABEL_PREFIX}/{config.CATEGORY_BY_KEY[e['category']]['label']}")
        for e in emails
    ]
    print("\nDry run — labels that would be applied:")
    counts: dict[str, int] = {}
    for _e, label in plan:
        counts[label] = counts.get(label, 0) + 1
    for label, n in sorted(counts.items()):
        print(f"  {label:<24} {n}")

    if not skip_confirm:
        answer = input("\nApply these labels in Gmail? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted — no changes made.")
            return

    cache = gmail_client.label_cache(service)
    for e, label in plan:
        label_id = gmail_client.ensure_label(service, label, cache)
        gmail_client.apply_label(service, e["id"], label_id)
    print(f"Applied labels to {len(plan)} message(s).")


def main(argv: list[str] | None = None) -> int:
    # The digest uses emoji; Windows consoles default to cp1252 and would crash
    # on encode. Force UTF-8 (with replace as a last resort) so output is portable.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    _load_dotenv()
    args = _parse_args(argv)

    backend = classifier.choose_backend(None if args.backend == "auto" else args.backend)
    if backend is None:
        print(
            "No backend available. Set ANTHROPIC_API_KEY for Claude, or run a local\n"
            "Ollama server (https://ollama.com). See the README.",
            file=sys.stderr,
        )
        return 2

    try:
        emails, service = _get_emails(args)
    except SystemExit as exc:  # surfaced from gmail_client with guidance
        print(exc, file=sys.stderr)
        return 2

    if not emails:
        print("No unread emails. Inbox zero. ✨")
        return 0

    print(f"Classifying {len(emails)} email(s) with backend: {backend} …")
    classified = classifier.classify(emails, backend, verbose=args.verbose)

    print(digest.render_terminal(classified))

    if not args.no_report and args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            fh.write(digest.render_markdown(classified))
        print(f"Markdown report written to {args.report}")

    if args.apply:
        if args.demo:
            print("\n(--apply is ignored in --demo mode; there's no real inbox to label.)")
        else:
            _apply_labels(service, classified, skip_confirm=args.yes)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
