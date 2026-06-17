"""Coverage tests for wizard_state.py — WizardState dataclass pure methods."""
import pytest
from app.orchestrator.guards.wizard_state import (
    WizardState,
    _redis_key,
    update_wizard_state_from_draft,
)


class TestWizardStateDefaults:
    def test_default_step_is_init(self):
        s = WizardState()
        assert s.step == "init"

    def test_default_strings_empty(self):
        s = WizardState()
        assert s.conversation_id == ""
        assert s.company_id == ""
        assert s.recruiter_id == ""

    def test_default_lists_empty(self):
        s = WizardState()
        assert s.skills == []
        assert s.confirmed_fields == []

    def test_default_optionals_none(self):
        s = WizardState()
        assert s.title is None
        assert s.department is None
        assert s.location is None
        assert s.salary_min is None
        assert s.salary_max is None
        assert s.seniority is None
        assert s.work_model is None
        assert s.description is None
        assert s.draft_id is None


class TestCollectedSummary:
    def test_empty_state_returns_default_message(self):
        s = WizardState()
        result = s.collected_summary()
        assert result == "Nenhum campo coletado ainda."

    def test_with_title_shows_titulo(self):
        s = WizardState(title="Backend Developer")
        result = s.collected_summary()
        assert "Backend Developer" in result
        assert "Titulo" in result

    def test_with_department_shows_departamento(self):
        s = WizardState(department="Engenharia")
        result = s.collected_summary()
        assert "Engenharia" in result
        assert "Departamento" in result

    def test_with_location(self):
        s = WizardState(location="São Paulo, SP")
        result = s.collected_summary()
        assert "São Paulo" in result

    def test_with_seniority(self):
        s = WizardState(seniority="Senior")
        result = s.collected_summary()
        assert "Senior" in result

    def test_with_work_model(self):
        s = WizardState(work_model="Remoto")
        result = s.collected_summary()
        assert "Remoto" in result

    def test_with_salary_range(self):
        s = WizardState(salary_min=8000.0, salary_max=12000.0)
        result = s.collected_summary()
        assert "8000" in result
        assert "12000" in result

    def test_with_only_salary_min(self):
        s = WizardState(salary_min=5000.0)
        result = s.collected_summary()
        assert "5000" in result

    def test_with_skills_up_to_5(self):
        s = WizardState(skills=["Python", "Django", "PostgreSQL", "Docker", "Redis", "FastAPI"])
        result = s.collected_summary()
        # At most 5 shown
        assert "Python" in result
        assert "FastAPI" not in result  # 6th item excluded

    def test_with_exactly_5_skills(self):
        s = WizardState(skills=["A", "B", "C", "D", "E"])
        result = s.collected_summary()
        assert "A" in result and "E" in result

    def test_multiline_result(self):
        s = WizardState(title="Dev", department="TI", location="SP")
        result = s.collected_summary()
        assert "\n" in result


class TestPendingFields:
    def test_empty_state_all_pending(self):
        s = WizardState()
        pending = s.pending_fields()
        assert len(pending) == 5
        assert "titulo da vaga" in pending
        assert "departamento" in pending
        assert "localizacao" in pending
        assert "nivel de senioridade" in pending
        assert "modelo de trabalho" in pending

    def test_with_title_removes_titulo(self):
        s = WizardState(title="Dev")
        pending = s.pending_fields()
        assert "titulo da vaga" not in pending

    def test_fully_filled_no_pending(self):
        s = WizardState(
            title="Dev",
            department="TI",
            location="SP",
            seniority="Senior",
            work_model="Remoto",
        )
        pending = s.pending_fields()
        assert pending == []

    def test_returns_list(self):
        s = WizardState()
        assert isinstance(s.pending_fields(), list)


class TestToPromptSnippet:
    def test_returns_string(self):
        s = WizardState()
        result = s.to_prompt_snippet()
        assert isinstance(result, str)

    def test_contains_estado_wizard_header(self):
        s = WizardState()
        result = s.to_prompt_snippet()
        assert "Estado do Wizard de Vaga" in result

    def test_with_pending_shows_ainda_precisa(self):
        s = WizardState()
        result = s.to_prompt_snippet()
        assert "Ainda precisa:" in result

    def test_fully_filled_shows_todos_coletados(self):
        s = WizardState(
            title="Dev",
            department="TI",
            location="SP",
            seniority="Senior",
            work_model="Remoto",
        )
        result = s.to_prompt_snippet()
        assert "Todos os campos essenciais coletados" in result

    def test_contains_nao_pergunte_instruction(self):
        s = WizardState()
        result = s.to_prompt_snippet()
        assert "NAO pergunte" in result


class TestRedisKey:
    def test_prefix_applied(self):
        key = _redis_key("conv-123")
        assert key.startswith("wizard:")

    def test_contains_conversation_id(self):
        key = _redis_key("abc-def")
        assert "abc-def" in key

    def test_empty_conversation_id(self):
        key = _redis_key("")
        assert isinstance(key, str)


class TestUpdateWizardStateFromDraft:
    def test_updates_title(self):
        s = WizardState()
        s = update_wizard_state_from_draft(s, {"title": "Backend Sênior"})
        assert s.title == "Backend Sênior"

    def test_updates_department(self):
        s = WizardState()
        s = update_wizard_state_from_draft(s, {"department": "Engenharia"})
        assert s.department == "Engenharia"

    def test_updates_draft_id_from_id(self):
        s = WizardState()
        s = update_wizard_state_from_draft(s, {"id": "draft-999"})
        assert s.draft_id == "draft-999"

    def test_updates_draft_id_directly(self):
        s = WizardState()
        s = update_wizard_state_from_draft(s, {"draft_id": "draft-888"})
        assert s.draft_id == "draft-888"

    def test_nested_data_key_extracted(self):
        s = WizardState()
        s = update_wizard_state_from_draft(s, {"data": {"title": "Dev"}})
        assert s.title == "Dev"

    def test_updates_skills_list(self):
        s = WizardState()
        s = update_wizard_state_from_draft(s, {"skills": ["Python", "FastAPI"]})
        assert s.skills == ["Python", "FastAPI"]

    def test_updates_salary_fields(self):
        s = WizardState()
        s = update_wizard_state_from_draft(s, {"salary_min": 5000, "salary_max": 10000})
        assert s.salary_min == 5000
        assert s.salary_max == 10000

    def test_none_values_not_overwritten(self):
        s = WizardState(title="Existing Title")
        s = update_wizard_state_from_draft(s, {"department": "TI"})
        assert s.title == "Existing Title"  # not changed

    def test_returns_same_state_object(self):
        s = WizardState()
        result = update_wizard_state_from_draft(s, {"title": "Dev"})
        assert result is s

    def test_empty_draft_does_not_crash(self):
        s = WizardState(title="Original")
        result = update_wizard_state_from_draft(s, {})
        assert result.title == "Original"
