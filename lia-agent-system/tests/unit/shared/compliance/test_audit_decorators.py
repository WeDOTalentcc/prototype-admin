"""PR4 (Task #1004) — Unit tests do wrapper canônico
``audit_company_change`` (Inegociável #6 / SOX / ISO 27001 / EU AI Act).

Modelo de execução: outbox de duas fases.

  * ``__aenter__`` emite ``decision="initiated"`` (intent). Se a infra
    de audit estiver indisponível, RuntimeError é levantado AQUI — o
    bloco protegido nunca executa.
  * ``__aexit__`` emite ``decision=<outcome>`` (completed / failed /
    blocked_fairness / exception / read), com ``before``/``after``/
    ``target_id`` capturados via setters. Falha no outcome é fail-CLOSED
    para o caller (RuntimeError) salvo se o bloco já estava propagando
    exceção (preserva exceção original).

Cobertura:

  1. Sucesso: 2 audit rows (initiated + completed); payload canônico
     ``before/after/target_id`` aparece em ``reasoning``.
  2. Bloqueio fairness: outcome ``blocked_fairness``.
  3. Intent falha → RuntimeError no entry, bloco protegido NÃO executa.
  4. Outcome falha + bloco OK → RuntimeError no exit (fail-CLOSED).
  5. Outcome falha + bloco já raising → exceção ORIGINAL propaga.
  6. Bypass via ``LIA_DISABLE_COMPANY_AUDIT=1`` → nenhuma row, nenhum
     raise.
  7. Read-only → 1 row de outcome ``read`` (sem intent — nada a
     proteger via outbox).
  8. company_id ausente → 0 rows + log error (caller já vai falhar).
  9. ``set_target_id`` durante o bloco aparece no ``reasoning``.

Roda offline (mocka ``AuditService.log_decision`` via monkeypatch).
"""
from __future__ import annotations

from typing import Any

import pytest

from app.shared.compliance import audit_decorators as ad


