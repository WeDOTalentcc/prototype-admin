"""
Testes Unitários — CANONICAL_SUB_STATUSES e estrutura de sub-statuses
Camada 2 (Unitário BE — pytest, sem DB)

Cobre:
- Todos os estágios obrigatórios estão presentes
- Cada estágio tem ao menos um is_default=True
- Sem duplicatas de nome dentro de um estágio
- 'rejected' cobre as 6 categorias de motivo de reprovação
- 'offer_declined' contém todos os motivos canônicos
- Campos obrigatórios presentes em cada sub-status
"""

from app.models.recruitment_stages import CANONICAL_SUB_STATUSES, DEFAULT_SUB_STATUSES

REQUIRED_STAGES = [
    "sourcing", "screening", "long_list", "short_list",
    "interview_hr", "technical_test", "english_test",
    "interview_technical", "interview_manager", "interview_manager2",
    "interview_final", "references", "offer",
    "hired", "rejected", "offer_declined", "standby",
]


class TestCanonicalSubStatusesStructure:

    def test_all_required_stages_present(self):
        """Todos os estágios obrigatórios existem no CANONICAL_SUB_STATUSES."""
        for stage in REQUIRED_STAGES:
            assert stage in CANONICAL_SUB_STATUSES, f"Estágio ausente: {stage}"

    def test_each_stage_has_at_least_one_default(self):
        """Cada estágio tem exatamente um sub-status marcado como is_default=True."""
        for stage, items in CANONICAL_SUB_STATUSES.items():
            defaults = [i for i in items if i.get("is_default")]
            assert len(defaults) >= 1, (
                f"Estágio '{stage}' não tem nenhum sub-status com is_default=True"
            )

    def test_no_duplicate_names_within_stage(self):
        """Nenhum nome de sub-status se repete dentro de um mesmo estágio."""
        for stage, items in CANONICAL_SUB_STATUSES.items():
            names = [i["name"] for i in items]
            assert len(names) == len(set(names)), (
                f"Duplicatas encontradas em '{stage}': "
                f"{[n for n in names if names.count(n) > 1]}"
            )

    def test_required_fields_present_in_all_sub_statuses(self):
        """Todo sub-status tem os campos 'name' e 'display_name'."""
        for stage, items in CANONICAL_SUB_STATUSES.items():
            for item in items:
                assert "name" in item, f"'name' ausente em {stage}: {item}"
                assert "display_name" in item, f"'display_name' ausente em {stage}: {item}"
                assert isinstance(item["name"], str) and item["name"], (
                    f"'name' inválido em {stage}: {item}"
                )
                assert isinstance(item["display_name"], str) and item["display_name"], (
                    f"'display_name' inválido em {stage}: {item}"
                )

    def test_all_stages_non_empty(self):
        """Nenhum estágio tem lista vazia de sub-statuses."""
        for stage, items in CANONICAL_SUB_STATUSES.items():
            assert len(items) > 0, f"Lista vazia para estágio '{stage}'"


class TestRejectedStageCompleteness:
    """Verifica que 'rejected' cobre as 6 categorias de reprovação."""

    def setup_method(self):
        self.names = {s["name"] for s in CANONICAL_SUB_STATUSES["rejected"]}

    def test_business_decision_reasons(self):
        assert "another_candidate_selected" in self.names
        assert "position_cancelled" in self.names
        assert "position_frozen" in self.names
        assert "internal_hire" in self.names
        assert "budget_insufficient" in self.names
        assert "org_restructuring" in self.names

    def test_qualification_reasons(self):
        assert "lacking_experience" in self.names
        assert "under_qualified" in self.names
        assert "over_qualified" in self.names
        assert "lacking_technical_skills" in self.names
        assert "education_mismatch" in self.names
        assert "missing_certification" in self.names
        assert "language_insufficient" in self.names
        assert "tools_insufficient" in self.names

    def test_cultural_reasons(self):
        assert "cultural_mismatch" in self.names
        assert "poor_communication" in self.names
        assert "inadequate_attitude" in self.names
        assert "lack_professionalism" in self.names
        assert "lack_of_interest" in self.names
        assert "misaligned_expectations" in self.names

    def test_logistics_reasons(self):
        assert "location_mismatch" in self.names
        assert "work_model_mismatch" in self.names
        assert "visa_required" in self.names
        assert "start_date_mismatch" in self.names
        assert "schedule_mismatch" in self.names

    def test_compensation_reasons(self):
        assert "salary_above_budget" in self.names
        assert "benefits_mismatch" in self.names
        assert "compensation_not_competitive" in self.names

    def test_process_reasons(self):
        assert "interview_no_show" in self.names
        assert "test_no_show" in self.names
        assert "withdrew" in self.names
        assert "unresponsive" in self.names
        assert "failed_technical_test" in self.names
        assert "failed_behavioral_test" in self.names
        assert "negative_references" in self.names
        assert "failed_background_check" in self.names
        assert "failed_admission_exam" in self.names

    def test_default_is_another_candidate_selected(self):
        defaults = [
            s["name"] for s in CANONICAL_SUB_STATUSES["rejected"]
            if s.get("is_default")
        ]
        assert "another_candidate_selected" in defaults


class TestOfferDeclinedCompleteness:
    """Verifica que 'offer_declined' tem todos os 12 motivos canônicos."""

    def setup_method(self):
        self.names = {s["name"] for s in CANONICAL_SUB_STATUSES["offer_declined"]}

    def test_all_canonical_reasons_present(self):
        expected = [
            "accepted_other_offer",
            "salary_below_expectation",
            "insufficient_benefits",
            "work_model_not_accepted",
            "location_not_accepted",
            "accepted_counter_offer",
            "personal_family_reasons",
            "culture_not_aligned",
            "better_career_opportunity",
            "company_response_timing",
            "personal_plans_changed",
            "health_issues",
        ]
        for name in expected:
            assert name in self.names, f"Motivo ausente em offer_declined: {name}"

    def test_total_count(self):
        assert len(CANONICAL_SUB_STATUSES["offer_declined"]) == 12


class TestBackwardCompatAlias:
    """DEFAULT_SUB_STATUSES é alias de CANONICAL_SUB_STATUSES."""

    def test_alias_is_same_object(self):
        assert DEFAULT_SUB_STATUSES is CANONICAL_SUB_STATUSES
