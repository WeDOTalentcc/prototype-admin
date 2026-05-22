"""Contract sensor — CredentialsAccessLog (Wave 3 Camada 3 Item 1, LGPD Art. 37).

Covers four invariants:
1. Every successful ``get_decrypted_credentials`` writes a log entry
   BEFORE the decrypt op completes.
2. The log entry includes all canonical fields (company_id, accessor_type,
   access_purpose, etc.).
3. Calling ``get_decrypted_credentials`` without ``access_purpose=`` keyword
   raises TypeError (REGRA 4 — no silent fallback).
4. Repository ``log_access`` rejects cross-tenant calls (multi-tenancy
   invariant): empty/None ``company_id`` raises ValueError.

Pure-unit: mocked AsyncSession, no real DB. Integration coverage belongs
under ``tests/integration/``.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.integrations_hub.repositories.credentials_access_log_repository import (
    CredentialsAccessLogRepository,
)
from app.domains.integrations_hub.repositories.integrations_hub_repository import (
    IntegrationsHubRepository,
)


def _make_db_mock() -> MagicMock:
    db = MagicMock()
    # Async methods the repository uses
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock()
    return db


def _make_connection_mock(
    *,
    company_id: uuid.UUID,
    has_encrypted: bool = True,
    has_legacy: bool = False,
) -> MagicMock:
    conn = MagicMock()
    conn.id = uuid.uuid4()
    conn.company_id = company_id
    conn.credentials_encrypted = "gAAAA-fake-fernet-ciphertext" if has_encrypted else None
    conn.credentials_legacy = {"key": "val"} if has_legacy else None
    return conn


# ───────────────────────────────────────────────────────────────────────
# Test 1 — log is created on each decryption attempt
# ───────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_log_created_on_each_decryption(monkeypatch):
    """get_decrypted_credentials must call log_access BEFORE decrypt."""
    company_id = uuid.uuid4()
    db = _make_db_mock()
    conn = _make_connection_mock(company_id=company_id)

    repo = IntegrationsHubRepository(db)

    # Patch the connection-fetch and the actual fernet decryption.
    repo.get_connection_by_id = AsyncMock(return_value=conn)

    # Track call ordering: log_access must happen BEFORE decrypt_credentials.
    call_order: list[str] = []

    async def fake_log_access(self, **kwargs):
        call_order.append("log_access")
        return MagicMock()

    def fake_decrypt(ciphertext):
        call_order.append("decrypt")
        return {"api_key": "decrypted_value"}

    monkeypatch.setattr(
        CredentialsAccessLogRepository, "log_access", fake_log_access
    )
    monkeypatch.setattr(
        "app.domains.integrations_hub.repositories.integrations_hub_repository.decrypt_credentials",
        fake_decrypt,
    )

    result = await repo.get_decrypted_credentials(
        str(conn.id),
        str(company_id),
        access_purpose="webhook_dispatch",
    )

    assert result == {"api_key": "decrypted_value"}
    assert call_order == ["log_access", "decrypt"], (
        f"log_access MUST precede decrypt; got {call_order}"
    )


# ───────────────────────────────────────────────────────────────────────
# Test 2 — log entry includes canonical fields
# ───────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_log_includes_canonical_fields():
    """CredentialsAccessLogRepository.log_access writes all canonical fields."""
    company_id = uuid.uuid4()
    user_id = uuid.uuid4()
    connection_id = uuid.uuid4()
    db = _make_db_mock()

    repo = CredentialsAccessLogRepository(db)
    entry = await repo.log_access(
        company_id=str(company_id),
        integration_connection_id=str(connection_id),
        accessor_user_id=str(user_id),
        accessor_type="human_user",
        access_purpose="manual_test",
        client_ip="192.168.1.1",
        request_id="req-abc-123",
    )

    # db.add must have been called once with the new entry
    assert db.add.call_count == 1
    persisted = db.add.call_args.args[0]
    assert persisted is entry

    # All canonical fields populated
    assert str(entry.company_id) == str(company_id)
    assert str(entry.integration_connection_id) == str(connection_id)
    assert str(entry.accessor_user_id) == str(user_id)
    assert entry.accessor_type == "human_user"
    assert entry.access_purpose == "manual_test"
    assert entry.client_ip == "192.168.1.1"
    assert entry.request_id == "req-abc-123"


# ───────────────────────────────────────────────────────────────────────
# Test 3 — get_decrypted_credentials without access_purpose raises TypeError
# ───────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_decrypted_credentials_fails_without_purpose():
    """REGRA 4 — access_purpose is keyword-only required; omitting raises TypeError."""
    db = _make_db_mock()
    repo = IntegrationsHubRepository(db)

    with pytest.raises(TypeError, match="access_purpose"):
        # access_purpose missing — must NOT silently default to empty
        await repo.get_decrypted_credentials(
            str(uuid.uuid4()), str(uuid.uuid4())
        )


# ───────────────────────────────────────────────────────────────────────
# Test 4 — access log multi-tenancy invariant
# ───────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_access_log_tenant_isolated():
    """log_access REJECTS empty/None company_id (cross-tenant defense)."""
    db = _make_db_mock()
    repo = CredentialsAccessLogRepository(db)

    with pytest.raises(ValueError, match="company_id"):
        await repo.log_access(
            company_id="",
            integration_connection_id=str(uuid.uuid4()),
            accessor_user_id=None,
            accessor_type="system",
            access_purpose="health_check",
        )

    with pytest.raises(ValueError, match="company_id"):
        await repo.log_access(
            company_id=None,  # type: ignore[arg-type]
            integration_connection_id=str(uuid.uuid4()),
            accessor_user_id=None,
            accessor_type="system",
            access_purpose="health_check",
        )


# ───────────────────────────────────────────────────────────────────────
# Bonus invariants — accessor_type whitelist + access_purpose non-empty
# ───────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_log_access_rejects_invalid_accessor_type():
    db = _make_db_mock()
    repo = CredentialsAccessLogRepository(db)

    with pytest.raises(ValueError, match="accessor_type"):
        await repo.log_access(
            company_id=str(uuid.uuid4()),
            integration_connection_id=None,
            accessor_user_id=None,
            accessor_type="hacker",  # not canonical
            access_purpose="manual_test",
        )


@pytest.mark.asyncio
async def test_log_access_rejects_empty_purpose():
    db = _make_db_mock()
    repo = CredentialsAccessLogRepository(db)

    with pytest.raises(ValueError, match="access_purpose"):
        await repo.log_access(
            company_id=str(uuid.uuid4()),
            integration_connection_id=None,
            accessor_user_id=None,
            accessor_type="system",
            access_purpose="   ",  # whitespace-only
        )
