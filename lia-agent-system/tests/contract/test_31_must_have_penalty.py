"""
3.1: must_have criteria penalizam o prerequisites_score no ranking.

Garante que:
1. must_have_prerequisites_score() existe em lia_score_service
2. 0/N must_haves met → prerequisites_score = 0
3. K/N must_haves met → prerequisites_score = K/N * 100
4. matrix sem must_haves → prerequisites_score = 100 (nenhuma penalidade)
5. calculate_ranking_score aceita must_have_score kwarg
6. Qualificação must_have parcial reduz ranking_score final vs. sem penalidade
"""
from __future__ import annotations
import pytest


def _make_matrix(must_have_met: int, must_have_total: int, preferred_met: int = 0, preferred_total: int = 0):
    from app.schemas.qualification_matrix import QualificationCriterion, QualificationMatrix
    criteria = []
    for i in range(must_have_total):
        st = "met" if i < must_have_met else "not_met"
        prov = "resume"
        criteria.append(
            QualificationCriterion(
                id=f"mh_{i}", label=f"Must-have {i}", group="must_have",
                status=st, provenance=prov, confidence=1.0,
            )
        )
    for j in range(preferred_total):
        st = "met" if j < preferred_met else "unknown"
        criteria.append(
            QualificationCriterion(
                id=f"pref_{j}", label=f"Preferred {j}", group="preferred",
                status=st, provenance="resume" if st == "met" else "none", confidence=0.8 if st == "met" else 0.0,
            )
        )
    return QualificationMatrix.build(mode="grouped", criteria=criteria)


class TestMustHavePenalty:
    """3.1: must_have penaliza prerequisites_score."""

    def test_must_have_prerequisites_score_exists(self):
        from app.domains.cv_screening.services.lia_score_service import must_have_prerequisites_score
        assert callable(must_have_prerequisites_score)

    def test_zero_must_haves_met_gives_zero_score(self):
        from app.domains.cv_screening.services.lia_score_service import must_have_prerequisites_score
        matrix = _make_matrix(must_have_met=0, must_have_total=3)
        assert must_have_prerequisites_score(matrix) == 0.0

    def test_all_must_haves_met_gives_100(self):
        from app.domains.cv_screening.services.lia_score_service import must_have_prerequisites_score
        matrix = _make_matrix(must_have_met=3, must_have_total=3)
        assert must_have_prerequisites_score(matrix) == 100.0

    def test_partial_must_haves_gives_proportional_score(self):
        from app.domains.cv_screening.services.lia_score_service import must_have_prerequisites_score
        matrix = _make_matrix(must_have_met=2, must_have_total=4)
        assert must_have_prerequisites_score(matrix) == pytest.approx(50.0)

    def test_no_must_haves_gives_100(self):
        """Vaga sem must_haves: nenhuma penalidade (score=100)."""
        from app.domains.cv_screening.services.lia_score_service import must_have_prerequisites_score
        matrix = _make_matrix(must_have_met=0, must_have_total=0, preferred_met=2, preferred_total=3)
        assert must_have_prerequisites_score(matrix) == 100.0

    def test_must_have_penalty_reduces_ranking_score(self):
        """ranking_score com 0/3 must_haves < ranking_score sem penalidade."""
        from app.domains.cv_screening.services.lia_score_service import get_lia_score_service
        svc = get_lia_score_service()
        # Sem penalidade (prerequisites_score=100)
        r_full = svc.calculate_ranking_score(
            candidate={"id": "cand-1"}, rubricas_score=80.0, prerequisites_score=100.0
        )
        # Com 0/3 must_haves
        matrix_fail = _make_matrix(must_have_met=0, must_have_total=3)
        r_penalized = svc.calculate_ranking_score(
            candidate={"id": "cand-1"}, rubricas_score=80.0, qualification_matrix=matrix_fail
        )
        assert r_penalized.ranking_score < r_full.ranking_score, (
            f"Score penalizado ({r_penalized.ranking_score}) deve ser < score pleno ({r_full.ranking_score})"
        )
