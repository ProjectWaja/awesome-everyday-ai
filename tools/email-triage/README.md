# 📥 AI Email Triage

**Sort your unread inbox into categories in seconds — locally or with Claude.**

A small, honest reference implementation of the "tame your inbox" recipe from the
[main list](../../README.md). It fetches your unread Gmail, asks an AI to sort each
message into a category with a priority and a one-line reason, prints a clean digest,
and — only if you ask — applies matching labels in Gmail.

```
============================================================
  EMAIL TRIAGE  —  10 unread sorted
============================================================
  ‼️  3 high-priority   ·   7 can wait

🔴  URGENT  (2)
------------------------------------------------------------
  ‼️ HIGH  Billing                       Action required: payment failed…
          ↳ Payment failure with a hard deadline; service interruption risk.
  ‼️ HIGH  Dr. Patel's Office            Appointment reminder: tomorrow 9:00 AM
          ↳ Time-sensitive reminder for tomorrow morning.
...
```

---

## Why this exists

It's the highest-leverage everyday automation: the **context → model → draft → you approve**
loop applied to the chore everyone has. It's deliberately small (a few hundred lines)
so you can read the whole thing, and it's **safe by default** — read-only unless you
pass `--apply`, and even then it shows a dry-run and asks before touching your inbox.

| Design choice | Why |
|---|---|
| 🟢 **Read-only by default** | It never modifies your inbox unless you opt in with `--apply`. |
| 🔒 **Two backends** | Claude for quality, **Ollama for fully-local/private**. Auto-detected. |
| 🧾 **Structured output** | Uses the model's JSON-schema mode, so results always match the schema. |
| ⚡ **Fast + cheap model** | Defaults to `claude-haiku-4-5` — classification doesn't need a big model. |
| 🔑 **Least privilege** | Requests Gmail's read-only scope unless `--apply` needs the modify scope. |

---

## Quick start (30 seconds, no email account)

```bash
cd tools/email-triage
pip install -r requirements.txt

# Try it on bundled sample emails — needs a backend (see below)
python triage.py --demo
```

`--demo` runs against a sample inbox, so you can see the output before wiring up Gmail.

---

## Pick a backend

The tool auto-detects one; force it with `--backend claude|ollama`.

### Option A — Claude (best quality)
```bash
export ANTHROPIC_API_KEY=sk-ant-...        # Windows PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."
python triage.py --demo
```

### Option B — Ollama (free, private, offline)
```bash
# Install from https://ollama.com, then:
ollama pull llama3.2
python triage.py --demo --backend ollama
```
The Ollama backend talks to your local server over the standard library — no extra
Python packages, and nothing leaves your machine.

---

## Connect your Gmail

1. In [Google Cloud Console](https://console.cloud.google.com/): create a project →
   enable the **Gmail API** → create an **OAuth client ID** of type **Desktop app**.
2. Download the client JSON, save it here as `credentials.json`.
3. Run it — a browser opens once for consent; a token is cached locally afterward.

```bash
python triage.py                 # read-only: fetch unread, classify, print + report
python triage.py --max 50        # sort up to 50 unread
python triage.py --apply         # also add Gmail labels (dry-run + confirm first)
python triage.py --apply --yes   # skip the confirmation prompt
```

With `--apply`, labels are created under a `Triage/` parent (e.g. `Triage/Urgent`,
`Triage/Newsletter`). It **only ever adds labels** — it never deletes, archives, or
marks anything read.

---

## Categories

| | Category | What lands here |
|---|---|---|
| 🔴 | **Urgent** | Time-sensitive, real consequences if ignored today |
| 🟠 | **Action** | Needs a reply or task from you, not urgent |
| 🔵 | **FYI** | Informational, no action needed |
| 📰 | **Newsletter** | Subscribed digests and roundups |
| 🛍️ | **Promotion** | Marketing and sales |
| 🧾 | **Receipt** | Orders, invoices, shipping confirmations |
| 💬 | **Social** | Social-network notifications |
| 🗑️ | **Junk** | Likely spam / cold outreach |

Edit the taxonomy in [`email_triage/config.py`](email_triage/config.py) — add a category
or reword a description and both backends pick it up automatically.

---

## How it works

```
Gmail unread ──▶ classifier ──▶ verdicts {category, priority, reason} ──▶ digest
                    │                                                        │
              Claude / Ollama                                    terminal + markdown
                                                                          │
                                                          (--apply) ──▶ Gmail labels
```

- **`config.py`** — the category taxonomy and all settings (single source of truth).
- **`classifier.py`** — both backends behind one `classify()` call. The Claude path
  uses `messages.parse()` with a Pydantic schema and a `cache_control` system prompt.
- **`gmail_client.py`** — OAuth, fetching unread, and label application.
- **`digest.py`** — the terminal report and the markdown file.
- **`cli.py`** — argument parsing and orchestration.

### A note on prompt caching

The taxonomy system prompt carries a `cache_control` breakpoint. Caching only kicks
in once the cached prefix exceeds the model's minimum (~4096 tokens on Haiku), so for
the current compact taxonomy it's effectively a no-op — included because it's the
correct pattern and starts paying off the moment you grow the prompt with few-shot
examples. Run with `-v` to see `cache_read` token counts.

---

## Flags

| Flag | Effect |
|---|---|
| `--demo` | Use bundled sample emails (no Gmail/credentials). |
| `--max N` | Fetch up to N unread (default 25). |
| `--backend auto\|claude\|ollama` | Choose the classifier (default: auto-detect). |
| `--apply` | Add Gmail labels (dry-run preview + confirm). |
| `--yes` | Skip the `--apply` confirmation. |
| `--report PATH` / `--no-report` | Markdown report path / disable it. |
| `-v` | Show backend and token-usage details. |

---

## Limitations (honest list)

- Classifies from sender + subject + snippet, not full bodies — fast and cheap, but
  it can misjudge a vague subject line.
- No persistent memory of past decisions yet (see the [Frontier](../../README.md#-the-frontier-what-doesnt-exist-well-yet)
  section of the main list — durable memory is gap #1).
- Gmail only. IMAP support would be a welcome PR.

PRs welcome — see the repo [CONTRIBUTING](../../CONTRIBUTING.md).
