"""PR4 (Task #1004) — Unit tests do wrapper canônico
``audit_company_change`` (Inegociável #6 / SOX / ISO 27001 / EU AI Act).

Cobertura:

  1. Sucesso: AuditService recebe ``decision="completed"`` quando o
     bloco protegido retorna ``{"success": True}``.
  2. Bloqueio fairness: bloco retorna ``{"success": False,
     "reason": "fairness_violation"}`` → ``decision="blocked_fairness"``.
  3. Falha do AuditService (fail-CLOSED): ``log_decision`` raise →
     wrapper raise ``RuntimeError`` quando o bloco completou OK.
  4. Falha do AuditService quando bloco também levantou: a exceção
     ORIGINAL do bloco propaga (audit_exc fica em logs).
  5. Bypass via ``LIA_DISABLE_COMPANY_AUDIT=1``: AuditService NÃO é
     chamado e o wrapper NÃO levanta mesmo se algo dentro falhar
     no caminho do audit.
  6. Read-only: ``decision="read"`` quando ``read_only=True``.

Roda offline (mocka ``AuditService.log_decision`` via monkeypatch).
"""
from __future__ import annotations

from typing import Any

import pytest

from app.shared.compliance import audit_decorators as ad


class _AuditCalls:
    """Capture helper — coleta chamadas a ``log_decision`` para asserts."""

    def __init__(self, *, raise_exc: Exception | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._raise_exc = raise_exc

    async def log_decision(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)
        if self._raise_exc is not None:
            raise self._raise_exc


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch):
    """Garante bypass DESLIGADO entre testes (default seguro)."""
    monkeypatch.delenv("LIA_DISABLE_COMPANY_AUDIT", raising=False)
    yield


def _patch_audit_service(monkeypatch, capture: _AuditCalls) -> None:
    """Substitui ``AuditService`` no namespace importado pelo decorator."""
    import app.shared.compliance.audit_service as audit_mod

    class _Stub:
        def __init__(self) -> None:
            self._capture = capture

        async def log_decision(self, **kwargs: Any) -> None:
            await self._capture.log_decision(**kwargs)

    monkeypatch.setattr(audit_mod, "AuditService", _Stub)


@pytest.mark.asyncio
async def test_success_path_emits_completed():
    """Caminho feliz: bloco retorna success=True → decision=completed."""
    capture = _AuditCalls()

    async def _run(monkey):
        _patch_audit_service(monkey, capture)
        async with ad.audit_company_change(
            action="save_company_field",
            company_id="co-1",
            actor="user-42",
            target_table="company_profiles",
            metadata={"section": "profile", "field": "name"},
        ) as a:
            a.set_result({"success": True, "data": {}})

    with pytest.MonkeyPatch.context() as mp:
        await _run(mp)

    assert len(capture.calls) == 1
    call = capture.calls[0]
    assert call["company_id"] == "co-1"
    assert call["action"] == "save_company_field"
    assert call["decision"] == "completed"
    assert call["agent_name"] == "company_settings_tools"
    assert "actor=user-42" in call["reasoning"]
    assert any("target_table:company_profiles" in c for c in call["criteria_used"])


@pytest.mark.asyncio
async def test_fairness_violation_outcome():
    """Bloco devolve ``reason='fairness_violation'`` → decision=blocked_fairness."""
    capture = _AuditCalls()

    with pytest.MonkeyPatch.context() as mp:
        _patch_audit_service(mp, capture)
        async with ad.audit_company_change(
            action="save_hiring_policy",
            company_id="co-1",
            actor="user-1",
            target_table="company_hiring_policies",
            metadata={"rule_keys": ["communication_rules"]},
        ) as a:
            a.set_result({
                "success": False,
                "reason": "fairness_violation",
                "offending_field": "lia_tone",
            })

    assert capture.calls[0]["decision"] == "blocked_fairness"


@pytest.mark.asyncio
async def test_audit_failure_raises_when_block_succeeded():
    """Fail-CLOSED: AuditService raise + bloco OK → wrapper raise RuntimeError."""
    capture = _AuditCalls(raise_exc=RuntimeError("DB down"))

    with pytest.MonkeyPatch.context() as mp:
        _patch_audit_service(mp, capture)
        with pytest.raises(RuntimeError, match="audit_company_change"):
            async with ad.audit_company_change(
                action="save_company_field",
                company_id="co-1",
                actor="user-1",
                target_table="company_profiles",
                metadata={},
            ) as a:
                a.set_result({"success": True})

    assert len(capture.calls) == 1


@pytest.mark.asyncio
async def test_audit_failure_does_not_mask_block_exception():
    """Quando o bloco protegido já estava raising, propaga a ORIGINAL —
    falha do audit fica em log mas NÃO mascara a exceção principal."""
    capture = _AuditCalls(raise_exc=RuntimeError("audit down"))

    class _BizError(Exception):
        pass

    with pytest.MonkeyPatch.context() as mp:
        _patch_audit_service(mp, capture)
        with pytest.raises(_BizError, match="boom"):
            async with ad.audit_company_change(
                action="save_company_field",
                company_id="co-1",
                actor="user-1",
                target_table="company_profiles",
                metadata={},
            ):
                raise _BizError("boom")


@pytest.mark.asyncio
async def test_disable_flag_skips_audit_emission(monkeypatch):
    """LIA_DISABLE_COMPANY_AUDIT=1 → log_decision NÃO é chamado e
    nenhuma exceção sobe mesmo se algo falharia no caminho do audit."""
    monkeypatch.setenv("LIA_DISABLE_COMPANY_AUDIT", "1")
    capture = _AuditCalls(raise_exc=RuntimeError("would fail if called"))
    _patch_audit_service(monkeypatch, capture)

    async with ad.audit_company_change(
        action="save_company_field",
        company_id="co-1",
        actor="user-1",
        target_table="company_profiles",
        metadata={},
    ) as a:
        a.set_result({"success": True})

    assert capture.calls == []
    assert ad.is_company_audit_disabled() is True


@pytest.mark.asyncio
async def test_read_only_outcome_is_read():
    """``read_only=True`` → decision=read (LGPD Art. 37 / ISO A.12.4)."""
    capture = _AuditCalls()

    with pytest.MonkeyPatch.context() as mp:
        _patch_audit_service(mp, capture)
        async with ad.audit_company_change(
            action="check_company_completeness",
            company_id="co-1",
            actor="user-1",
            target_table="company_profiles",
            metadata={},
            read_only=True,
        ) as a:
            a.set_result({"success": True, "overall_pct": 0.8})

    assert capture.calls[0]["decision"] == "read"
    assert any("read_only:True" in c for c in capture.calls[0]["criteria_used"])


@pytest.mark.asyncio
async def test_missing_company_id_logs_and_skips(monkeypatch, caplog):
    """company_id ausente → não emite (RLS impediria) e NÃO levanta —
    o caller já vai falhar por outro motivo."""
    capture = _AuditCalls()
    _patch_audit_service(monkeypatch, capture)

    async with ad.audit_company_change(
        action="save_company_field",
        company_id="",
        actor="user-1",
        target_table="company_profiles",
        metadata={},
    ) as a:
        a.set_result({"success": False, "error": "company_id_required"})

    assert capture.calls == []
