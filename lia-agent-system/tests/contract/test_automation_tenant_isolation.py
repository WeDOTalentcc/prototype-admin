"""Cross-tenant isolation contract test for automation module.

Sensor permanente para o ratchet decremental tenant-filter sprint automation
(2026-05-22). Pina:
- AISuggestionRepository.get_by_id / list_by_vacancy / list_by_candidate filtram
  por company_id (P1.1 fix multi-tenancy fail-closed).
- AISuggestionRepository._require_company_id raise ValueError quando company_id
  vazio (R-019 P0 fail-closed).
- PlannedTaskRepository.list_ready_candidates aplica
  `PlannedTask.company_id == company_id` quando company_id é provido.
- PlannedTaskRepository._require_company_id raise ValueError quando company_id
  vazio (R-019 P0).
- ProactiveAlertService.check_predictive_indicators filtra Candidate.company_id
  (bug P0 LGPD descoberto na sprint automation, fix 2026-05-22).

Pattern: pure-unit tests (sem subir FastAPI app nem DB session real).
Espelha pattern de test_audit_logs_tenant_isolation.py + test_offer_approval_gate.py.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.automation.repositories.ai_suggestion_repository import (
    AISuggestionRepository,
)
from app.domains.automation.repositories.planned_task_repository import (
    PlannedTaskRepository,
)


TENANT_A_ID = "11111111-1111-4111-a111-111111111111"
TENANT_B_ID = "22222222-2222-4222-a222-222222222222"


# ---------------------------------------------------------------------------
# AISuggestionRepository — cross-tenant isolation
# ---------------------------------------------------------------------------


class TestAISuggestionRepositoryTenantIsolation:
    """Pin company_id filter in AISuggestion read methods (P1.1 regression sensor)."""

    def test_require_company_id_rejects_empty_string(self):
        """R-019 P0 fail-closed: empty company_id deve levantar ValueError."""
        with pytest.raises(ValueError) as exc_info:
            AISuggestionRepository._require_company_id("")
        assert "company_id" in str(exc_info.value).lower()

    def test_require_company_id_rejects_none(self):
        """R-019 P0 fail-closed: None company_id deve levantar ValueError."""
        with pytest.raises(ValueError) as exc_info:
            AISuggestionRepository._require_company_id(None)
        assert "company_id" in str(exc_info.value).lower()

    def test_require_company_id_accepts_valid_uuid(self):
        """company_id válido retorna a string normalizada."""
        result = AISuggestionRepository._require_company_id(TENANT_A_ID)
        assert result == TENANT_A_ID

    @pytest.mark.asyncio
    async def test_get_by_id_applies_company_filter(self):
        """get_by_id deve emitir SELECT com WHERE company_id == <tenant>."""
        db = MagicMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none = MagicMock(return_value=None)
        db.execute = AsyncMock(return_value=result_mock)

        repo = AISuggestionRepository(db)
        await repo.get_by_id(uuid4(), company_id=TENANT_A_ID)

        # Inspecionar query SQL renderizada
        executed_stmt = db.execute.call_args[0][0]
        rendered = str(
            executed_stmt.compile(compile_kwargs={"literal_binds": True})
        )
        assert TENANT_A_ID in rendered, (
            f"Esperava {TENANT_A_ID} na query renderizada (filter company_id), "
            f"recebido:\n{rendered}"
        )
        assert "company_id" in rendered.lower()

    @pytest.mark.asyncio
    async def test_get_by_id_rejects_missing_company_id(self):
        """get_by_id sem company_id (None) deve levantar ValueError (fail-closed)."""
        db = MagicMock()
        repo = AISuggestionRepository(db)
        with pytest.raises(ValueError):
            await repo.get_by_id(uuid4(), company_id="")

    @pytest.mark.asyncio
    async def test_list_by_vacancy_applies_company_filter(self):
        """list_by_vacancy deve filtrar por company_id (rejeita cross-tenant)."""
        db = MagicMock()
        result_mock = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=[])
        result_mock.scalars = MagicMock(return_value=scalars_mock)
        db.execute = AsyncMock(return_value=result_mock)

        repo = AISuggestionRepository(db)
        await repo.list_by_vacancy("vacancy-123", company_id=TENANT_A_ID)

        executed_stmt = db.execute.call_args[0][0]
        rendered = str(
            executed_stmt.compile(compile_kwargs={"literal_binds": True})
        )
        assert TENANT_A_ID in rendered
        assert "company_id" in rendered.lower()

    @pytest.mark.asyncio
    async def test_list_by_candidate_applies_company_filter(self):
        """list_by_candidate deve filtrar por company_id (rejeita cross-tenant)."""
        db = MagicMock()
        result_mock = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=[])
        result_mock.scalars = MagicMock(return_value=scalars_mock)
        db.execute = AsyncMock(return_value=result_mock)

        repo = AISuggestionRepository(db)
        await repo.list_by_candidate("candidate-456", company_id=TENANT_A_ID)

        executed_stmt = db.execute.call_args[0][0]
        rendered = str(
            executed_stmt.compile(compile_kwargs={"literal_binds": True})
        )
        assert TENANT_A_ID in rendered
        assert "company_id" in rendered.lower()


# ---------------------------------------------------------------------------
# PlannedTaskRepository — cross-tenant isolation (fail-closed quando provido)
# ---------------------------------------------------------------------------


class TestPlannedTaskRepositoryTenantIsolation:
    """Pin company_id filter in PlannedTaskRepository read methods (R-019 P0)."""

    def test_require_company_id_rejects_empty_string(self):
        """R-019 P0 fail-closed: empty company_id deve levantar ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PlannedTaskRepository._require_company_id("")
        assert "company_id" in str(exc_info.value).lower()

    def test_require_company_id_accepts_valid_uuid(self):
        """company_id válido é normalizado para str."""
        result = PlannedTaskRepository._require_company_id(TENANT_A_ID)
        assert result == TENANT_A_ID

    @pytest.mark.asyncio
    async def test_list_ready_candidates_applies_company_filter_when_provided(self):
        """list_ready_candidates aplica filter quando company_id provido."""
        db = MagicMock()
        result_mock = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=[])
        result_mock.scalars = MagicMock(return_value=scalars_mock)
        db.execute = AsyncMock(return_value=result_mock)

        repo = PlannedTaskRepository(db)
        await repo.list_ready_candidates(company_id=TENANT_A_ID)

        executed_stmt = db.execute.call_args[0][0]
        rendered = str(
            executed_stmt.compile(compile_kwargs={"literal_binds": True})
        )
        assert TENANT_A_ID in rendered, (
            f"Esperava {TENANT_A_ID} na query (PlannedTask.company_id filter), "
            f"recebido:\n{rendered}"
        )

    @pytest.mark.asyncio
    async def test_list_ready_candidates_rejects_empty_company_id(self):
        """company_id="" é rejeitado pela _require_company_id (fail-closed)."""
        db = MagicMock()
        repo = PlannedTaskRepository(db)
        with pytest.raises(ValueError):
            await repo.list_ready_candidates(company_id="")

    @pytest.mark.asyncio
    async def test_list_ready_candidates_no_company_id_is_cross_tenant(self):
        """Quando company_id is None, query roda cross-tenant (system context).

        Verifica que NÃO há WHERE planned_tasks.company_id = ... no SQL
        (sufficient: tenant_id não aparece bound na cláusula WHERE).
        """
        db = MagicMock()
        result_mock = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=[])
        result_mock.scalars = MagicMock(return_value=scalars_mock)
        db.execute = AsyncMock(return_value=result_mock)

        repo = PlannedTaskRepository(db)
        # company_id=None: scheduler/admin scan — sem filter por design
        await repo.list_ready_candidates(company_id=None)

        executed_stmt = db.execute.call_args[0][0]
        rendered = str(
            executed_stmt.compile(compile_kwargs={"literal_binds": True})
        ).lower()
        # Extrair somente a cláusula WHERE (após FROM ... WHERE)
        where_part = rendered.split("where", 1)[1] if "where" in rendered else ""
        # Cross-tenant: WHERE não deve mencionar company_id (filter), apenas SELECT pode.
        assert "company_id" not in where_part, (
            "Esperava query SEM company_id filter na WHERE (cross-tenant intencional), "
            f"recebido WHERE clause:\n{where_part}"
        )
        # Sanity: tenant uuid NÃO aparece bound no SQL renderizado
        assert TENANT_A_ID not in rendered

    @pytest.mark.asyncio
    async def test_get_by_id_applies_company_filter_when_provided(self):
        """get_by_id aplica company_id filter quando provido."""
        db = MagicMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none = MagicMock(return_value=None)
        db.execute = AsyncMock(return_value=result_mock)

        repo = PlannedTaskRepository(db)
        await repo.get_by_id("task-id-1", company_id=TENANT_A_ID)

        executed_stmt = db.execute.call_args[0][0]
        rendered = str(
            executed_stmt.compile(compile_kwargs={"literal_binds": True})
        )
        assert TENANT_A_ID in rendered
        assert "company_id" in rendered.lower()


