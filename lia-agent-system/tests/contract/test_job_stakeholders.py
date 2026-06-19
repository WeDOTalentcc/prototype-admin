"""T10 -- Contract tests for job vacancy stakeholders feature.

Covers:
  - Model field existence and defaults
  - API schema validation (valid, invalid email, missing name, bad role)
  - Wizard tool set_stakeholders
  - notify_stakeholders reads from vacancy stakeholders list
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# 1. Model field
# ---------------------------------------------------------------------------

class TestStakeholdersModelField:
    """Verify the stakeholders column exists on JobVacancy."""

    def test_field_exists(self):
        from libs.models.lia_models.job_vacancy import JobVacancy
        assert hasattr(JobVacancy, "stakeholders"), "stakeholders column missing from JobVacancy"

    def test_field_default_is_list(self):
        from libs.models.lia_models.job_vacancy import JobVacancy
        col = JobVacancy.__table__.columns["stakeholders"]
        assert col.default is not None
        # default.arg is callable (the `list` builtin) that returns []
        assert callable(col.default.arg), "default should be a callable"
        assert col.default.arg.__name__ == "list"

    def test_field_server_default(self):
        from libs.models.lia_models.job_vacancy import JobVacancy
        col = JobVacancy.__table__.columns["stakeholders"]
        assert col.server_default is not None
        assert "[]" in str(col.server_default.arg)


# ---------------------------------------------------------------------------
# 2. API schema validation
# ---------------------------------------------------------------------------

class TestStakeholderSchemaValidation:
    """Pydantic schema validators for stakeholders field."""

    def test_valid_stakeholders(self):
        from app.api.v1.job_vacancies._shared import JobVacancyCreate
        obj = JobVacancyCreate(
            title="Dev Sr",
            stakeholders=[
                {"name": "Ana Silva", "email": "ana@corp.com", "role": "hr_bp"},
                {"name": "Carlos Souza", "email": "carlos@corp.com", "role": "dept_head"},
            ],
        )
        assert len(obj.stakeholders) == 2
        assert obj.stakeholders[0]["name"] == "Ana Silva"
        assert obj.stakeholders[0]["email"] == "ana@corp.com"
        assert obj.stakeholders[0]["role"] == "hr_bp"

    def test_none_stakeholders_passes(self):
        from app.api.v1.job_vacancies._shared import JobVacancyCreate
        obj = JobVacancyCreate(title="Dev", stakeholders=None)
        assert obj.stakeholders is None

    def test_empty_list_passes(self):
        from app.api.v1.job_vacancies._shared import JobVacancyCreate
        obj = JobVacancyCreate(title="Dev", stakeholders=[])
        assert obj.stakeholders == []

    def test_invalid_email_rejected(self):
        from app.api.v1.job_vacancies._shared import JobVacancyCreate
        with pytest.raises(Exception) as exc_info:
            JobVacancyCreate(title="Dev", stakeholders=[{"name": "Jo", "email": "not-an-email"}])
        assert "email" in str(exc_info.value).lower()

    def test_missing_name_rejected(self):
        from app.api.v1.job_vacancies._shared import JobVacancyCreate
        with pytest.raises(Exception) as exc_info:
            JobVacancyCreate(title="Dev", stakeholders=[{"email": "a@b.com"}])
        assert "name" in str(exc_info.value).lower()

    def test_short_name_rejected(self):
        from app.api.v1.job_vacancies._shared import JobVacancyCreate
        with pytest.raises(Exception) as exc_info:
            JobVacancyCreate(title="Dev", stakeholders=[{"name": "A", "email": "a@b.com"}])
        assert "name" in str(exc_info.value).lower()

    def test_invalid_role_rejected(self):
        from app.api.v1.job_vacancies._shared import JobVacancyCreate
        with pytest.raises(Exception) as exc_info:
            JobVacancyCreate(
                title="Dev",
                stakeholders=[{"name": "Ana", "email": "a@b.com", "role": "ceo"}],
            )
        assert "role" in str(exc_info.value).lower()

    def test_default_role_is_other(self):
        from app.api.v1.job_vacancies._shared import JobVacancyCreate
        obj = JobVacancyCreate(
            title="Dev",
            stakeholders=[{"name": "Jo Silva", "email": "jo@x.com"}],
        )
        assert obj.stakeholders[0]["role"] == "other"

    def test_email_normalized_lowercase(self):
        from app.api.v1.job_vacancies._shared import JobVacancyCreate
        obj = JobVacancyCreate(
            title="Dev",
            stakeholders=[{"name": "Jo", "email": "JO@X.COM"}],
        )
        assert obj.stakeholders[0]["email"] == "jo@x.com"

    def test_max_stakeholders_exceeded(self):
        from app.api.v1.job_vacancies._shared import JobVacancyCreate
        many = [{"name": f"Person {i}", "email": f"p{i}@x.com"} for i in range(21)]
        with pytest.raises(Exception) as exc_info:
            JobVacancyCreate(title="Dev", stakeholders=many)
        assert "20" in str(exc_info.value)

    def test_update_schema_also_validates(self):
        from app.api.v1.job_vacancies._shared import JobVacancyUpdate
        obj = JobVacancyUpdate(
            stakeholders=[{"name": "Maria", "email": "m@corp.com", "role": "interviewer"}]
        )
        assert len(obj.stakeholders) == 1

    def test_response_schema_includes_stakeholders(self):
        from app.api.v1.job_vacancies._shared import JobVacancyResponse
        fields = JobVacancyResponse.model_fields
        assert "stakeholders" in fields


# ---------------------------------------------------------------------------
# 3. Wizard tool set_stakeholders
# ---------------------------------------------------------------------------

class TestWizardSetStakeholders:
    """Wizard tool handler validates and stores stakeholders."""

    def _make_ctx(self, company_id="test-co"):
        ctx = MagicMock()
        ctx.company_id = company_id
        return ctx

    def test_valid_stakeholders_accepted(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_set_stakeholders
        result = _handle_set_stakeholders(
            state={"company_id": "co1"},
            tool_input={"stakeholders": [
                {"name": "Ana", "email": "ana@co.com", "role": "hr_bp"},
            ]},
            ctx=self._make_ctx(),
        )
        assert not result.error
        assert "parsed_stakeholders" in result.state_updates
        assert len(result.state_updates["parsed_stakeholders"]) == 1
        assert result.state_updates["parsed_stakeholders"][0]["name"] == "Ana"

    def test_invalid_email_rejected(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_set_stakeholders
        result = _handle_set_stakeholders(
            state={},
            tool_input={"stakeholders": [{"name": "Jo", "email": "bad"}]},
            ctx=self._make_ctx(),
        )
        assert result.error
        assert "email" in result.llm_message.lower()

    def test_empty_list_rejected(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_set_stakeholders
        result = _handle_set_stakeholders(
            state={},
            tool_input={"stakeholders": []},
            ctx=self._make_ctx(),
        )
        assert result.error

    def test_rejects_company_id_in_input(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_set_stakeholders
        result = _handle_set_stakeholders(
            state={},
            tool_input={"stakeholders": [{"name": "Jo", "email": "j@x.com"}], "company_id": "evil"},
            ctx=self._make_ctx(),
        )
        assert result.error  # _reject_tenant_keys blocks

    def test_multiple_stakeholders(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_set_stakeholders
        result = _handle_set_stakeholders(
            state={},
            tool_input={"stakeholders": [
                {"name": "Ana", "email": "ana@co.com", "role": "hr_bp"},
                {"name": "Bob", "email": "bob@co.com", "role": "interviewer"},
                {"name": "Carla", "email": "carla@co.com"},
            ]},
            ctx=self._make_ctx(),
        )
        assert not result.error
        assert len(result.state_updates["parsed_stakeholders"]) == 3
        assert result.state_updates["parsed_stakeholders"][2]["role"] == "other"

    def test_confirmation_message_includes_names(self):
        from app.domains.job_creation.orchestrator.wizard_service_tools import _handle_set_stakeholders
        result = _handle_set_stakeholders(
            state={},
            tool_input={"stakeholders": [
                {"name": "Ana Silva", "email": "ana@co.com", "role": "hr_bp"},
            ]},
            ctx=self._make_ctx(),
        )
        assert "Ana Silva" in result.llm_message
        assert "HRBP" in result.llm_message


# ---------------------------------------------------------------------------
# 4. notify_stakeholders reads from vacancy
# ---------------------------------------------------------------------------

class TestNotifyStakeholdersReadsVacancy:
    """notify_stakeholders should prefer per-vacancy stakeholders list."""

    def test_vacancy_stakeholders_field_in_state(self):
        """State-level check: parsed_stakeholders maps to stakeholders in publish."""
        from app.domains.job_creation.state import JobCreationState
        fields = {f.name for f in JobCreationState.__dataclass_fields__.values()} if hasattr(JobCreationState, '__dataclass_fields__') else set()
        # If using TypedDict, check keys
        if not fields:
            import typing
            hints = typing.get_type_hints(JobCreationState)
            fields = set(hints.keys())
        assert "parsed_stakeholders" in fields, "parsed_stakeholders missing from JobCreationState"

    def test_publish_node_includes_stakeholders(self):
        """Verify that publish node code references parsed_stakeholders."""
        import inspect
        from app.domains.job_creation.nodes import publish
        source = inspect.getsource(publish)
        assert "parsed_stakeholders" in source, "publish node does not reference parsed_stakeholders"

    def test_notify_stakeholders_code_references_vacancy(self):
        """Verify that notify_stakeholders handler code references vacancy stakeholders."""
        import inspect
        from app.domains.communication.domain import CommunicationDomain
        source = inspect.getsource(CommunicationDomain._handle_notify_stakeholders)
        assert "vacancy_stakeholders" in source, "notify_stakeholders does not read vacancy stakeholders"
        assert "Fallback" in source or "fallback" in source.lower(), "notify_stakeholders has no fallback path"


class TestNewStakeholderRoles:
    """Novos roles canonicos devem ser aceitos; roles legados continuam validos."""

    def test_new_roles_accepted(self):
        from app.api.v1.job_vacancies._shared import JobVacancyCreate
        for role in ("ta_lead", "area_manager", "area_director", "technical_interviewer"):
            obj = JobVacancyCreate(
                title="Dev",
                stakeholders=[{"name": "Ana", "email": "ana@co.com", "role": role}],
            )
            assert obj.stakeholders[0]["role"] == role, f"role {role} nao foi aceito"

    def test_legacy_roles_still_valid(self):
        from app.api.v1.job_vacancies._shared import JobVacancyCreate
        for role in ("dept_head", "interviewer"):
            obj = JobVacancyCreate(
                title="Dev",
                stakeholders=[{"name": "Ana", "email": "ana@co.com", "role": role}],
            )
            assert obj.stakeholders[0]["role"] == role, f"role legado {role} nao deve ser rejeitado (backward compat)"

    def test_total_valid_roles_count(self):
        from app.api.v1.job_vacancies._shared import _VALID_STAKEHOLDER_ROLES
        expected = {
            "ta_lead", "area_manager", "area_director", "technical_interviewer",
            "hr_bp", "dept_head", "committee_member", "interviewer", "other",
        }
        assert expected == _VALID_STAKEHOLDER_ROLES, (
            f"Set de roles divergiu do esperado. "
            f"Adicionados: {_VALID_STAKEHOLDER_ROLES - expected}, "
            f"Faltando: {expected - _VALID_STAKEHOLDER_ROLES}"
        )
