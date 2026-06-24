"""
Sensores da derivação da matriz de qualificação (fonte vaga + fonte busca).

Pinam:
- eligibility eliminatória → must_have (via shape canônico)
- skills met/not_met determinístico
- busca = lista plana (mode='flat', group='criteria')
- proveniência presente em todo critério
- invariantes de honestidade: partial⇒is_inference; provenance='none'⇒status='unknown'
"""
from app.domains.analytics.services.criteria_derivation import (
    derive_from_job,
    derive_from_search,
)


CANDIDATE = {
    "technical_skills": ["Python", "FastAPI", "PostgreSQL"],
    "seniority_level": "Pleno",
    "years_of_experience": 5,
    "location_city": "São Paulo",
    "location_state": "SP",
    "location_country": "Brasil",
    "languages": ["Português", "Inglês"],
    "current_title": "Product Manager",
}


class TestDeriveFromJob:
    def test_eliminatory_eligibility_becomes_must_have(self):
        job = {}
        eligibility = [
            {"id": "q1", "question": "Tem CNH?", "is_eliminatory": True,
             "expected_answer": "sim", "candidate_answer": "sim"},
        ]
        matrix = derive_from_job(job, CANDIDATE, eligibility)
        assert matrix.mode == "grouped"
        elig = [c for c in matrix.criteria if c.id == "elig:q1"]
        assert len(elig) == 1
        assert elig[0].group == "must_have"
        assert elig[0].status == "met"
        assert elig[0].provenance == "eligibility"

    def test_eligibility_without_answer_is_unknown(self):
        job = {}
        eligibility = [
            {"id": "q1", "question": "Aceita presencial?", "is_eliminatory": True,
             "expected_answer": "sim", "candidate_answer": None},
        ]
        matrix = derive_from_job(job, CANDIDATE, eligibility)
        c = matrix.criteria[0]
        assert c.status == "unknown"
        assert c.provenance == "none"

    def test_required_tech_is_must_have_and_evaluated(self):
        job = {"technical_requirements": [
            {"technology": "Python", "required": True},
            {"technology": "Go", "required": False},
        ]}
        matrix = derive_from_job(job, CANDIDATE, [])
        py = next(c for c in matrix.criteria if c.id == "tech:python")
        go = next(c for c in matrix.criteria if c.id == "tech:go")
        assert py.group == "must_have" and py.status == "met"
        assert go.group == "preferred" and go.status == "not_met"

    def test_essential_behavioral_is_must_have_but_unknown(self):
        job = {"behavioral_competencies": [{"competency": "Liderança", "weight": "Essencial"}]}
        matrix = derive_from_job(job, CANDIDATE, [])
        c = matrix.criteria[0]
        assert c.group == "must_have"
        assert c.status == "unknown"  # fuzzy, sem fabricar


class TestDeriveFromSearch:
    def test_flat_mode_no_grouping(self):
        filters = {"required_skills": ["Python"], "seniority_levels": ["Pleno"]}
        matrix = derive_from_search(filters, CANDIDATE)
        assert matrix.mode == "flat"
        assert all(c.group == "criteria" for c in matrix.criteria)

    def test_skill_met_and_missing(self):
        filters = {"required_skills": ["Python", "Kubernetes"]}
        matrix = derive_from_search(filters, CANDIDATE)
        py = next(c for c in matrix.criteria if c.id == "skill:python")
        k8s = next(c for c in matrix.criteria if c.id == "skill:kubernetes")
        assert py.status == "met"
        assert k8s.status == "not_met"

    def test_location_and_years_and_title(self):
        filters = {"locations": ["São Paulo"], "min_years_experience": 3, "titles": ["Product Manager"]}
        matrix = derive_from_search(filters, CANDIDATE)
        loc = next(c for c in matrix.criteria if c.id == "location")
        yrs = next(c for c in matrix.criteria if c.id == "min_years")
        title = next(c for c in matrix.criteria if c.id.startswith("title:"))
        assert loc.status == "met"
        assert yrs.status == "met"
        assert title.status == "met"

    def test_overall_label_counts(self):
        filters = {"required_skills": ["Python", "Kubernetes"]}
        matrix = derive_from_search(filters, CANDIDATE)
        assert matrix.total_count == 2
        assert matrix.met_count == 1
        assert "1/2" in matrix.overall_label


class TestHonestyInvariants:
    def test_every_criterion_has_provenance(self):
        job = {
            "technical_requirements": [{"technology": "Python", "required": True}],
            "behavioral_competencies": [{"competency": "Liderança", "weight": "Essencial"}],
            "requirements": ["Disponibilidade para viagens"],
        }
        eligibility = [{"id": "q1", "question": "Tem CNH?", "is_eliminatory": True,
                        "expected_answer": "sim", "candidate_answer": "sim"}]
        matrix = derive_from_job(job, CANDIDATE, eligibility)
        for c in matrix.criteria:
            assert c.provenance is not None and c.provenance != ""

    def test_partial_implies_inference(self):
        # senioridade um nível abaixo → partial
        cand = {**CANDIDATE, "seniority_level": "Júnior"}
        filters = {"seniority_levels": ["Pleno"]}
        matrix = derive_from_search(filters, cand)
        c = matrix.criteria[0]
        assert c.status == "partial"
        assert c.is_inference is True

    def test_provenance_none_forces_unknown(self):
        from app.schemas.qualification_matrix import QualificationCriterion
        c = QualificationCriterion(
            id="x", label="x", group="criteria", status="met", provenance="none"
        )
        # invariante: sem fonte não pode afirmar 'met'
        assert c.status == "unknown"
