"""TDD tests — department_wizard_service.py"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

_REPO_PATH = "app.domains.company.repositories.department_repository.DepartmentRepository"

def _make_mock_repo(dept_name="Recursos Humanos"):
    repo = MagicMock()
    created = MagicMock()
    created.id = uuid4()
    created.name = dept_name
    repo.create = AsyncMock(return_value=created)
    return repo


class TestCreateDepartmentForWizard:
    @pytest.mark.asyncio
    async def test_creates_with_name_only(self):
        from app.domains.job_creation.services.department_wizard_service import (
            create_department_for_wizard,
        )
        mock_repo = _make_mock_repo()
        with patch(_REPO_PATH, return_value=mock_repo):
            result = await create_department_for_wizard(
                name="Recursos Humanos",
                company_id=str(uuid4()),
                db=AsyncMock(),
            )
        assert result["name"] == "Recursos Humanos"
        assert "id" in result
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_with_all_fields(self):
        from app.domains.job_creation.services.department_wizard_service import (
            create_department_for_wizard,
        )
        mock_repo = _make_mock_repo()
        cid = str(uuid4())
        with patch(_REPO_PATH, return_value=mock_repo):
            await create_department_for_wizard(
                name="Recursos Humanos", company_id=cid, db=AsyncMock(),
                code="rh", description="Gestão de pessoas",
                location="São Paulo", headcount=15,
                cost_center="CC-001", hiring_priority="alta",
            )
        call_data = mock_repo.create.call_args[0][0]
        assert call_data["code"] == "RH"
        assert call_data["description"] == "Gestão de pessoas"
        assert call_data["location"] == "São Paulo"
        assert call_data["headcount"] == 15
        assert call_data["cost_center"] == "CC-001"
        assert call_data["hiring_priority"] == "alta"

    @pytest.mark.asyncio
    async def test_links_manager_when_provided(self):
        from app.domains.job_creation.services.department_wizard_service import (
            create_department_for_wizard,
        )
        mock_repo = _make_mock_repo()
        with patch(_REPO_PATH, return_value=mock_repo):
            await create_department_for_wizard(
                name="RH", company_id=str(uuid4()), db=AsyncMock(),
                manager_name="Ana Souza", manager_email="ana@empresa.com",
            )
        call_data = mock_repo.create.call_args[0][0]
        assert call_data["manager_name"] == "Ana Souza"
        assert call_data["manager_email"] == "ana@empresa.com"

    @pytest.mark.asyncio
    async def test_company_id_injected_fail_closed(self):
        from app.domains.job_creation.services.department_wizard_service import (
            create_department_for_wizard,
        )
        mock_repo = _make_mock_repo()
        cid = str(uuid4())
        with patch(_REPO_PATH, return_value=mock_repo):
            await create_department_for_wizard(name="TI", company_id=cid, db=AsyncMock())
        call_data = mock_repo.create.call_args[0][0]
        assert str(call_data["company_id"]) == cid

    @pytest.mark.asyncio
    async def test_raises_on_invalid_company_id(self):
        from app.domains.job_creation.services.department_wizard_service import (
            create_department_for_wizard,
        )
        with pytest.raises(ValueError, match="company_id"):
            await create_department_for_wizard(
                name="TI", company_id="not-a-uuid", db=AsyncMock(),
            )


class TestParseDeptCreationResponse:
    def test_detects_confirmation(self):
        from app.domains.job_creation.services.department_wizard_service import (
            parse_dept_creation_response,
        )
        for phrase in ["sim", "Pode criar", "cria ai", "yes", "confirmo"]:
            r = parse_dept_creation_response(phrase, "RH")
            assert r["confirmed"] is True, f"Should confirm: {phrase!r}"

    def test_detects_denial(self):
        from app.domains.job_creation.services.department_wizard_service import (
            parse_dept_creation_response,
        )
        for phrase in ["não", "nao", "cancelar"]:
            r = parse_dept_creation_response(phrase, "RH")
            assert r["confirmed"] is False, f"Should deny: {phrase!r}"

    def test_parses_code(self):
        from app.domains.job_creation.services.department_wizard_service import (
            parse_dept_creation_response,
        )
        r = parse_dept_creation_response("sim, código RH", "Recursos Humanos")
        assert r["confirmed"] is True
        assert r["code"] == "RH"

    def test_parses_description(self):
        from app.domains.job_creation.services.department_wizard_service import (
            parse_dept_creation_response,
        )
        r = parse_dept_creation_response("sim, descrição: Gestão de pessoas", "RH")
        assert r["description"] == "Gestão de pessoas"

    def test_parses_headcount(self):
        from app.domains.job_creation.services.department_wizard_service import (
            parse_dept_creation_response,
        )
        r = parse_dept_creation_response("sim, 15 pessoas", "RH")
        assert r["headcount"] == 15

    def test_parses_location(self):
        from app.domains.job_creation.services.department_wizard_service import (
            parse_dept_creation_response,
        )
        r = parse_dept_creation_response("sim, localização São Paulo", "RH")
        assert r["location"] == "São Paulo"

    def test_parses_existing_dept_from_denial(self):
        from app.domains.job_creation.services.department_wizard_service import (
            parse_dept_creation_response,
        )
        r = parse_dept_creation_response("não, usa Tecnologia", "RH")
        assert r["confirmed"] is False
        assert r["chosen_existing"] == "Tecnologia"