class _AuditCalls:
    """Capture helper. ``raise_on`` é uma lista 1-indexed de chamadas
    onde levantar (ex.: ``[1]`` = falha só no intent; ``[2]`` = falha
    só no outcome; ``[1, 2]`` = falha em ambas)."""

    def __init__(
        self,
        *,
        raise_exc: Exception | None = None,
        raise_on: list[int] | None = None,
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self._raise_exc = raise_exc
        self._raise_on = set(raise_on or ([1, 2] if raise_exc else []))

    async def log_decision(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)
        if self._raise_exc is not None and len(self.calls) in self._raise_on:
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
async def test_success_emits_intent_and_completed_with_canonical_payload(monkeypatch):
    """Sucesso: 2 rows (initiated + completed) com before/after/target_id."""
    capture = _AuditCalls()
    _patch_audit_service(monkeypatch, capture)

    async with ad.audit_company_change(
        action="save_company_field",
        company_id="co-1",
        actor="user-42",
        target_table="company_profiles",
        target_id="co-1::profile.name",
        metadata={"section": "profile", "field": "name"},
    ) as a:
        a.set_before({"value": "Old Co"})
        a.set_after({"value": "New Co"})
        a.set_result({"success": True, "data": {}})

    assert len(capture.calls) == 2
    intent, outcome = capture.calls
    # Intent
    assert intent["decision"] == "initiated"
    assert intent["company_id"] == "co-1"
    assert intent["action"] == "save_company_field"
    assert any("trace_id=" in r for r in intent["reasoning"])
    # Outcome
    assert outcome["decision"] == "completed"
    assert "before={\"value\": \"Old Co\"}" in outcome["reasoning"]
    assert "after={\"value\": \"New Co\"}" in outcome["reasoning"]
    assert any("target_id=co-1::profile.name" in r for r in outcome["reasoning"])
    assert any("target_id:co-1::profile.name" in c for c in outcome["criteria_used"])
    # Trace ID compartilhado entre as duas rows
    intent_trace = next(r for r in intent["reasoning"] if r.startswith("trace_id="))
    outcome_trace = next(r for r in outcome["reasoning"] if r.startswith("trace_id="))
    assert intent_trace == outcome_trace


@pytest.mark.asyncio
async def test_fairness_violation_outcome(monkeypatch):
    capture = _AuditCalls()
    _patch_audit_service(monkeypatch, capture)

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

    assert [c["decision"] for c in capture.calls] == ["initiated", "blocked_fairness"]


@pytest.mark.asyncio
async def test_intent_failure_aborts_business_block(monkeypatch):
    """Storage de audit indisponível no entry → bloco NUNCA executa.
    Esse é o comportamento "outbox-equivalent": fail-CLOSED transacional
    pra a falha de storage de audit."""
    capture = _AuditCalls(raise_exc=RuntimeError("DB down"), raise_on=[1])
    _patch_audit_service(monkeypatch, capture)

    business_executed = False

    with pytest.raises(RuntimeError, match="storage de audit indisponível"):
        async with ad.audit_company_change(
            action="save_company_field",
            company_id="co-1",
            actor="user-1",
            target_table="company_profiles",
            metadata={},
        ) as a:
            business_executed = True  # nunca alcançado
            a.set_result({"success": True})

    assert business_executed is False
    assert len(capture.calls) == 1  # só o intent falho


@pytest.mark.asyncio
async def test_outcome_failure_raises_when_block_succeeded(monkeypatch):
    """Intent OK; outcome falha; bloco completou → RuntimeError no exit."""
    capture = _AuditCalls(raise_exc=RuntimeError("DB down on outcome"), raise_on=[2])
    _patch_audit_service(monkeypatch, capture)

    with pytest.raises(RuntimeError, match="audit row de outcome"):
        async with ad.audit_company_change(
            action="save_company_field",
            company_id="co-1",
            actor="user-1",
            target_table="company_profiles",
            metadata={},
        ) as a:
            a.set_result({"success": True})

    assert [c["decision"] for c in capture.calls] == ["initiated", "completed"]


@pytest.mark.asyncio
async def test_outcome_failure_does_not_mask_block_exception(monkeypatch):
    """Intent OK; bloco raising; outcome também falha → propaga ORIGINAL."""
    capture = _AuditCalls(raise_exc=RuntimeError("audit down"), raise_on=[2])
    _patch_audit_service(monkeypatch, capture)

    class _BizError(Exception):
        pass

    with pytest.raises(_BizError, match="boom"):
        async with ad.audit_company_change(
            action="save_company_field",
            company_id="co-1",
            actor="user-1",
            target_table="company_profiles",
            metadata={},
        ):
            raise _BizError("boom")

    # Intent emitido + tentativa de outcome (que falhou)
    assert [c["decision"] for c in capture.calls] == ["initiated", "exception"]


@pytest.mark.asyncio
async def test_disable_flag_skips_both_phases(monkeypatch):
    """LIA_DISABLE_COMPANY_AUDIT=1 → 0 rows, sem raise mesmo com stub
    configurado para falhar."""
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
async def test_read_only_skips_intent_emits_read(monkeypatch):
    """``read_only=True``: pula intent (não há mutação a proteger),
    emite só ``decision="read"`` no exit."""
    capture = _AuditCalls()
    _patch_audit_service(monkeypatch, capture)

    async with ad.audit_company_change(
        action="check_company_completeness",
        company_id="co-1",
        actor="user-1",
        target_table="company_profiles",
        metadata={},
        read_only=True,
    ) as a:
        a.set_result({"success": True, "overall_pct": 0.8})

    assert len(capture.calls) == 1
    assert capture.calls[0]["decision"] == "read"
    assert any("read_only:True" in c for c in capture.calls[0]["criteria_used"])


@pytest.mark.asyncio
async def test_missing_company_id_logs_and_skips(monkeypatch):
    """company_id ausente → não emite (RLS impediria) e NÃO levanta."""
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


@pytest.mark.asyncio
async def test_set_target_id_during_block_appears_in_outcome(monkeypatch):
    """``set_target_id`` chamado durante a execução (após criar a row e
    obter PK) deve aparecer no outcome (e no intent só se já era
    conhecido no entry)."""
    capture = _AuditCalls()
    _patch_audit_service(monkeypatch, capture)

    async with ad.audit_company_change(
        action="save_hiring_policy",
        company_id="co-1",
        actor="user-1",
        target_table="company_hiring_policies",
        metadata={},
    ) as a:
        a.set_target_id("policy-uuid-99")
        a.set_result({"success": True})

    intent, outcome = capture.calls
    # Intent foi emitido antes do set_target_id → target_id=∅
    assert any("target_id=∅" in r for r in intent["reasoning"])
    # Outcome reflete o ID descoberto durante a execução
    assert any("target_id=policy-uuid-99" in r for r in outcome["reasoning"])
