"""W1-004-B · TDD · kanban_tool_registry ADR-001 migration.

Tests são RED antes da implementação e GREEN depois.
Valida:
1. SQL inline removido de 6 funções do kanban_tool_registry
2. RecruiterMetricsRepository tem métodos novos
3. CandidatePipelineRepository existe e tem métodos corretos
4. Todos os repos têm _require_company_id fail-closed
5. kanban_tool_registry importa CandidatePipelineRepository
"""
import re
from pathlib import Path

import pytest


# ── Paths ──────────────────────────────────────────────────────────────────────
KANBAN = Path(
    "app/domains/recruiter_assistant/agents/kanban_tool_registry.py"
)
METRICS_REPO = Path(
    "app/domains/recruiter_assistant/repositories/recruiter_metrics_repository.py"
)
PIPELINE_REPO = Path(
    "app/domains/recruiter_assistant/repositories/candidate_pipeline_repository.py"
)


# ── Helper ─────────────────────────────────────────────────────────────────────
def _func_src(full_src: str, func_name: str) -> str:
    """Extrai código-fonte de uma função (até a próxima função async def / EOF)."""
    pattern = rf"async def {func_name}.*?(?=\nasync def |\Z)"
    m = re.search(pattern, full_src, re.DOTALL)
    return m.group(0) if m else ""


# ── 1. SQL inline removido ─────────────────────────────────────────────────────

class TestNoSQLInlineInKanban:
    """Verifica que os blocos text(\"\"\"...\"\"\") foram removidos das funções."""

    def _assert_no_inline_sql(self, func_name: str):
        src = KANBAN.read_text()
        func_src = _func_src(src, func_name)
        assert func_src, f"Função {func_name} não encontrada em kanban_tool_registry"
        assert 'text("""' not in func_src, (
            f"SQL inline text(\"\"\"...\"\"\") deve ser removido de {func_name}. "
            "Delegar para repository canonical."
        )

    def test_no_inline_sql_pipeline_summary(self):
        self._assert_no_inline_sql("_wrap_get_pipeline_summary")

    def test_no_inline_sql_stage_metrics(self):
        self._assert_no_inline_sql("_wrap_get_stage_metrics")

    def test_no_inline_sql_list_stage_candidates(self):
        self._assert_no_inline_sql("_wrap_list_stage_candidates")

    def test_no_inline_sql_identify_bottlenecks(self):
        self._assert_no_inline_sql("_wrap_identify_bottlenecks")

    def test_no_inline_sql_candidate_aging(self):
        self._assert_no_inline_sql("_wrap_get_candidate_aging")

    def test_no_inline_sql_suggest_movements(self):
        self._assert_no_inline_sql("_wrap_suggest_movements")

    def test_no_inline_sql_batch_move(self):
        self._assert_no_inline_sql("_wrap_batch_move_candidates")

    def test_no_inline_sql_view_profile(self):
        self._assert_no_inline_sql("_wrap_view_candidate_full_profile")


# ── 2. RecruiterMetricsRepository métodos novos ────────────────────────────────

class TestRecruiterMetricsRepoExtensions:
    """RecruiterMetricsRepository deve ter os 4 métodos novos."""

    def test_has_count_candidates_per_stage(self):
        from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
            RecruiterMetricsRepository,
        )
        assert hasattr(RecruiterMetricsRepository, "count_candidates_per_stage"), (
            "RecruiterMetricsRepository.count_candidates_per_stage ausente"
        )

    def test_has_get_stage_metrics(self):
        from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
            RecruiterMetricsRepository,
        )
        assert hasattr(RecruiterMetricsRepository, "get_stage_metrics"), (
            "RecruiterMetricsRepository.get_stage_metrics ausente"
        )

    def test_has_get_stage_bottleneck_metrics(self):
        from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
            RecruiterMetricsRepository,
        )
        assert hasattr(RecruiterMetricsRepository, "get_stage_bottleneck_metrics"), (
            "RecruiterMetricsRepository.get_stage_bottleneck_metrics ausente"
        )

    def test_has_bulk_update_candidate_stage(self):
        from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
            RecruiterMetricsRepository,
        )
        assert hasattr(RecruiterMetricsRepository, "bulk_update_candidate_stage"), (
            "RecruiterMetricsRepository.bulk_update_candidate_stage ausente"
        )


