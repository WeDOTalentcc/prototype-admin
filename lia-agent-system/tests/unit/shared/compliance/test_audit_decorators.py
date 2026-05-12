"""PR4 (Task #1004) — Unit tests do wrapper canônico
``audit_company_change`` (Inegociável #6 / SOX / ISO 27001 / EU AI Act).

Modelo de execução: outbox de duas fases + transação atômica do outcome.

  * ``__aenter__`` emite ``decision="initiated"`` (intent) em sessão
    INDEPENDENTE (committed). Se a infra de audit estiver indisponível,
    RuntimeError é levantado AQUI — o bloco protegido nunca executa.
  * ``__aenter__`` então abre uma sessão COMPARTILHADA (``audit.session``)
    para o body usar nos business writes (sem commit).
  * ``__aexit__`` (sucesso) emite ``decision=<outcome>`` na MESMA session
    do body via ``log_decision_in_session`` e faz ``session.commit()`` —
    business writes + outcome row commitam atomicamente. Falha aqui
    levanta RuntimeError + faz rollback.
  * ``__aexit__`` (body raised) faz rollback do business e emite
    ``decision="exception"`` em sessão independente.

Cobertura: idem ao PR4 anterior, mas validando o novo fluxo atômico.
"""
from __future__ import annotations

from typing import Any

import pytest

from app.shared.compliance import audit_decorators as ad


class _AuditCalls:
    """Captura de chamadas. ``raise_on`` 1-indexed."""

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


class _FakeSession:
    """Mock async session: exibe a API que o wrapper precisa
    (commit/rollback/add/flush/execute) como no-ops."""

    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    def add(self, _obj: Any) -> None:  # pragma: no cover
        pass

    async def flush(self) -> None:  # pragma: no cover
        pass

    async def execute(self, *_a: Any, **_kw: Any) -> None:  # pragma: no cover
        return None


class _FakeSessionCM:
    def __init__(self, session: _FakeSession) -> None:
        self._session = session

    async def __aenter__(self) -> _FakeSession:
        return self._session

    async def __aexit__(self, *_exc: Any) -> bool:
        return False


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch):
    monkeypatch.delenv("LIA_DISABLE_COMPANY_AUDIT", raising=False)
    yield


def _patch_audit_service(monkeypatch, capture: _AuditCalls) -> _FakeSession:
    """Substitui ``AuditService`` + ``AsyncSessionLocal`` + ``_bind_tenant``
    no namespace usado pelo decorator. Retorna a fake session que o
    wrapper irá compartilhar com o body."""
    import app.shared.compliance.audit_service as audit_mod

    fake_session = _FakeSession()

    class _Stub:
        def __init__(self) -> None:
            self._capture = capture

        async def log_decision(self, **kwargs: Any) -> None:
            await self._capture.log_decision(**kwargs)

        async def log_decision_in_session(self, _session, **kwargs: Any) -> None:
            # Mesma captura — atomicidade real é validada no integration test.
            await self._capture.log_decision(**kwargs)

    def _fake_session_local() -> _FakeSessionCM:
        return _FakeSessionCM(fake_session)

    async def _noop_bind_tenant(_session, _company_id):
        return None

    monkeypatch.setattr(audit_mod, "AuditService", _Stub)
    monkeypatch.setattr(audit_mod, "AsyncSessionLocal", _fake_session_local)
    monkeypatch.setattr(audit_mod, "_bind_tenant", _noop_bind_tenant)
    return fake_session


@pytest.mark.asyncio
async def test_success_emits_intent_and_completed_with_canonical_payload(monkeypatch):
    capture = _AuditCalls()
    session = _patch_audit_service(monkeypatch, capture)

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
    assert intent["decision"] == "initiated"
    assert outcome["decision"] == "completed"
    assert "before={\"value\": \"Old Co\"}" in outcome["reasoning"]
    assert "after={\"value\": \"New Co\"}" in outcome["reasoning"]
    assert any("target_id=co-1::profile.name" in r for r in outcome["reasoning"])
    assert any("target_id:co-1::profile.name" in c for c in outcome["criteria_used"])
    intent_trace = next(r for r in intent["reasoning"] if r.startswith("trace_id="))
    outcome_trace = next(r for r in outcome["reasoning"] if r.startswith("trace_id="))
    assert intent_trace == outcome_trace
    # Atomicidade: o wrapper commitou a session compartilhada (business
    # + outcome juntos) e não fez rollback.
    assert session.commits == 1
    assert session.rollbacks == 0


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
    """Storage indisponível no entry → bloco NUNCA executa, body session
    nunca é aberta (outbox transactional pattern)."""
    capture = _AuditCalls(raise_exc=RuntimeError("DB down"), raise_on=[1])
    session = _patch_audit_service(monkeypatch, capture)

    business_executed = False

    with pytest.raises(RuntimeError, match="audit storage unavailable"):
        async with ad.audit_company_change(
            action="save_company_field",
            company_id="co-1",
            actor="user-1",
            target_table="company_profiles",
            metadata={},
        ) as a:
            business_executed = True
            a.set_result({"success": True})

    assert business_executed is False
    assert len(capture.calls) == 1
    assert session.commits == 0
    assert session.rollbacks == 0


@pytest.mark.asyncio
async def test_outcome_failure_raises_and_rolls_back_business(monkeypatch):
    """Intent OK; outcome falha; bloco completou → RuntimeError no exit
    + rollback ATÔMICO da session compartilhada (business writes
    cancelados — fail-CLOSED transacional real)."""
    capture = _AuditCalls(raise_exc=RuntimeError("DB down on outcome"), raise_on=[2])
    session = _patch_audit_service(monkeypatch, capture)

    with pytest.raises(RuntimeError, match="outcome audit failed"):
        async with ad.audit_company_change(
            action="save_company_field",
            company_id="co-1",
            actor="user-1",
            target_table="company_profiles",
            metadata={},
        ) as a:
            a.set_result({"success": True})

    assert [c["decision"] for c in capture.calls] == ["initiated", "completed"]
    # Atomic rollback: business writes da session compartilhada foram
    # cancelados quando a outcome row falhou.
    assert session.commits == 0
    assert session.rollbacks == 1


@pytest.mark.asyncio
async def test_outcome_failure_does_not_mask_block_exception(monkeypatch):
    """Intent OK; bloco raising; outcome também falha → propaga ORIGINAL.
    Body session é rolled back; outcome 'exception' tentado em sessão
    independente (e falha silenciosamente — log only)."""
    capture = _AuditCalls(raise_exc=RuntimeError("audit down"), raise_on=[2])
    session = _patch_audit_service(monkeypatch, capture)

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

    assert [c["decision"] for c in capture.calls] == ["initiated", "exception"]
    assert session.rollbacks == 1
    assert session.commits == 0


@pytest.mark.asyncio
async def test_disable_flag_skips_both_phases(monkeypatch):
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
    capture = _AuditCalls()
    session = _patch_audit_service(monkeypatch, capture)

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
    # Read-only não commita session compartilhada (sem mutação).
    assert session.commits == 0


@pytest.mark.asyncio
async def test_missing_company_id_logs_and_skips(monkeypatch):
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
    assert any("target_id=∅" in r for r in intent["reasoning"])
    assert any("target_id=policy-uuid-99" in r for r in outcome["reasoning"])
