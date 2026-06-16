"""
Bootstrap Admin User — Idempotent upsert of a password-login admin user.

Why this exists
---------------
The published platform runs in email/password login mode (WorkOS SSO is not
configured) but no valid login user exists:

  - The demo auto-login is disabled in production (gated by ``APP_ENV``).
  - ``POST /api/v1/auth/login`` reads the auth table ``users``
    (``app/auth/models.py``, with ``password_hash`` + ``is_active``).
  - The full-platform seed only writes to the DIFFERENT ``client_users``
    table and without a password, so there is no row to authenticate against.
  - Password recovery is unavailable because the email provider runs in mock
    mode in production.

This command creates (or updates, if it already exists) an ``admin`` user in
the ``users`` table so the owner can log in via the normal email/password form.

Security
--------
  - Email and password are read from environment variables / secrets, NEVER
    hardcoded.
  - Reuses the canonical password hashing utility (``app/auth/security.py``).
  - Idempotent: re-running updates the SAME user's password instead of
    duplicating or breaking.

Required environment variables
------------------------------
  ADMIN_BOOTSTRAP_EMAIL     — admin login email (required)
  ADMIN_BOOTSTRAP_PASSWORD  — admin login password (required, min 8 chars)

Optional
--------
  ADMIN_BOOTSTRAP_NAME       — display name (default: "Platform Admin")
  ADMIN_BOOTSTRAP_COMPANY_ID — tenant UUID (default: canonical Demo Company)

Usage
-----
Local / dev (uses the configured DATABASE_URL)::

    cd lia-agent-system
    export ADMIN_BOOTSTRAP_EMAIL="owner@example.com"
    export ADMIN_BOOTSTRAP_PASSWORD="a-strong-password"
    python -m scripts.bootstrap_admin_user

Against production (one-off), point DATABASE_URL at the production database for
this single invocation only::

    DATABASE_URL="<prod-database-url>" \
    ADMIN_BOOTSTRAP_EMAIL="owner@example.com" \
    ADMIN_BOOTSTRAP_PASSWORD="a-strong-password" \
    python -m scripts.bootstrap_admin_user
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from lia_config.database import AsyncSessionLocal

from app.auth.models import User, UserRole
from app.auth.security import get_password_hash
from app.repositories.auth_user_repository import UserRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bootstrap_admin_user")

CANONICAL_DEMO_UUID = "00000000-0000-4000-a000-000000000001"
MIN_PASSWORD_LENGTH = 8


def _read_config() -> dict:
    """Read and validate admin config from the environment. Fail loud."""
    email = (os.environ.get("ADMIN_BOOTSTRAP_EMAIL") or "").strip()
    password = os.environ.get("ADMIN_BOOTSTRAP_PASSWORD") or ""
    name = (os.environ.get("ADMIN_BOOTSTRAP_NAME") or "Platform Admin").strip()
    company_id = (os.environ.get("ADMIN_BOOTSTRAP_COMPANY_ID") or CANONICAL_DEMO_UUID).strip()

    missing = []
    if not email:
        missing.append("ADMIN_BOOTSTRAP_EMAIL")
    if not password:
        missing.append("ADMIN_BOOTSTRAP_PASSWORD")
    if missing:
        raise SystemExit(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". Set them (as secrets) before running this command."
        )

    if len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(
            f"ADMIN_BOOTSTRAP_PASSWORD must be at least {MIN_PASSWORD_LENGTH} characters."
        )

    return {"email": email, "password": password, "name": name, "company_id": company_id}


async def _email_column_is_not_null(db: AsyncSession) -> bool:
    """Return True if the legacy ``users.email`` column still has a NOT NULL
    constraint.

    The PII encryption mixin nulls the legacy plaintext ``email`` column on
    write (the value lives encrypted in ``email_encrypted`` + hashed in
    ``email_hash``). On databases where migration backfill has not yet relaxed
    the column to nullable, that NULL write violates the constraint. When that
    is the case we keep the plaintext column populated (the same state as
    pre-migration rows), which ``UserRepository.get_by_email`` still resolves.
    """
    result = await db.execute(
        text(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_name = 'users' AND column_name = 'email'"
        )
    )
    row = result.fetchone()
    if row is None:
        return False
    return str(row[0]).upper() == "NO"


async def bootstrap_admin_user(cfg: dict) -> dict:
    """Create or update the admin user in the ``users`` table.

    Returns a small summary dict for logging (no secrets).
    """
    async with AsyncSessionLocal() as db:
        repo = UserRepository(db)
        password_hash = get_password_hash(cfg["password"])

        existing = await repo.get_by_email(cfg["email"])
        if existing is not None:
            await repo.update_by_instance(
                existing,
                {
                    "password_hash": password_hash,
                    "role": UserRole.admin,
                    "is_active": True,
                    "company_id": cfg["company_id"],
                    "name": cfg["name"],
                },
            )
            return {"action": "updated", "id": str(existing.id)}

        user = User(
            name=cfg["name"],
            password_hash=password_hash,
            role=UserRole.admin,
            is_active=True,
            company_id=cfg["company_id"],
            email_verified=True,
        )
        # Setting the hybrid ``email`` encrypts the value, computes ``email_hash``
        # and nulls the legacy plaintext column.
        user.email = cfg["email"]
        if await _email_column_is_not_null(db):
            # Legacy column still required — keep plaintext populated so the
            # INSERT satisfies the NOT NULL constraint (pre-migration row shape).
            user._email_raw = cfg["email"]
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {"action": "created", "id": str(user.id)}


async def _main() -> None:
    cfg = _read_config()
    result = await bootstrap_admin_user(cfg)
    logger.info(
        "Admin user %s (id=%s, email=%s, role=admin, is_active=true, company_id=%s)",
        result["action"],
        result["id"],
        cfg["email"],
        cfg["company_id"],
    )


if __name__ == "__main__":
    asyncio.run(_main())
