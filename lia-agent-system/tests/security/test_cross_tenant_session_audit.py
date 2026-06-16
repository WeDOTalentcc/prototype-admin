"""Sentinela canônica para `app.shared.admin.cross_tenant_session` (Task #1148).

Cobre as invariantes da ADR-030 v2 §4:

1. **PermissionError** quando o caller não passou pelo `require_superadmin`
   (ContextVar marker ausente) — o módulo nunca abre conexão DB.
2. **Audit-log emitido** (start + end) a cada uso bem-sucedido.
3. **`RESET ROLE` garantido** mesmo se o bloco `async with` levantar — a
   exceção original é propagada e o RESET é executado.
4. **`PermissionError` antes do `__aenter__`** quando o gate falha.
5. **Métrica Prometheus** `lia_cross_tenant_session_bypass_total{reason}`
   é incrementada uma vez por uso.

Os testes usam um fake `AsyncSessionLocal` que apenas registra os SQL
emitidos — eles não tocam Postgres real (rodam offline em CI).
"""

from __future__ import annotations

import re
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any

import pytest

from app.shared.admin import cross_tenant_session as ctm


# ─────────────────────────────────────────────────────────────────────────────
# Fake session — captures the sequence of SQL strings executed on it.
# ─────────────────────────────────────────────────────────────────────────────
class _FakeSession:
    def __init__(self) -> None:
        self.executed: list[tuple[str, dict | None]] = []
        self.committed: int = 0
        self.closed: bool = False

    async def execute(self, stmt: Any, params: dict | None = None) -> Any:
        # SQLAlchemy ``text(...)`` objects expose the raw string via ``.text``.
        raw = getattr(stmt, "text", str(stmt))
        self.executed.append((raw, params))
        return SimpleNamespace(scalar=lambda: None)

    async def commit(self) -> None:
        self.committed += 1

    async def close(self) -> None:
        self.closed = True

    @property
    def role_ops(self) -> list[str]:
        """SET/RESET ROLE statements only (for ordering assertions)."""
        return [
            s for s, _ in self.executed
            if re.search(r"\b(SET ROLE|RESET ROLE)\b", s, re.IGNORECASE)
        ]

    @property
    def audit_inserts(self) -> list[dict]:
        """Parameter dicts of INSERT INTO audit_logs statements."""
        return [
            p or {} for s, p in self.executed
            if "INSERT INTO audit_logs" in s
        ]


@pytest.fixture
def fake_session(monkeypatch: pytest.MonkeyPatch) -> _FakeSession:
    """Patch ``AsyncSessionLocal`` so the helper opens our fake session."""
    session = _FakeSession()

    # Patch the lazy import target inside cross_tenant_session.
    import app.core.database as core_db

    monkeypatch.setattr(core_db, "AsyncSessionLocal", lambda: session, raising=False)
    return session


@pytest.fixture(autouse=True)
def _reset_marker_between_tests():
    """Reset the ContextVar between tests so leakage can't mask a failure."""
    ctm._clear_superadmin_marker()
    yield
    ctm._clear_superadmin_marker()


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 1 + 4 — PermissionError raised BEFORE any DB op when marker unset.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_raises_permission_error_when_not_superadmin(monkeypatch: pytest.MonkeyPatch) -> None:
    # Make sure even if a session were opened, we'd notice.
    sentinel = _FakeSession()
    import app.core.database as core_db
    monkeypatch.setattr(core_db, "AsyncSessionLocal", lambda: sentinel, raising=False)

    with pytest.raises(PermissionError):
        async with ctm.cross_tenant_session(reason="x", audit_user_id="u"):
            pytest.fail("body must not execute")

    assert sentinel.executed == [], "no SQL must run when gate fails"
    assert sentinel.committed == 0


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 2 — audit start + end rows emitted; metric incremented.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_emits_audit_start_and_end_and_metric(fake_session: _FakeSession) -> None:
    ctm._mark_superadmin(user_id="admin-1", company_id="00000000-0000-4000-a000-000000000001")

    before = _metric_value("monthly_billing_report")

    async with ctm.cross_tenant_session(
        reason="monthly_billing_report", audit_user_id="admin-1"
    ) as db:
        assert db is fake_session

    inserts = fake_session.audit_inserts
    assert len(inserts) == 2, f"expected 2 audit rows (start+end), got {len(inserts)}"
    assert inserts[0]["action"] == "start"
    assert inserts[1]["action"] == "end"
    for row in inserts:
        assert row["decision_type"] == ctm.CROSS_TENANT_BYPASS_EVENT_TYPE
        assert row["agent_name"] == "cross_tenant_session"
        assert row["session_id"] == "admin-1"
        assert "monthly_billing_report" in row["criteria_used"]

    # Metric incremented exactly once for this reason.
    after = _metric_value("monthly_billing_report")
    assert after - before == pytest.approx(1.0)


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 3 — RESET ROLE runs even when wrapped block raises.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_reset_role_runs_when_block_raises(fake_session: _FakeSession) -> None:
    ctm._mark_superadmin(user_id="admin-1", company_id="00000000-0000-4000-a000-000000000001")

    class _Boom(RuntimeError):
        pass

    with pytest.raises(_Boom):
        async with ctm.cross_tenant_session(reason="export", audit_user_id="admin-1"):
            raise _Boom("kaboom")

    role_ops = fake_session.role_ops
    assert any("SET ROLE postgres" in op for op in role_ops), role_ops
    assert any("RESET ROLE" in op for op in role_ops), role_ops
    # SET must come before the final RESET.
    set_idx = next(i for i, o in enumerate(role_ops) if "SET ROLE postgres" in o)
    reset_idx = next(i for i, o in enumerate(role_ops) if "RESET ROLE" in o)
    assert reset_idx > set_idx

    # End audit row still attempted even on exception.
    inserts = fake_session.audit_inserts
    actions = [r["action"] for r in inserts]
    assert "start" in actions
    assert "end" in actions

    assert fake_session.closed is True


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 5 — require_superadmin gate (role / is_superadmin attr).
# ─────────────────────────────────────────────────────────────────────────────
def test_is_superadmin_truth_table() -> None:
    # is_superadmin attribute beats role.
    u = SimpleNamespace(is_superadmin=True, role="recruiter")
    assert ctm._is_superadmin_user(u) is True

    # Tenant-scoped admin is NOT enough.
    u2 = SimpleNamespace(role="admin", is_superadmin=False)
    assert ctm._is_superadmin_user(u2) is False

    # platform_admin / super_admin role labels count.
    u3 = SimpleNamespace(role="platform_admin")
    assert ctm._is_superadmin_user(u3) is True

    u4 = SimpleNamespace(role=SimpleNamespace(value="super_admin"))
    assert ctm._is_superadmin_user(u4) is True

    # Plain user.
    assert ctm._is_superadmin_user(SimpleNamespace(role="viewer")) is False


