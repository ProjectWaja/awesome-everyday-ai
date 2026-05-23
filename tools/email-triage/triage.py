#!/usr/bin/env python3
"""Convenience entry point so you can run `python triage.py` from this folder.

Equivalent to `python -m email_triage`.
"""

from email_triage.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
