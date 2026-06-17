"""PR4 (Task #1004) — Integration test: ``audit_company_change`` realmente
persiste rows em ``audit_logs`` para pelo menos 2 ações distintas.

Levanta uma engine sqlite in-memory que emula a tabela
``audit_logs`` (apenas as colunas exigidas pela ``AuditLog`` ORM model
do `lia-agent-system`). Substitui ``AsyncSessionLocal`` no
``app.shared.compliance.audit_service`` para apontar pra essa engine,
patcha ``_bind_tenant`` (sqlite não tem ``set_config``), e exercita o
wrapper ``audit_company_change`` em DOIS cenários reais:

  * ``save_company_field`` (success) → 2 rows: ``initiated`` + ``completed``
  * ``save_hiring_policy`` (fairness blocked) → 2 rows: ``initiated`` +
    ``blocked_fairness``

Em seguida faz ``SELECT * FROM audit_logs`` direto na engine e valida:

  * 4 rows persistidas no total
  * ``company_id`` correto e isolado por tenant
  * ``action`` igual em intent + outcome (par correlato via ``trace_id``)
  * ``decision`` correto por fase (initiated / completed / blocked_fairness)
  * ``reasoning`` contém ``before``/``after``/``target_id`` quando capturados

Esse teste fecha a finding C4 do code review do PR4: prova de
persistência real em ``audit_logs`` para ≥ 2 tools.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from lia_config.database import Base
from app.models.audit_log import AuditLog
from app.shared.compliance import audit_decorators as ad
from app.shared.compliance import audit_service as audit_svc


@pytest.fixture
async def in_memory_audit_engine(monkeypatch):
    """Engine sqlite in-memory + sessionmaker patched no audit_service.

    Patches:
      * ``app.shared.compliance.audit_service.AsyncSessionLocal`` →
        sessionmaker dessa engine
      * ``app.shared.compliance.audit_service._bind_tenant`` → no-op
        (sqlite não suporta ``SELECT set_config(...)``)
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        # Cria APENAS a tabela audit_logs — Base.metadata tem outras
        # tabelas com tipos pg-only (UUID, JSONB) que não rodam em
        # sqlite. AuditLog usa JSON genérico → portável.
        await conn.run_sync(lambda sync_conn: AuditLog.__table__.create(sync_conn))

    SessionMaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def _noop_bind_tenant(session, company_id):
        return None

    monkeypatch.setattr(audit_svc, "AsyncSessionLocal", SessionMaker)
    monkeypatch.setattr(audit_svc, "_bind_tenant", _noop_bind_tenant)
    monkeypatch.delenv("LIA_DISABLE_COMPANY_AUDIT", raising=False)

    yield engine, SessionMaker

    await engine.dispose()


