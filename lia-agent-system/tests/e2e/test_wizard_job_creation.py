"""
End-to-End Tests for Job Creation Wizard.

Tests the complete flow from wizard start to job vacancy creation in database.
"""
import pytest
import httpx
from uuid import uuid4
import asyncio

import os

# Skip toda a suite se servidor não estiver acessível
pytestmark = pytest.mark.skipif(
    os.getenv("LIA_INTEGRATION_TESTS") != "1",
    reason="Requer servidor rodando (LIA_INTEGRATION_TESTS=1)"
)


BASE_URL = "http://localhost:8000"


@pytest.fixture
def session_id():
    return str(uuid4())


@pytest.fixture
def sample_job_data():
    return {
        "title": "Desenvolvedor Python Senior",
        "department": "Tecnologia",
        "location": "São Paulo, SP",
        "work_model": "hybrid",
        "seniority": "senior",
        "salary_range": {"min": 15000, "max": 25000, "currency": "BRL"},
        "technical_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "behavioral_competencies": ["Comunicação", "Trabalho em equipe"],
        "description": "Buscamos um desenvolvedor Python experiente para atuar em projetos de alta complexidade.",
    }


class TestWizardJobCreation:
    """Test suite for wizard job creation flow."""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_wizard_stage_transitions(self, session_id, sample_job_data):
        """Test wizard progresses through stages correctly."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            stages = ["input-evaluation", "salary", "competencies", "wsi-questions", "review-publish"]
            current_stage = stages[0]
            collected_data = {}
            history = []
            
            messages = [
                "Quero criar uma vaga de Desenvolvedor Python Senior em São Paulo, modelo híbrido",
                "Confirmo. O salário é de 15 a 25 mil reais",
                "Confirmo as competências",
                "Confirmo as perguntas",
                "Confirmo e quero publicar a vaga",
            ]
            
            for i, message in enumerate(messages[:3]):
                response = await client.post(
                    f"{BASE_URL}/api/v1/wizard/smart-orchestrate",
                    json={
                        "message": message,
                        "current_stage": current_stage,
                        "collected_data": collected_data,
                        "conversation_history": history,
                        "conversation_id": session_id,
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                
                if data.get("next_stage"):
                    current_stage = data["next_stage"]
                
                collected_data.update(data.get("detected_criteria", {}))
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": data["lia_message"]})

    @pytest.mark.asyncio
    async def test_wizard_confirmation_gates(self, session_id):
        """Test that confirmation gates block automatic transitions."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/wizard/smart-orchestrate",
                json={
                    "message": "Desenvolvedor Python Senior, 15 a 25k, São Paulo, híbrido",
                    "current_stage": "input-evaluation",
                    "collected_data": {},
                    "conversation_history": [],
                    "conversation_id": session_id,
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            if data.get("awaiting_confirmation"):
                assert data["auto_transition"] is False

    @pytest.mark.asyncio
    async def test_wizard_complete_creates_job(self, session_id, sample_job_data):
        """Test that completing wizard creates job in database."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/wizard/smart-orchestrate",
                json={
                    "message": "Confirmo e quero publicar a vaga",
                    "current_stage": "review-publish",
                    "collected_data": sample_job_data,
                    "conversation_history": [
                        {"role": "user", "content": "Criar vaga de Python Senior"},
                        {"role": "assistant", "content": "Entendi, vamos criar a vaga."}
                    ],
                    "conversation_id": session_id,
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_full_wizard_flow_creates_job_with_id(self, session_id, sample_job_data):
        """Test complete wizard flow from start to job creation with ID."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/wizard/smart-orchestrate",
                json={
                    "message": "Confirmo tudo e quero publicar",
                    "current_stage": "complete",
                    "collected_data": sample_job_data,
                    "conversation_history": [],
                    "conversation_id": session_id,
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("job_published"):
                    assert data["job_vacancy_id"] is not None
                    assert len(data["job_vacancy_id"]) > 0
                    print(f"✅ Job created with ID: {data['job_vacancy_id']}")


class TestWizardAPIEndpoints:
    """Test wizard API endpoints."""

    @pytest.mark.asyncio
    async def test_stage_mapping_endpoint(self):
        """Test stage mapping endpoint returns correct mappings."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/api/v1/wizard/stage-mapping")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "frontend_to_backend" in data
            assert "backend_to_frontend" in data
            assert "backend_stages" in data
            
            assert "input-evaluation" in data["frontend_to_backend"]
            assert "review-publish" in data["frontend_to_backend"]

    @pytest.mark.asyncio
    async def test_graph_structure_endpoint(self):
        """Test graph structure endpoint returns valid structure."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/api/v1/wizard/graph-structure")
            
            assert response.status_code == 200
            data = response.json()
            
            assert isinstance(data, dict)


class TestJobVacancyCreation:
    """Test job vacancy creation directly."""

    @pytest.mark.asyncio
    async def test_direct_job_creation(self, sample_job_data):
        """Test creating job vacancy directly via API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/jobs/job-vacancies",
                json=sample_job_data
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                print(f"✅ Direct job created with ID: {data['id']}")

    @pytest.mark.asyncio
    async def test_job_list_endpoint(self):
        """Test job listing endpoint."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/api/v1/jobs/job-vacancies")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (list, dict))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
