"""Unit tests — FairnessGuard integration in JD bulk import pipeline.

Harness: Sensor (computacional) — D3 do Sprint A debt resolution.

FairnessGuard é importado lazily dentro de import_jd(), então o patch
correto é `app.shared.compliance.fairness_guard.FairnessGuard`.

Cobre:
- JD hard-blocked → is_used_for_learning=False + ValueError propagado
  → import_batch_jds conta como failed
- JD com soft warnings → is_used_for_learning=False + JD salva (não failed)
- JD limpa → is_used_for_learning inalterado pelo FairnessGuard
- FairnessGuard crash → fail-open
- _update_skill_catalog exclui JDs com is_used_for_learning=False
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Patch path para o import lazy dentro de import_jd()
_FG_PATH = "app.shared.compliance.fairness_guard.FairnessGuard"


def _make_fg_result(is_blocked: bool = False, soft_warnings: list[str] | None = None,
                    category: str = "age", blocked_terms: list[str] | None = None):
    r = MagicMock()
    r.is_blocked = is_blocked
    r.soft_warnings = soft_warnings or []
    r.category = category
    r.blocked_terms = blocked_terms or []
    r.educational_message = "Termos discriminatórios detectados."
    return r


def _make_mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


class TestImportJdFairnessGuard:

    def _run_import_jd(self, jd_data: dict, fg_result) -> tuple[object | None, Exception | None]:
        from uuid import uuid4
        from app.domains.job_management.services.jd_import_service import JDImportService

        svc = JDImportService.__new__(JDImportService)
        svc.parse_jd = MagicMock(return_value={})
        svc._apply_parsed_data = MagicMock()
        mock_db = _make_mock_db()

        async def _run():
            with patch(_FG_PATH, return_value=MagicMock(check=MagicMock(return_value=fg_result))):
                return await svc.import_jd(
                    db=mock_db, company_id=uuid4(), jd_data=jd_data,
                    source="spreadsheet", parse_immediately=False,
                )

        try:
            return asyncio.run(_run()), None
        except Exception as e:
            return None, e

    def test_clean_jd_passes_unchanged(self):
        fg_clean = _make_fg_result(is_blocked=False, soft_warnings=[])
        jd = {"title": "Backend Engineer", "salary_min": 10000, "department": "Engineering",
              "seniority": "Senior", "skills": ["Python"]}
        imported, exc = self._run_import_jd(jd, fg_clean)
        assert exc is None, f"Clean JD should not raise: {exc}"
        assert imported is not None
        assert imported.is_used_for_learning is True, (
            "Clean JD com quality_score >= 0.65 deve ter is_used_for_learning=True. "
            "FairnessGuard não deve alterar."
        )

    def test_hard_blocked_jd_raises_and_sets_learning_false(self):
        fg_blocked = _make_fg_result(
            is_blocked=True, category="age", blocked_terms=["jovens dinâmicos"]
        )
        jd = {"title": "Dev", "salary_min": 8000, "department": "Tech",
              "seniority": "Junior", "description": "Buscamos jovens dinâmicos"}
        imported, exc = self._run_import_jd(jd, fg_blocked)
        assert exc is not None, (
            "JD hard-blocked deve levantar ValueError para que import_batch_jds marque "
            "o item como failed. Adicione `raise ValueError('fairness_blocked ...')` em import_jd()."
        )
        assert "fairness_blocked" in str(exc).lower(), (
            f"ValueError deve conter 'fairness_blocked', recebeu: {exc}"
        )

    def test_hard_blocked_propagates_to_batch_errors(self):
        """ValueError de FairnessGuard deve aparecer em batch.errors."""
        from uuid import uuid4
        from app.domains.job_management.services.jd_import_service import JDImportService

        fg_blocked = _make_fg_result(is_blocked=True, category="age", blocked_terms=["jovem"])
        mock_batch = MagicMock(
            id=uuid4(), status="pending", total_records=1,
            successful_records=0, failed_records=0, processed_records=0,
            errors=[], completed_at=None,
        )

        svc = JDImportService.__new__(JDImportService)
        svc.parse_jd = MagicMock(return_value={})
        svc._apply_parsed_data = MagicMock()
        svc._update_skill_catalog = AsyncMock()
        svc.create_import_batch = AsyncMock(return_value=mock_batch)

        mock_db = _make_mock_db()
        jds_data = [{"title": "Dev", "salary_min": 9000, "seniority": "Junior",
                     "department": "Tech", "description": "Buscamos jovens"}]

        async def _run():
            with patch(_FG_PATH, return_value=MagicMock(check=MagicMock(return_value=fg_blocked))):
                return await svc.import_batch_jds(
                    db=mock_db, company_id=uuid4(),
                    jds_data=jds_data, source="spreadsheet",
                )

        batch = asyncio.run(_run())
        assert batch.failed_records == 1, (
            f"JD bloqueada pelo FairnessGuard deve contar como failed_records=1, "
            f"recebeu {batch.failed_records}."
        )
        assert batch.successful_records == 0
        assert any("fairness" in str(e.get("error", "")).lower() for e in (batch.errors or [])), (
            "batch.errors deve ter entrada com 'fairness_blocked' para a JD bloqueada."
        )

    def test_soft_warning_sets_learning_false_no_raise(self):
        fg_warnings = _make_fg_result(is_blocked=False, soft_warnings=["linguagem generificada"])
        jd = {"title": "Dev", "salary_min": 8000, "department": "Tech",
              "seniority": "Senior", "description": "Perfil ideal: determinado e agressivo"}
        imported, exc = self._run_import_jd(jd, fg_warnings)
        assert exc is None, (
            f"JD com soft warnings NÃO deve levantar — item é importado, apenas excluído "
            f"do aprendizado. Recebeu: {exc}"
        )
        assert imported is not None
        assert imported.is_used_for_learning is False, (
            "JD com soft warnings de FairnessGuard deve ter is_used_for_learning=False. "
            "Viés implícito não deve contaminar o learning loop."
        )

    def test_fairness_guard_crash_is_fail_open(self):
        """Crash no FairnessGuard não deve interromper o import."""
        from uuid import uuid4
        from app.domains.job_management.services.jd_import_service import JDImportService

        svc = JDImportService.__new__(JDImportService)
        svc.parse_jd = MagicMock(return_value={})
        svc._apply_parsed_data = MagicMock()
        mock_db = _make_mock_db()
        jd = {"title": "Engineer", "salary_min": 10000, "department": "Engineering",
              "seniority": "Senior", "skills": ["Python"]}

        async def _run():
            with patch(_FG_PATH, side_effect=Exception("guard crashed")):
                return await svc.import_jd(
                    db=mock_db, company_id=uuid4(), jd_data=jd,
                    source="spreadsheet", parse_immediately=False,
                )

        imported, exc = None, None
        try:
            imported = asyncio.run(_run())
        except Exception as e:
            exc = e

        assert exc is None, (
            f"Crash no FairnessGuard deve ser fail-open (não levantar): {exc}. "
            "Adicione `except Exception: logger.warning(...)` ao redor do guard."
        )
        assert imported.is_used_for_learning is True, (
            "Crash do guard não deve afetar is_used_for_learning definido pelo quality gate."
        )


class TestSkillCatalogFairnessFilter:
    """_update_skill_catalog deve excluir JDs com is_used_for_learning=False."""

    def test_query_filters_by_is_used_for_learning(self):
        import inspect
        from app.domains.job_management.services.jd_import_service import JDImportService

        source = inspect.getsource(JDImportService._update_skill_catalog)
        assert "is_used_for_learning" in source, (
            "_update_skill_catalog deve filtrar por is_used_for_learning. "
            "JDs bloqueadas pelo FairnessGuard contaminariam o catálogo de skills. "
            "Adicione `ImportedJobDescription.is_used_for_learning.is_(True)` no WHERE."
        )
