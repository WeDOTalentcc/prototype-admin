"""Task #1017 — Integration test: ``check_company_completeness`` via
``ToolExecutor`` REAL (não mocada) persistindo linha em ``audit_logs``.

Contexto da regressão original
──────────────────────────────
A sentinela offline ``test_company_settings_no_regression.py`` (1396L)
mocka todo o tool registry e nunca toca ``audit_logs``. Resultado: a
LIA podia chamar ``check_company_completeness`` em produção, devolver
payload “correto”, e NÃO gravar nenhuma linha de auditoria — violando
silenciosamente Inegociável #6 (SOX/ISO 27001/EU AI Act). O caso
canônico passou a precisar de um teste end-to-end que exercitasse
*pelo menos* a cadeia ``ToolExecutor → registry → handler →
audit_company_change → AuditService → INSERT audit_logs``.

Estratégia
──────────
* sqlite in-memory + monkeypatch em ``audit_service.AsyncSessionLocal``
  + ``_bind_tenant`` (mesmo padrão de
  ``test_company_audit_persistence_pr4.py``);
* ``ToolExecutor`` real, instanciado com uma ``ToolRegistry`` fresh
  (sem poluição de outras tools registradas em outros testes);
* ``register_company_settings_tools()`` chamado contra esse registry
  fresh (monkeypatch em ``import_tools.tool_registry``) — cobre o
  contrato de allowed_agents / parameters_schema canônico;
* ``_check_company_completeness_impl`` é stubbado para devolver um
  payload sqlite-friendly. Esta única substituição é DOCUMENTADA e
  intencional: a impl real usa ``id::text = :cid`` (sintaxe pg-only)
  que sqlite não parseia. O caminho de governança (audit ctx + INSERT)
  é exercitado 100% real — apenas o conteúdo do SELECT é stub.
  Quando a infra de testes ganhar Postgres efêmero, este stub deve
  ser removido e a impl real exercitada de ponta-a-ponta.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.audit_log import AuditLog
from app.shared.compliance import audit_service as audit_svc
from app.tools.executor import ToolExecutionContext, ToolExecutor
from app.tools.registry import ToolRegistry
from app.domains.company_settings.tools import import_tools


@pytest.fixture
async def in_memory_audit_engine(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: AuditLog.__table__.create(c))

    SessionMaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def _noop_bind_tenant(session, company_id):
        return None

    monkeypatch.setattr(audit_svc, "AsyncSessionLocal", SessionMaker)
    monkeypatch.setattr(audit_svc, "_bind_tenant", _noop_bind_tenant)
    monkeypatch.delenv("LIA_DISABLE_COMPANY_AUDIT", raising=False)

    yield engine, SessionMaker

    await engine.dispose()


@pytest.fixture
def isolated_tool_registry(monkeypatch):
    """Registry fresh + register_company_settings_tools contra ele.

    Patches ``import_tools.tool_registry`` para evitar colisão com a
    instância global (que pode ter sido populada por outros módulos
    importados via fixtures). O ``ToolExecutor`` recebe a mesma
    instância via construtor — não há fallback para ``tool_registry``
    global durante este teste.
    """
    fresh = ToolRegistry()
    monkeypatch.setattr(import_tools, "tool_registry", fresh)
    import_tools.register_company_settings_tools()
    return fresh


@pytest.fixture
def stub_completeness_impl(monkeypatch):
    """Substitui ``_check_company_completeness_impl`` por uma versão
    sqlite-friendly. Vide docstring do módulo (justificativa)."""
    captured = {}

    async def _impl(*, session, company_id):
        captured["session"] = session
        captured["company_id"] = company_id
        return {
            "success": True,
            "company_id": company_id,
            "profile_completeness_pct": 0.5,
            "culture_completeness_pct": 0.4,
            "overall_pct": 0.45,
            "missing_profile_fields": ["website", "linkedin_url"],
            "missing_culture_fields": ["mission", "vision"],
            "has_website": False,
            "website": None,
            "recommendation": "Perfil 45% completo — adicione website e LinkedIn.",
        }

    monkeypatch.setattr(import_tools, "_check_company_completeness_impl", _impl)
    return captured


@pytest.mark.asyncio
async def test_check_company_completeness_persists_audit_via_real_executor(
    in_memory_audit_engine, isolated_tool_registry, stub_completeness_impl,
):
    """End-to-end: ToolExecutor real → handler real → audit_logs INSERT."""
    _engine, SessionMaker = in_memory_audit_engine
    executor = ToolExecutor(registry=isolated_tool_registry)

    ctx = ToolExecutionContext(
        user_id="user-task-1017",
        company_id="co-task-1017",
        permissions=[],
        session_id="sess-1017",
    )

    result = await executor.execute(
        tool_name="check_company_completeness",
        parameters={},
        agent_type="company_settings",
        context=ctx,
    )

    # Payload — contrato externo da tool
    assert result.success, f"executor.execute falhou: {result.error}"
    assert result.tool_name == "check_company_completeness"
    payload = result.result
    assert isinstance(payload, dict), f"payload deve ser dict, veio {type(payload)}"
    assert payload["success"] is True
    assert payload["company_id"] == "co-task-1017"
    assert "missing_profile_fields" in payload
    assert "overall_pct" in payload
    assert "has_website" in payload

    # Sentinela: o handler recebeu o ctx via _context (tenant injection)
    assert stub_completeness_impl["company_id"] == "co-task-1017", (
        "handler não recebeu company_id do ToolExecutionContext — quebra "
        "do contrato de tenant injection do ToolExecutor"
    )

    # Audit row REAL — read-only flow emite UMA row independent com
    # decision="read" (vide audit_decorators.py: read_only path NÃO
    # emite intent, apenas outcome).
    async with SessionMaker() as session:
        rows = list(
            (await session.execute(select(AuditLog).order_by(AuditLog.created_at)))
            .scalars()
            .all()
        )

    actions_decisions = [(r.action, r.decision) for r in rows]
    assert any(
        a == "check_company_completeness" and d == "read"
        for a, d in actions_decisions
    ), (
        "audit_logs deveria conter (check_company_completeness, read). "
        f"Persistido: {actions_decisions}. "
        "Esta era exatamente a falha invisível pré-Task #1017: tool "
        "rodava em prod, devolvia payload, mas NÃO deixava trilha SOX."
    )

    read_row = next(
        r for r in rows
        if r.action == "check_company_completeness" and r.decision == "read"
    )
    assert read_row.company_id == "co-task-1017"
    assert read_row.decision_type == "company_settings_change"
    assert read_row.agent_name == "company_settings_tools"
    # Reasoning canônico: trace_id/actor/target_id/outcome
    blob = " | ".join(read_row.reasoning)
    assert "outcome=read" in blob
    assert "trace_id=" in blob
    cu = read_row.criteria_used
    assert "company_scoped" in cu
    assert "read_only:True" in cu


@pytest.mark.asyncio
async def test_check_company_completeness_unauthorized_agent_returns_error(
    in_memory_audit_engine, isolated_tool_registry, stub_completeness_impl,
):
    """allowed_agents é defesa em profundidade — agente fora da lista
    canônica recebe erro estruturado E não dispara audit row (handler
    nunca executa)."""
    _engine, SessionMaker = in_memory_audit_engine
    executor = ToolExecutor(registry=isolated_tool_registry)

    ctx = ToolExecutionContext(
        user_id="u", company_id="co-x", permissions=[], session_id="s",
    )

    result = await executor.execute(
        tool_name="check_company_completeness",
        parameters={},
        agent_type="random_other_agent",
        context=ctx,
    )

    assert result.success is False
    assert result.error and "not authorized" in result.error

    async with SessionMaker() as session:
        rows = list((await session.execute(select(AuditLog))).scalars().all())
    assert rows == [], (
        f"Agente não autorizado NÃO pode disparar audit row. Persistido: "
        f"{[(r.action, r.decision) for r in rows]}"
    )