@pytest.mark.asyncio
async def test_pr4_persists_audit_rows_for_two_tools(in_memory_audit_engine):
    """End-to-end: wrapper exerce AuditService → SQLAlchemy → sqlite."""
    engine, SessionMaker = in_memory_audit_engine

    # Tool 1: save_company_field success
    async with ad.audit_company_change(
        action="save_company_field",
        company_id="co-acme",
        actor="user-42",
        target_table="company_profiles",
        target_id="co-acme::profile.name",
        metadata={"section": "profile", "field": "name"},
    ) as a1:
        a1.set_before({"value": "Acme S.A."})
        a1.set_after({"value": "Acme Inc."})
        a1.set_result({"success": True, "data": {"updated": True}})

    # Tool 2: save_hiring_policy bloqueado por fairness
    async with ad.audit_company_change(
        action="save_hiring_policy",
        company_id="co-acme",
        actor="user-42",
        target_table="company_hiring_policies",
        target_id="policy-uuid-99",
        metadata={"rule_keys": ["communication_rules"]},
    ) as a2:
        a2.set_before({"lia_tone": "friendly"})
        a2.set_after({"lia_tone": "harsh"})
        a2.set_result({
            "success": False,
            "reason": "fairness_violation",
            "offending_field": "lia_tone",
        })

    # Verifica persistência REAL no audit_logs
    async with SessionMaker() as session:
        result = await session.execute(select(AuditLog).order_by(AuditLog.created_at))
        rows = list(result.scalars().all())

    assert len(rows) == 4, (
        f"Esperava 4 audit rows (2 tools × 2 fases), obtidas {len(rows)}: "
        f"{[(r.action, r.decision) for r in rows]}"
    )

    # Agrupa por action para validar pares intent+outcome
    by_action: dict[str, list[AuditLog]] = {}
    for r in rows:
        by_action.setdefault(r.action, []).append(r)

    # save_company_field: initiated + completed
    field_rows = by_action["save_company_field"]
    assert len(field_rows) == 2
    decisions = sorted(r.decision for r in field_rows)
    assert decisions == ["completed", "initiated"]
    completed = next(r for r in field_rows if r.decision == "completed")
    assert completed.company_id == "co-acme"
    assert completed.decision_type == "company_settings_change"
    reasoning_blob = " | ".join(completed.reasoning)
    assert "before=" in reasoning_blob and "Acme S.A." in reasoning_blob
    assert "after=" in reasoning_blob and "Acme Inc." in reasoning_blob
    assert "target_id=co-acme::profile.name" in reasoning_blob
    assert "actor=user-42" in reasoning_blob
    # Trace ID compartilhado entre intent e outcome
    intent = next(r for r in field_rows if r.decision == "initiated")
    intent_trace = next(
        r.split("=", 1)[1] for r in intent.reasoning if r.startswith("trace_id=")
    )
    completed_trace = next(
        r.split("=", 1)[1] for r in completed.reasoning if r.startswith("trace_id=")
    )
    assert intent_trace == completed_trace, (
        "intent e outcome devem compartilhar trace_id pra correlação forense"
    )

    # save_hiring_policy: initiated + blocked_fairness
    policy_rows = by_action["save_hiring_policy"]
    assert len(policy_rows) == 2
    decisions = sorted(r.decision for r in policy_rows)
    assert decisions == ["blocked_fairness", "initiated"]
    blocked = next(r for r in policy_rows if r.decision == "blocked_fairness")
    assert blocked.company_id == "co-acme"
    blocked_blob = " | ".join(blocked.reasoning)
    assert "target_id=policy-uuid-99" in blocked_blob
    assert "before=" in blocked_blob and "after=" in blocked_blob

    # criteria_used canônico em todas as 4 rows
    for r in rows:
        cu = r.criteria_used
        assert "company_scoped" in cu
        assert any(c.startswith("target_table:") for c in cu)
        assert any(c.startswith("trace_id:") for c in cu)


@pytest.mark.asyncio
async def test_pr4_intent_failure_aborts_business_no_outcome_row(
    in_memory_audit_engine, monkeypatch
):
    """Storage de audit indisponível no intent: bloco protegido NÃO
    executa → 0 rows persistidas (e RuntimeError no caller). Esse é o
    coração do "outbox-equivalent transactional pattern": audit
    indisponível ⇒ business write não acontece."""
    engine, SessionMaker = in_memory_audit_engine

    # Faz a primeira chamada ao log_decision falhar
    original = audit_svc.AuditService.log_decision
    call_count = {"n": 0}

    async def _fail_first(self, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("audit storage indisponível")
        return await original(self, **kwargs)

    monkeypatch.setattr(audit_svc.AuditService, "log_decision", _fail_first)

    business_executed = False

    with pytest.raises(RuntimeError, match="audit storage unavailable"):
        async with ad.audit_company_change(
            action="save_company_field",
            company_id="co-bravo",
            actor="user-1",
            target_table="company_profiles",
            metadata={},
        ) as a:
            business_executed = True
            a.set_result({"success": True})

    assert business_executed is False

    # Nenhuma row persistida — intent falhou antes do business code rodar
    async with SessionMaker() as session:
        result = await session.execute(select(AuditLog))
        rows = list(result.scalars().all())
    assert rows == [], (
        f"intent falhou → 0 rows esperadas; obtidas {len(rows)}: "
        f"{[(r.action, r.decision) for r in rows]}"
    )
