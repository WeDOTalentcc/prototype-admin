"""Task #1021 — Integration: real ToolExecutor → audit_company_change → INSERT
em ``audit_logs`` (Postgres + RLS).

Origem do gap: a sentinela em ``test_company_settings_no_regression.py``
mocka o tool registry. ``test_company_audit_persistence_pr4.py`` exerce
``audit_company_change`` direto, mas com ``AsyncSessionLocal`` apontado
para sqlite in-memory + ``_bind_tenant`` no-op — ou seja, NÃO exercita
RLS. Foi exatamente esse gap que deixou o build verde enquanto
``session.refresh(audit_log)`` em sessão RLS-bound bloqueava 100% das
tools de Minha Empresa em produção (Bug A da auditoria #1015 / Task
#1016 PR-A).

Este teste fecha a malha:

  1. Sobe um tenant temporário em ``companies`` (UUID v4 satisfazendo
     ``ck_companies_id_format_canonical``).
  2. Roda ``initialize_tools()`` para popular o registry global.
  3. Chama ``check_company_completeness`` via ``ToolExecutor`` real
     (com ``ToolExecutionContext`` autêntico, mesma rota do orchestrator).
  4. Asserta que o ToolResult devolve payload válido (``success=True``).
  5. SELECT direto em ``audit_logs`` (sessão RLS-bound) confirma que
     existe exatamente 1 row com
     ``decision_type='company_settings_change'`` e ``decision='read'``
     pra esse tenant — prova que o caminho:

         AuditService.log_decision  →  AsyncSessionLocal()  →
         _bind_tenant(set_config app.company_id)  →  INSERT ...  →
         COMMIT  (sem session.refresh)

     funciona ponta a ponta em sessão RLS-bound.

Se um futuro PR re-introduzir ``session.refresh(audit_log)`` em
``AuditService.log_decision`` (ou em qualquer caminho equivalente), o
SELECT após COMMIT levantará ``InvalidRequestError`` na chamada da tool
e este teste quebra antes do merge.

O teste pula automaticamente se ``DATABASE_URL`` não for Postgres — o
caminho RLS é o ponto inteiro do contrato e sqlite não tem como
representá-lo.
"""
from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import text


pytestmark = pytest.mark.asyncio


def _postgres_available() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    return url.startswith("postgres")


pytest_skip_if_no_pg = pytest.mark.skipif(
    not _postgres_available(),
    reason=(
        "Requer DATABASE_URL Postgres real — o ponto do teste é exercitar "
        "RLS em audit_logs, que não existe em sqlite."
    ),
)


@pytest.fixture
async def temp_company():
    """Cria um tenant descartável em ``companies`` e devolve o UUID.

    O id é UUID v4 pra satisfazer ``ck_companies_id_format_canonical``.
    Cleanup remove a row e qualquer audit_logs com seu company_id (RLS
    exige ``set_config('app.company_id', ...)`` antes do DELETE — mesmo
    o owner não bypassa FORCE ROW LEVEL SECURITY).
    """
    from app.shared.compliance.audit_service import AsyncSessionLocal

    company_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(
                "INSERT INTO companies (id, name, is_demo) "
                "VALUES (:cid, :name, false)"
            ),
            {"cid": company_id, "name": f"Test #1021 {company_id[:8]}"},
        )
        await session.commit()

    yield company_id

    async with AsyncSessionLocal() as session:
        await session.execute(
            text("SELECT set_config('app.company_id', :cid, true)"),
            {"cid": company_id},
        )
        await session.execute(
            text("DELETE FROM audit_logs WHERE company_id = :cid"),
            {"cid": company_id},
        )
        await session.execute(
            text("DELETE FROM companies WHERE id = :cid"),
            {"cid": company_id},
        )
        await session.commit()