@pytest.mark.asyncio
async def test_require_superadmin_rejects_non_superadmin() -> None:
    from fastapi import HTTPException

    plain = SimpleNamespace(id="u1", role="admin", company_id="c1", is_superadmin=False)
    with pytest.raises(HTTPException) as exc_info:
        await ctm.require_superadmin(current_user=plain)
    assert exc_info.value.status_code == 403
    # Marker MUST NOT be set on failure.
    assert ctm._SUPERADMIN_CTX.get() is None


@pytest.mark.asyncio
async def test_require_superadmin_sets_marker_for_superadmin() -> None:
    boss = SimpleNamespace(id="boss-1", role="platform_admin", company_id="c-boss")
    out = await ctm.require_superadmin(current_user=boss)
    assert out is boss
    marker = ctm._SUPERADMIN_CTX.get()
    assert marker == {"user_id": "boss-1", "company_id": "c-boss"}


# ─────────────────────────────────────────────────────────────────────────────
# Invariant — input validation.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_rejects_audit_user_id_mismatch_anti_spoofing(
    fake_session: _FakeSession,
) -> None:
    """The caller MUST pass the same user_id that ``require_superadmin`` set.

    A handler that tries to forge audit attribution by passing a different
    ``audit_user_id`` is refused with ``PermissionError`` before any DB or
    role-switch happens.
    """
    ctm._mark_superadmin(user_id="boss-1", company_id="c-boss")

    with pytest.raises(PermissionError, match="anti-spoofing"):
        async with ctm.cross_tenant_session(
            reason="export", audit_user_id="some-other-user"
        ):
            pytest.fail("body must not execute")

    assert fake_session.executed == [], "no SQL must run when spoofing is detected"
    assert fake_session.committed == 0


@pytest.mark.asyncio
async def test_rejects_empty_reason_or_actor(fake_session: _FakeSession) -> None:
    ctm._mark_superadmin(user_id="u", company_id="c")

    with pytest.raises(ValueError):
        async with ctm.cross_tenant_session(reason="", audit_user_id="u"):
            pass

    with pytest.raises(ValueError):
        async with ctm.cross_tenant_session(reason="r", audit_user_id=""):
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Invariant — no SET ROLE postgres outside the canonical helper.
# ─────────────────────────────────────────────────────────────────────────────
def test_no_raw_set_role_postgres_outside_canonical_helper() -> None:
    """Any `SET ROLE postgres` in app/libs Python code MUST come from
    ``app/shared/admin/cross_tenant_session.py``. A second call-site would
    silently bypass RLS with no audit trail."""
    import pathlib
    import subprocess

    root = pathlib.Path(__file__).resolve().parents[2]  # lia-agent-system/
    res = subprocess.run(
        [
            "grep", "-RIln", "--include=*.py",
            "--exclude=cross_tenant_session.py",
            "SET ROLE postgres",
            str(root / "app"), str(root / "libs"),
        ],
        capture_output=True, text=True,
    )
    assert res.returncode == 1, (
        "`SET ROLE postgres` must only be issued from the canonical "
        f"cross_tenant_session helper:\n{res.stdout}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _metric_value(reason: str) -> float:
    counter = ctm._BYPASS_COUNTER
    if counter is None:
        return 0.0
    try:
        return counter.labels(reason=reason)._value.get()  # type: ignore[attr-defined]
    except Exception:
        return 0.0
