"""Gmail access: OAuth, fetching unread mail, and applying category labels.

Least privilege: requests the read-only scope unless `apply=True`, in which case
it requests the modify scope (needed to add labels). Tokens are cached per-scope
so switching modes doesn't silently reuse a token with the wrong permissions.

First run opens a browser for consent. You need a `credentials.json` (OAuth client
of type "Desktop app") from Google Cloud Console in the working directory — see
the tool README for the 2-minute setup.
"""

from __future__ import annotations

import os
from typing import Any

from . import config

CREDENTIALS_FILE = os.environ.get("TRIAGE_CREDENTIALS", "credentials.json")


def _token_file(apply: bool) -> str:
    return "token_modify.json" if apply else "token_readonly.json"


def get_service(apply: bool = False):
    """Build an authenticated Gmail API client."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover - dependency guidance
        raise SystemExit(
            "Gmail support needs extra packages. Install them with:\n"
            "    pip install google-api-python-client google-auth-oauthlib\n"
            f"(import error: {exc})"
        )

    scopes = [config.SCOPE_MODIFY if apply else config.SCOPE_READONLY]
    token_path = _token_file(apply)
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise SystemExit(
                    f"Missing {CREDENTIALS_FILE}. Download an OAuth 'Desktop app' "
                    "client from Google Cloud Console and save it here. See the README."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_unread(service, max_results: int = 25) -> list[dict[str, Any]]:
    """Return recent unread messages as {id, sender, subject, snippet, date}."""
    resp = (
        service.users()
        .messages()
        .list(userId="me", q="is:unread", maxResults=max_results)
        .execute()
    )
    ids = [m["id"] for m in resp.get("messages", [])]
    emails: list[dict[str, Any]] = []
    for msg_id in ids:
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            )
            .execute()
        )
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        emails.append(
            {
                "id": msg_id,
                "sender": headers.get("From", "(unknown sender)"),
                "subject": headers.get("Subject", "(no subject)"),
                "snippet": msg.get("snippet", ""),
                "date": headers.get("Date", ""),
            }
        )
    return emails


def _list_labels(service) -> dict[str, str]:
    resp = service.users().labels().list(userId="me").execute()
    return {lab["name"]: lab["id"] for lab in resp.get("labels", [])}


def ensure_label(service, name: str, cache: dict[str, str]) -> str:
    """Return the id of label `name`, creating it (and its parent) if needed."""
    if name in cache:
        return cache[name]
    created = (
        service.users()
        .labels()
        .create(
            userId="me",
            body={
                "name": name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        )
        .execute()
    )
    cache[name] = created["id"]
    return created["id"]


def apply_label(service, msg_id: str, label_id: str) -> None:
    service.users().messages().modify(
        userId="me", id=msg_id, body={"addLabelIds": [label_id]}
    ).execute()


def label_cache(service) -> dict[str, str]:
    """Snapshot existing labels so we don't recreate ones that exist."""
    return _list_labels(service)