@pytest_skip_if_no_pg
async def test_check_company_completeness_via_tool_executor_persists_audit_row(
    temp_company,
):
    """Caminho canônico ponta a ponta:

      ``ToolExecutor.execute("check_company_completeness", ...)`` →
      ``audit_company_change(read_only=True)`` →
      ``AuditService.log_decision`` (write em audit_logs RLS-bound).

    Sem mocks na cadeia: ``initialize_tools()`` registra a tool real,
    ``ToolExecutionContext`` simula o orchestrator, e o INSERT acontece
    contra Postgres com policy ``audit_logs_tenant_insert``
    (``WITH CHECK (company_id::text = app_current_company_id())``).
    """
    from app.shared.compliance.audit_service import AsyncSessionLocal
    from app.tools import initialize_tools
    from app.tools.executor import ToolExecutionContext, ToolExecutor
    from app.tools.registry import tool_registry

    initialize_tools()
    assert tool_registry.get_tool("check_company_completeness") is not None, (
        "Pré-condição: initialize_tools() deve registrar "
        "`check_company_completeness` no tool_registry global."
    )

    company_id = temp_company
    user_id = str(uuid.uuid4())

    executor = ToolExecutor(registry=tool_registry)
    ctx = ToolExecutionContext(
        user_id=user_id,
        company_id=company_id,
        permissions=[],
        session_id=str(uuid.uuid4()),
    )

    result = await executor.execute(
        tool_name="check_company_completeness",
        parameters={},
        context=ctx,
        agent_type="company_settings",
    )

    # 1) Payload válido — prova que o wrapper audit_company_change não
    # explodiu por re-introdução de session.refresh ou outra regressão
    # equivalente. Antes do fix #1016, este caminho devolvia
    # success=False com error="db_error" porque o RuntimeError do
    # FAIL-CLOSED do read outcome propagava até ToolExecutor.
    assert result.success is True, (
        f"ToolResult inesperado: success={result.success!r} "
        f"error={result.error!r} result={result.result!r} — "
        "regressão provável: refresh em sessão RLS-bound, ou outra "
        "falha no caminho audit_company_change → AuditService."
    )
    payload = result.result
    assert isinstance(payload, dict)
    assert payload.get("success") is True
    # Empresa fresh — todos os campos obrigatórios estão vazios.
    assert payload["company_id"] == company_id
    assert isinstance(payload.get("missing_profile_fields"), list)
    assert isinstance(payload.get("missing_culture_fields"), list)
    assert "recommendation" in payload

    # 2) Persistência REAL em audit_logs (sessão RLS-bound, FORCE RLS).
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("SELECT set_config('app.company_id', :cid, true)"),
            {"cid": company_id},
        )
        rows = (
            await session.execute(
                text(
                    "SELECT decision_type, decision, action, agent_name "
                    "FROM audit_logs "
                    "WHERE company_id = :cid "
                    "  AND decision_type = 'company_settings_change' "
                    "  AND action = 'check_company_completeness'"
                ),
                {"cid": company_id},
            )
        ).mappings().all()

    assert len(rows) == 1, (
        f"Esperava exatamente 1 row em audit_logs (decision_type="
        f"'company_settings_change', action='check_company_completeness') "
        f"pra company_id={company_id}; obtidas {len(rows)}: {list(rows)}. "
        "Caminho ToolExecutor → audit_company_change(read_only=True) → "
        "AuditService.log_decision não persistiu — possível regressão do "
        "fix #1016 (session.refresh em sessão RLS-bound) ou drift no "
        "_emit_independent do read outcome."
    )
    only = rows[0]
    assert only["decision"] == "read", (
        f"read-only deve emitir decision='read' (derivado em "
        f"_derive_outcome com read_only=True); obtido: {only['decision']!r}"
    )
    assert only["agent_name"] == "company_settings_tools", (
        "agent_name canônico do wrapper audit_company_change é "
        "'company_settings_tools' (default em audit_decorators); "
        f"obtido: {only['agent_name']!r}"
    )