# ---------------------------------------------------------------------------
# ProactiveAlertService — Candidate.company_id filter (P0 LGPD bug fix)
# ---------------------------------------------------------------------------


class TestProactiveAlertServiceTenantIsolation:
    """Pin Candidate.company_id filter in check_predictive_indicators.

    Bug P0 LGPD encontrado durante sprint automation tenant_filter (2026-05-22):
    select(Candidate).where(...) sem filter por company_id permitia o método
    enxergar candidates de OUTROS tenants. Fix aplica `Candidate.company_id == company_id`.
    """

    @pytest.mark.asyncio
    async def test_check_predictive_indicators_filters_candidate_by_company_id(self):
        """check_predictive_indicators applies Candidate.company_id == company_id."""
        from app.domains.automation.services.proactive_alert_service import (
            ProactiveAlertService,
        )

        # Mock db that captures executed SQL
        db = MagicMock()
        executed_queries = []

        async def capture_execute(stmt, *args, **kwargs):
            executed_queries.append(stmt)
            result_mock = MagicMock()
            scalars_mock = MagicMock()
            scalars_mock.all = MagicMock(return_value=[])
            scalars_mock.first = MagicMock(return_value=None)
            result_mock.scalars = MagicMock(return_value=scalars_mock)
            result_mock.scalar_one_or_none = MagicMock(return_value=None)
            result_mock.scalar = MagicMock(return_value=0)
            return result_mock

        db.execute = capture_execute

        service = ProactiveAlertService()
        # Patch _get_effective_threshold to a stable response
        service._get_effective_threshold = MagicMock(
            return_value={"threshold_match": 90, "severity": "info"}
        )

        await service.check_predictive_indicators(
            user_id="user-xyz",
            company_id=TENANT_A_ID,
            db=db,
        )

        # At least one query must mention company_id and the tenant value
        found_filter = False
        for q in executed_queries:
            try:
                rendered = str(
                    q.compile(compile_kwargs={"literal_binds": True})
                )
            except Exception:
                continue
            if TENANT_A_ID in rendered and "company_id" in rendered.lower():
                found_filter = True
                break

        assert found_filter, (
            "Esperava SELECT Candidate com Candidate.company_id == company_id "
            f"para tenant {TENANT_A_ID}. Queries executadas:\n"
            + "\n".join(
                str(q.compile(compile_kwargs={"literal_binds": True}))
                for q in executed_queries
                if hasattr(q, "compile")
            )
        )