# ── 3. CandidatePipelineRepository ────────────────────────────────────────────

class TestCandidatePipelineRepoImportable:
    """CandidatePipelineRepository deve existir e expor métodos corretos."""

    def test_importable(self):
        from app.domains.recruiter_assistant.repositories.candidate_pipeline_repository import (
            CandidatePipelineRepository,
        )
        assert CandidatePipelineRepository is not None

    def test_has_list_candidates_in_stage(self):
        from app.domains.recruiter_assistant.repositories.candidate_pipeline_repository import (
            CandidatePipelineRepository,
        )
        assert hasattr(CandidatePipelineRepository, "list_candidates_in_stage"), (
            "CandidatePipelineRepository.list_candidates_in_stage ausente"
        )

    def test_has_get_aging_candidates(self):
        from app.domains.recruiter_assistant.repositories.candidate_pipeline_repository import (
            CandidatePipelineRepository,
        )
        assert hasattr(CandidatePipelineRepository, "get_aging_candidates"), (
            "CandidatePipelineRepository.get_aging_candidates ausente"
        )

    def test_has_get_candidates_for_movement_suggestion(self):
        from app.domains.recruiter_assistant.repositories.candidate_pipeline_repository import (
            CandidatePipelineRepository,
        )
        assert hasattr(CandidatePipelineRepository, "get_candidates_for_movement_suggestion"), (
            "CandidatePipelineRepository.get_candidates_for_movement_suggestion ausente"
        )

    def test_has_get_candidate_full_profile(self):
        from app.domains.recruiter_assistant.repositories.candidate_pipeline_repository import (
            CandidatePipelineRepository,
        )
        assert hasattr(CandidatePipelineRepository, "get_candidate_full_profile"), (
            "CandidatePipelineRepository.get_candidate_full_profile ausente"
        )


# ── 4. _require_company_id fail-closed ────────────────────────────────────────

class TestRequireCompanyIdFailClosed:
    """Ambos repos devem rejeitar company_id vazio."""

    def test_metrics_repo_rejects_empty_company_id(self):
        from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
            RecruiterMetricsRepository,
        )
        with pytest.raises(ValueError, match="company_id is required"):
            RecruiterMetricsRepository._require_company_id("")

    def test_metrics_repo_rejects_none_company_id(self):
        from app.domains.recruiter_assistant.repositories.recruiter_metrics_repository import (
            RecruiterMetricsRepository,
        )
        with pytest.raises(ValueError, match="company_id is required"):
            RecruiterMetricsRepository._require_company_id(None)

    def test_pipeline_repo_rejects_empty_company_id(self):
        from app.domains.recruiter_assistant.repositories.candidate_pipeline_repository import (
            CandidatePipelineRepository,
        )
        with pytest.raises(ValueError, match="company_id is required"):
            CandidatePipelineRepository._require_company_id("")

    def test_pipeline_repo_rejects_none_company_id(self):
        from app.domains.recruiter_assistant.repositories.candidate_pipeline_repository import (
            CandidatePipelineRepository,
        )
        with pytest.raises(ValueError, match="company_id is required"):
            CandidatePipelineRepository._require_company_id(None)


# ── 5. kanban_tool_registry importa CandidatePipelineRepository ───────────────

class TestKanbanImportsCandidatePipelineRepo:
    """kanban_tool_registry.py deve referenciar CandidatePipelineRepository."""

    def test_kanban_imports_candidate_pipeline_repo(self):
        src = KANBAN.read_text()
        assert "CandidatePipelineRepository" in src, (
            "kanban_tool_registry deve importar CandidatePipelineRepository "
            "para poder delegar queries para o novo repo."
        )

    def test_kanban_imports_recruiter_metrics_repo(self):
        src = KANBAN.read_text()
        assert "RecruiterMetricsRepository" in src, (
            "kanban_tool_registry deve importar RecruiterMetricsRepository"
        )
