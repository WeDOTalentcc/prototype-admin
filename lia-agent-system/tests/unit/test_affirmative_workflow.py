"""
Onda 2C.3 — workflow de documento de ação afirmativa (revival async + compliance).

Testes puros (in-memory) das partes determinísticas: elegibilidade, tipos de documento,
verdict do hard-gate, e o registro do consent purpose. (O CRUD async é validado por
py_compile + review; roundtrip real contra DB fica como follow-up — ver commit.)
"""
from types import SimpleNamespace

from app.shared.services.affirmative_service import (
    AffirmativeService,
    affirmative_advancement_verdict,
    AFFIRMATIVE_CONSENT_PURPOSE,
)


def _svc():
    return AffirmativeService(db=None)


class TestEligibility:
    def test_non_affirmative_vacancy_is_eligible(self):
        vac = SimpleNamespace(is_affirmative=False, affirmative_criteria_primary=None, affirmative_criteria_secondary=None)
        r = _svc().check_candidate_eligibility(SimpleNamespace(), vac)
        assert r["eligible"] is True

    def test_affirmative_race_matching_candidate(self):
        vac = SimpleNamespace(is_affirmative=True, affirmative_criteria_primary="race_ethnicity", affirmative_criteria_secondary=None)
        cand = SimpleNamespace(
            gender=None, diversity_race_ethnicity="parda", diversity_disability=False,
            diversity_age_50_plus=False, diversity_lgbtqia=False, diversity_refugee=False,
            diversity_indigenous=False,
        )
        r = _svc().check_candidate_eligibility(cand, vac)
        assert r["eligible"] is True
        assert r["requires_document"] is True
        assert "autodeclaracao_racial" in r["document_types"]

    def test_affirmative_non_matching_candidate(self):
        vac = SimpleNamespace(is_affirmative=True, affirmative_criteria_primary="disability", affirmative_criteria_secondary=None)
        cand = SimpleNamespace(
            gender=None, diversity_race_ethnicity=None, diversity_disability=False,
            diversity_age_50_plus=False, diversity_lgbtqia=False, diversity_refugee=False,
            diversity_indigenous=False,
        )
        r = _svc().check_candidate_eligibility(cand, vac)
        assert r["eligible"] is False


class TestDocTypes:
    def test_disability_doc_types(self):
        dt = _svc()._get_required_document_types("disability")
        assert "laudo_pcd" in dt and "certificado_reabilitacao" in dt

    def test_combined_dedupes(self):
        # gender + lgbtqia ambos mapeiam para 'autodeclaracao' -> deduplicado.
        dt = _svc()._get_required_document_types("gender", "lgbtqia")
        assert dt.count("autodeclaracao") == 1


class TestAdvancementVerdict:
    def test_permit_when_approved_and_recruiter_verified(self):
        assert affirmative_advancement_verdict("approved", True, False) == "permit"

    def test_rejected(self):
        assert affirmative_advancement_verdict("rejected", True, False) == "rejected"

    def test_unverified(self):
        assert affirmative_advancement_verdict("pending_verification", False, False) == "unverified"

    def test_expired_by_status_or_flag(self):
        assert affirmative_advancement_verdict("expired", False, True) == "expired"
        assert affirmative_advancement_verdict("pending_upload", False, True) == "expired"

    def test_approved_but_not_recruiter_verified_is_unverified(self):
        assert affirmative_advancement_verdict("approved", False, False) == "unverified"


class TestConsentPurpose:
    def test_affirmative_purpose_registered(self):
        from app.domains.lgpd.services.consent_checker_service import ConsentCheckerService
        assert AFFIRMATIVE_CONSENT_PURPOSE == "affirmative_verification"
        assert "affirmative_verification" in ConsentCheckerService.AI_PURPOSES
        assert ConsentCheckerService.PURPOSE_TO_CONSENT_TYPE["affirmative_verification"] == "AFFIRMATIVE_SENSITIVE_DATA"
