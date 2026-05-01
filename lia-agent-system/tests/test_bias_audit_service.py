"""
Testes — Bias Audit Service (E.2)

Verifica cálculo de adverse impact real (Four-Fifths Rule) por dimensão demográfica:
- Sem candidatos → total=0
- Adverse impact acima do limiar (gender)
- Adverse impact perfeito (disability)
- Abaixo do limiar → alert_level warning
- Faixas etárias corretas
- Sem PII no relatório
- Contagem total correta
- has_alerts quando qualquer dimensão abaixo do limiar
"""
import pytest
from dataclasses import dataclass
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.shared.services.bias_audit_service import (
    BiasAuditService,
    BiasAuditReport,
    DemographicAuditResult,
    APPROVAL_THRESHOLD,
    FOUR_FIFTHS_THRESHOLD,
    _age_group,
    _adverse_impact_ratio,
    AGE_GROUP_YOUNG,
    AGE_GROUP_MID,
    AGE_GROUP_SENIOR,
)

JOB_ID = uuid4()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_evaluation(score: float, candidate_id=None) -> MagicMock:
    e = MagicMock()
    e.score = score
    e.job_vacancy_id = JOB_ID
    e.candidate_id = candidate_id or uuid4()
    return e


def _mock_candidate(
    gender=None,
    dob=None,
    disability=False,
    state=None,
) -> MagicMock:
    c = MagicMock()
    c.id = uuid4()
    c.gender = gender
    c.date_of_birth = dob
    c.diversity_disability = disability
    c.location_state = state
    return c


def _make_rows(pairs: list[tuple]) -> list:
    """Transforma pares (evaluation, candidate) em rows simulados."""
    rows = []
    for e, c in pairs:
        row = MagicMock()
        row.__getitem__ = lambda self, i: (e, c)[i]
        rows.append(row)
    return rows


async def _stub_db_execute(pairs: list[tuple]) -> AsyncMock:
    """Retorna AsyncMock de db.execute() com .all() produzindo os pares."""
    rows = [(e, c) for e, c in pairs]
    result_mock = MagicMock()
    result_mock.all.return_value = rows
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result_mock)
    return db


# ---------------------------------------------------------------------------
# Testes unitários — funções auxiliares
# ---------------------------------------------------------------------------

class TestAgeGroup:
    def test_young(self):
        dob = date(2000, 1, 1)
        assert _age_group(dob) == AGE_GROUP_YOUNG

    def test_mid(self):
        dob = date(1985, 6, 15)
        assert _age_group(dob) == AGE_GROUP_MID

    def test_senior(self):
        dob = date(1975, 3, 20)
        assert _age_group(dob) == AGE_GROUP_SENIOR

    def test_none_returns_not_informed(self):
        assert _age_group(None) == "não informado"


class TestAdverseImpactRatio:
    def test_ratio_calculation(self):
        groups = {
            "A": {"count": 10, "approved": 8, "rate": 0.8},
            "B": {"count": 10, "approved": 4, "rate": 0.4},
        }
        ratio = _adverse_impact_ratio(groups)
        assert ratio == 0.5  # 0.4 / 0.8

    def test_single_group_returns_one(self):
        groups = {"A": {"count": 5, "approved": 3, "rate": 0.6}}
        assert _adverse_impact_ratio(groups) == 1.0

    def test_empty_groups_returns_one(self):
        assert _adverse_impact_ratio({}) == 1.0


# ---------------------------------------------------------------------------
# Testes de integração — BiasAuditService
# ---------------------------------------------------------------------------

