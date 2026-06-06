"""
Onda 2C.2 — FairnessGuard ciente da exceção legítima de ação afirmativa.

Numa vaga afirmativa de critério X (raça/gênero/PCD/idade/LGBTQIA+), a AUTODECLARAÇÃO
do atributo protegido X é ESPERADA e PERMITIDA (CLT 373-A / LGPD Art. 20) — não deve ser
bloqueada pelo guard. Em qualquer outra vaga (ou critério divergente) o bloqueio permanece.
A exceção vive no middleware (onde o contexto da vaga flui); FairnessGuard.check() segue
job-agnóstico.
"""
from types import SimpleNamespace
from unittest.mock import patch

import app.shared.compliance.fairness_guard_middleware as mw
from app.shared.compliance.fairness_guard_middleware import (
    affirmative_exception_applies,
    check_fairness,
)


class TestAffirmativeExceptionApplies:
    def test_matching_criterion_and_category(self):
        assert affirmative_exception_applies("raca_etnia", "race_ethnicity") is True
        assert affirmative_exception_applies("genero", "gender") is True
        assert affirmative_exception_applies("deficiencia", "disability") is True
        assert affirmative_exception_applies("idade", "age") is True
        assert affirmative_exception_applies("orientacao_sexual", "lgbtqia") is True

    def test_mismatch_or_missing_does_not_apply(self):
        assert affirmative_exception_applies("raca_etnia", "gender") is False
        assert affirmative_exception_applies("raca_etnia", None) is False
        assert affirmative_exception_applies("raca_etnia", "") is False
        assert affirmative_exception_applies("genero", "other") is False
        assert affirmative_exception_applies(None, "gender") is False


def _blocked(category):
    return SimpleNamespace(
        is_blocked=True, category=category, blocked_terms=["x"],
        educational_message="msg", soft_warnings=[],
    )


class TestCheckFairnessAffirmativeException:
    def test_allows_self_declaration_in_matching_affirmative_vacancy(self):
        with patch.object(mw._fairness_guard, "check", return_value=_blocked("raca_etnia")):
            out = check_fairness(
                {"candidate_response": "sou pardo"},
                context="test",
                affirmative_criterion="race_ethnicity",
            )
        assert out.is_blocked is False
        assert any("affirmative_self_declaration_allowed" in w for w in out.warnings)

    def test_still_blocks_when_not_affirmative(self):
        with patch.object(mw._fairness_guard, "check", return_value=_blocked("raca_etnia")):
            out = check_fairness({"candidate_response": "x"}, context="test")
        assert out.is_blocked is True

    def test_still_blocks_when_criterion_mismatches(self):
        with patch.object(mw._fairness_guard, "check", return_value=_blocked("raca_etnia")):
            out = check_fairness(
                {"candidate_response": "x"}, context="test", affirmative_criterion="gender",
            )
        assert out.is_blocked is True
