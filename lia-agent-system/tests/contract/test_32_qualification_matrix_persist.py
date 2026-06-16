"""
3.2: Derivar e persistir QualificationMatrix on-the-fly apos triagem.

Garante que:
1. VacancyCandidateRepository tem update_qualification_matrix
2. update_qualification_matrix faz JSONB merge em ai_analysis
3. completion.py bloco 3.2 invoca derive_from_job + update_qualification_matrix
4. fail-soft: excecao nao quebra o fluxo
5. matrix serializada inclui must_have_met/must_have_total
"""
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestQualificationMatrixPersist:
    """3.2: persist on-the-fly apos triagem."""

    def test_vacancy_candidate_repo_has_update_qualification_matrix(self):
        from app.domains.candidates.repositories.vacancy_candidate_repository import (
            VacancyCandidateRepository,
        )
        assert hasattr(VacancyCandidateRepository, "update_qualification_matrix")

    @pytest.mark.asyncio
    async def test_update_qualification_matrix_writes_to_jsonb(self):
        from app.domains.candidates.repositories.vacancy_candidate_repository import (
            VacancyCandidateRepository,
        )
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(rowcount=1))
        repo = VacancyCandidateRepository(db)
        rows = await repo.update_qualification_matrix(
            vacancy_id="vac-1",
            candidate_id="cand-1",
            company_id="comp-1",
            qualification_matrix={"must_have_met": 2, "must_have_total": 3, "criteria": []},
        )
        assert rows == 1
        db.execute.assert_called_once()
        call_args = db.execute.call_args
        sql = str(call_args[0][0]) if call_args[0] else str(call_args.args[0])
        assert "ai_analysis" in sql.lower()

    @pytest.mark.asyncio
    async def test_completion_block_32_invoked(self):
        """completion.py bloco 3.2 chama derive_from_job + update_qualification_matrix."""
        import importlib
        mod = importlib.import_module(
            "app.domains.recruitment.services.triagem_session_service.completion"
        )
        src = open(mod.__file__).read()
        assert "derive_from_job" in src, "completion.py deve importar derive_from_job"
        assert "update_qualification_matrix" in src, "completion.py deve chamar update_qualification_matrix"
        assert "qualification_matrix_persist" in src, "completion.py deve registrar em actions"

    @pytest.mark.asyncio
    async def test_completion_block_32_is_fail_soft(self):
        """Bloco 3.2 e fail-soft — erro nao propaga."""
        import importlib
        mod = importlib.import_module(
            "app.domains.recruitment.services.triagem_session_service.completion"
        )
        src = open(mod.__file__).read()
        # Deve ter try/except com "failed" no bloco 3.2
        assert '# 3.2:' in src
        assert 'qualification_matrix_persist"] = "failed"' in src

    def test_matrix_serialized_includes_must_have_counts(self):
        """Matrix serializada contem must_have_met e must_have_total."""
        from app.schemas.qualification_matrix import QualificationCriterion, QualificationMatrix
        matrix = QualificationMatrix.build(
            mode="grouped",
            criteria=[
                QualificationCriterion(
                    id="mh1", label="Python", group="must_have",
                    status="met", provenance="resume", confidence=1.0,
                ),
                QualificationCriterion(
                    id="mh2", label="Docker", group="must_have",
                    status="not_met", provenance="resume", confidence=1.0,
                ),
            ],
        )
        d = matrix.model_dump()
        assert d["must_have_met"] == 1
        assert d["must_have_total"] == 2
