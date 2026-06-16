#!/usr/bin/env python3
"""
SENSOR (harness-engineering): validate required environment variables.

Catches the class of bugs we hit in 2026-05-20: a critical env var (e.g.
``FIELD_ENCRYPTION_KEY``) is missing or malformed, but the app boots
"successfully" and only fails at the first request that needs the var
— which manifests as HTTP 500 minutes/hours later instead of an obvious
startup error.

This is ADR-AUTH-001: fail at startup, not on first user request.

Usage:
  python3 scripts/check_required_env.py             # check current shell env
  python3 scripts/check_required_env.py --strict    # also enforce min lengths
  python3 scripts/check_required_env.py --dotenv .env  # also load .env first

Exit codes:
  0 — all required vars present and (in --strict mode) within expected shape
  1 — at least one required var missing or malformed
  2 — usage error (e.g. .env file not found)

Output format: each violation includes the var name, the failure mode, AND
a concrete fix command. Designed so an LLM reading the error can self-correct
without consulting external docs.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class EnvRequirement:
    """A single env var check."""
    name: str
    required: bool                  # if False, only checked under --strict
    min_length: int | None          # raw byte/char length lower bound
    base64_fernet: bool             # must decode as Fernet key (44-char base64)
    description: str
    fix_hint: str                   # how to obtain/generate a valid value


REQUIRED_ENV_VARS: tuple[EnvRequirement, ...] = (
    EnvRequirement(
        name="DATABASE_URL",
        required=True,
        min_length=20,
        base64_fernet=False,
        description="Postgres connection string (with +asyncpg for async paths).",
        fix_hint=(
            "Set DATABASE_URL=postgresql+asyncpg://user:pw@host:5432/db in "
            "Replit Secrets. Required for SQLAlchemy + alembic upgrades."
        ),
    ),
    EnvRequirement(
        name="SECRET_KEY",
        required=True,
        min_length=32,
        base64_fernet=False,
        description="JWT signing secret (HS256). Must be ≥32 bytes for RFC 7518.",
        fix_hint=(
            "Generate with: python3 -c \"import secrets; "
            "print(secrets.token_urlsafe(48))\" and set in Replit Secrets."
        ),
    ),
    EnvRequirement(
        name="FIELD_ENCRYPTION_KEY",
        required=True,
        min_length=44,
        base64_fernet=True,
        description=(
            "Fernet symmetric key used by EncryptedFieldMixin for PII columns "
            "(User.email_encrypted, Candidate.cpf, etc). Without this key, any "
            "endpoint hitting get_current_user_or_demo crashes with HTTP 500."
        ),
        fix_hint=(
            "Generate with: python3 -c \"from cryptography.fernet import "
            "Fernet; print(Fernet.generate_key().decode())\" and set in "
            "Replit Secrets. ADR-AUTH-001: app MUST fail startup if missing."
        ),
    ),
    EnvRequirement(
        name="IS_DEVELOPMENT",
        required=False,
        min_length=None,
        base64_fernet=False,
        description=(
            "When 'true', encryption fallback is allowed (PII saved raw). Off "
            "by default for prod safety. Set to 'true' on Replit dev workspaces."
        ),
        fix_hint="Set IS_DEVELOPMENT=true in Replit Secrets for dev/staging workspaces.",
    ),
    EnvRequirement(
        name="REDIS_URL",
        required=False,
        min_length=10,
        base64_fernet=False,
        description="Cache + rate-limiter backend. Falls back to in-memory if missing.",
        fix_hint="Set REDIS_URL=redis://localhost:6379/0 in Replit Secrets.",
    ),
)


def _maybe_load_dotenv(path: str) -> None:
    """Best-effort load of .env without requiring python-dotenv."""
    if not os.path.isfile(path):
        print(f"❌ --dotenv path not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        from dotenv import load_dotenv
        load_dotenv(path, override=False)
    except ImportError:
        # Manual parse (no python-dotenv installed)
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v


def _check_var(req: EnvRequirement, strict: bool) -> str | None:
    """Return None on pass, error string on fail."""
    value = os.environ.get(req.name, "")
    if not value:
        if req.required:
            return (
                f"{req.name} = <UNSET>\n"
                f"  why it matters: {req.description}\n"
                f"  how to fix: {req.fix_hint}"
            )
        return None  # optional + missing = no error

    if req.min_length is not None and len(value) < req.min_length:
        return (
            f"{req.name} = <SET, but only {len(value)} chars; "
            f"need ≥{req.min_length}>\n"
            f"  why it matters: {req.description}\n"
            f"  how to fix: {req.fix_hint}"
        )

    if strict and req.base64_fernet:
        try:
            from cryptography.fernet import Fernet
            Fernet(value.encode() if isinstance(value, str) else value)
        except Exception as exc:
            return (
                f"{req.name} = <SET, but NOT a valid Fernet key: "
                f"{type(exc).__name__}: {exc}>\n"
                f"  why it matters: {req.description}\n"
                f"  how to fix: {req.fix_hint}"
            )
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify required env vars per ADR-AUTH-001.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also validate min_length and Fernet key parseability.",
    )
    parser.add_argument(
        "--dotenv",
        default=None,
        help="Path to a .env file to load before checking.",
    )
    args = parser.parse_args()

    if args.dotenv:
        _maybe_load_dotenv(args.dotenv)

    failures: list[str] = []
    for req in REQUIRED_ENV_VARS:
        err = _check_var(req, args.strict)
        if err:
            failures.append(err)

    if not failures:
        print("✅ All required env vars present (ADR-AUTH-001 holds).")
        return 0

    print(
        f"❌ {len(failures)} required env var(s) missing or malformed.\n"
        f"\nADR-AUTH-001 (CLAUDE.md): app MUST fail at startup, not on the\n"
        f"first request that needs the var. Fix each entry below before\n"
        f"restarting the workflow.\n"
    )
    for i, err in enumerate(failures, start=1):
        print(f"── #{i} ──")
        print(err)
        print()
    print("Re-run: python3 scripts/check_required_env.py --strict")
    return 1


if __name__ == "__main__":
    sys.exit(main())


# ─── Programmatic API (importable from app code) ───────────────────────────

def validate_required_env(strict: bool = True) -> list[str]:
    """
    Validate required env vars. Returns list of error strings (empty = OK).

    Intended for use from FastAPI lifespan/startup hooks to fail-fast when
    canonical vars are missing (ADR-AUTH-001).

    Example:
        from scripts.check_required_env import validate_or_raise
        validate_or_raise(strict=True)  # raises RuntimeError on any failure
    """
    failures: list[str] = []
    for req in REQUIRED_ENV_VARS:
        err = _check_var(req, strict)
        if err:
            failures.append(err)
    return failures


def validate_or_raise(strict: bool = True) -> None:
    """
    Validate required env vars; raise RuntimeError with all violations if any.

    Per ADR-AUTH-001 (CLAUDE.md): app MUST fail at startup, not on first
    request that hits the missing var.
    """
    failures = validate_required_env(strict=strict)
    if not failures:
        return
    msg_parts = [
        f"{len(failures)} required env var(s) missing or malformed "
        f"(ADR-AUTH-001 startup check):\n"
    ]
    for i, err in enumerate(failures, start=1):
        msg_parts.append(f"── #{i} ──\n{err}\n")
    raise RuntimeError("\n".join(msg_parts))