class TestBiasAuditService:

    @pytest.mark.asyncio
    async def test_empty_job_returns_zero_candidates(self):
        """Vaga sem avaliações → total_candidates=0, dimensões vazias."""
        db = await _stub_db_execute([])
        svc = BiasAuditService()
        report = await svc.get_adverse_impact_by_job(db, JOB_ID)

        assert report.total_candidates == 0
        assert report.dimensions == []
        assert report.has_alerts is False

    @pytest.mark.asyncio
    async def test_gender_adverse_impact_above_threshold(self):
        """Gênero com taxas equivalentes → ratio >= 0.80, sem alerta."""
        pairs = [
            (_mock_evaluation(70.0), _mock_candidate(gender="masculino")),
            (_mock_evaluation(75.0), _mock_candidate(gender="masculino")),
            (_mock_evaluation(72.0), _mock_candidate(gender="feminino")),
            (_mock_evaluation(68.0), _mock_candidate(gender="feminino")),
        ]
        db = await _stub_db_execute(pairs)
        svc = BiasAuditService()
        report = await svc.get_adverse_impact_by_job(db, JOB_ID)

        gender_dim = next(d for d in report.dimensions if d.dimension == "gender")
        assert gender_dim.adverse_impact_ratio >= FOUR_FIFTHS_THRESHOLD
        assert gender_dim.alert_level == "ok"
        assert gender_dim.below_threshold is False

    @pytest.mark.asyncio
    async def test_disability_adverse_impact_perfect(self):
        """PCD e sem PCD com mesma taxa → ratio=1.0."""
        pairs = [
            (_mock_evaluation(80.0), _mock_candidate(disability=True)),
            (_mock_evaluation(80.0), _mock_candidate(disability=False)),
        ]
        db = await _stub_db_execute(pairs)
        svc = BiasAuditService()
        report = await svc.get_adverse_impact_by_job(db, JOB_ID)

        disability_dim = next(d for d in report.dimensions if d.dimension == "disability")
        assert disability_dim.adverse_impact_ratio == 1.0
        assert disability_dim.alert_level == "ok"

    @pytest.mark.asyncio
    async def test_below_threshold_sets_alert(self):
        """Ratio < 0.80 → below_threshold=True, alert_level=warning."""
        # Grupo A: 10/10 aprovados (100%), Grupo B: 2/10 aprovados (20%) → ratio=0.2
        pairs = []
        for _ in range(10):
            pairs.append((_mock_evaluation(80.0), _mock_candidate(gender="masculino")))
        for _ in range(8):
            pairs.append((_mock_evaluation(40.0), _mock_candidate(gender="feminino")))  # reprovados
        for _ in range(2):
            pairs.append((_mock_evaluation(80.0), _mock_candidate(gender="feminino")))  # aprovados

        db = await _stub_db_execute(pairs)
        svc = BiasAuditService()
        report = await svc.get_adverse_impact_by_job(db, JOB_ID)

        gender_dim = next(d for d in report.dimensions if d.dimension == "gender")
        assert gender_dim.below_threshold is True
        assert gender_dim.alert_level == "warning"
        assert report.has_alerts is True

    @pytest.mark.asyncio
    async def test_age_grouping_correct(self):
        """Candidatos de diferentes idades são corretamente agrupados."""
        pairs = [
            (_mock_evaluation(70.0), _mock_candidate(dob=date(2000, 1, 1))),   # <30
            (_mock_evaluation(70.0), _mock_candidate(dob=date(1985, 1, 1))),   # 30-44
            (_mock_evaluation(70.0), _mock_candidate(dob=date(1975, 1, 1))),   # 45+
        ]
        db = await _stub_db_execute(pairs)
        svc = BiasAuditService()
        report = await svc.get_adverse_impact_by_job(db, JOB_ID)

        age_dim = next(d for d in report.dimensions if d.dimension == "age_group")
        assert AGE_GROUP_YOUNG in age_dim.groups
        assert AGE_GROUP_MID in age_dim.groups
        assert AGE_GROUP_SENIOR in age_dim.groups

    @pytest.mark.asyncio
    async def test_no_pii_in_report(self):
        """Relatório não deve conter IDs individuais de candidatos."""
        pairs = [
            (_mock_evaluation(75.0), _mock_candidate(gender="masculino")),
            (_mock_evaluation(65.0), _mock_candidate(gender="feminino")),
        ]
        db = await _stub_db_execute(pairs)
        svc = BiasAuditService()
        report = await svc.get_adverse_impact_by_job(db, JOB_ID)

        report_dict = {
            "job_id": report.job_id,
            "total_candidates": report.total_candidates,
            "dimensions": [
                {"dimension": d.dimension, "groups": d.groups}
                for d in report.dimensions
            ],
        }
        report_str = str(report_dict)
        # Não deve conter UUIDs de candidatos individuais
        for _, c in pairs:
            assert str(c.id) not in report_str

    @pytest.mark.asyncio
    async def test_total_candidates_count(self):
        """total_candidates deve refletir o número de avaliações na vaga."""
        pairs = [
            (_mock_evaluation(70.0), _mock_candidate()),
            (_mock_evaluation(55.0), _mock_candidate()),
            (_mock_evaluation(80.0), _mock_candidate()),
        ]
        db = await _stub_db_execute(pairs)
        svc = BiasAuditService()
        report = await svc.get_adverse_impact_by_job(db, JOB_ID)

        assert report.total_candidates == 3

    @pytest.mark.asyncio
    async def test_has_alerts_when_any_dimension_below_threshold(self):
        """has_alerts=True quando pelo menos uma dimensão está abaixo de 0.80."""
        # Gênero com ratio crítico (0.2) mas disability OK
        pairs = []
        for _ in range(10):
            pairs.append((_mock_evaluation(80.0), _mock_candidate(
                gender="masculino", disability=False
            )))
        for _ in range(10):
            pairs.append((_mock_evaluation(30.0), _mock_candidate(
                gender="feminino", disability=False
            )))

        db = await _stub_db_execute(pairs)
        svc = BiasAuditService()
        report = await svc.get_adverse_impact_by_job(db, JOB_ID)

        assert report.has_alerts is True
        # Ao menos uma dimensão com alerta
        assert any(d.alert_level == "warning" for d in report.dimensions)
