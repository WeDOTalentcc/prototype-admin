"""
Pytest fixtures for domain agent testing (nova arquitetura DDD).
Cobre os agentes em app/domains/*/agents/.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any


@pytest.fixture
def company_id() -> str:
    return "company-test-001"


@pytest.fixture
def user_id() -> str:
    return "user-test-001"


@pytest.fixture
def job_id() -> str:
    return "job-test-001"


@pytest.fixture
def candidate_id() -> str:
    return "candidate-test-001"


@pytest.fixture
def mock_llm_response():
    """Mock de resposta do LLM para testes sem chamada de API."""
    mock = MagicMock()
    mock.content = '{"decision": "final_answer", "answer": "OK", "confidence": 0.9}'
    return mock


@pytest.fixture
def mock_llm_service(mock_llm_response):
    """Mock do LLMService."""
    mock = MagicMock()
    mock.generate = AsyncMock(return_value=mock_llm_response.content)
    mock.generate_json = AsyncMock(return_value={"decision": "final_answer", "answer": "OK"})
    mock.claude = MagicMock()
    mock.claude.ainvoke = AsyncMock(return_value=mock_llm_response)
    return mock


@pytest.fixture
def mock_db_session():
    """Mock de sessão de banco de dados."""
    mock = MagicMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    mock.execute = AsyncMock(return_value=MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    ))
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    return mock


@pytest.fixture
def sample_candidate_data() -> Dict[str, Any]:
    return {
        "id": "candidate-test-001",
        "name": "Maria Silva",
        "email": "maria.silva@example.com",
        "cv_text": (
            "Desenvolvedora Python Sênior com 7 anos de experiência. "
            "Especialista em FastAPI, SQLAlchemy, PostgreSQL, Docker, AWS. "
            "Liderou equipe de 5 pessoas. Inglês fluente."
        ),
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "experience_years": 7,
        "seniority": "senior",
        "location": "São Paulo, SP",
    }


@pytest.fixture
def sample_job_requirements() -> list:
    return [
        {"name": "Python", "priority": "required", "years": 5},
        {"name": "FastAPI", "priority": "required", "years": 3},
        {"name": "PostgreSQL", "priority": "desired", "years": 2},
        {"name": "Docker", "priority": "desired", "years": 1},
    ]


@pytest.fixture
def discriminatory_job_text() -> str:
    return "Procuramos homem jovem, solteiro, sem filhos, de 20 a 30 anos, para cargo de gerente."


@pytest.fixture
def base_agent_context(company_id, user_id, job_id) -> Dict[str, Any]:
    return {
        "company_id": company_id,
        "user_id": user_id,
        "job_id": job_id,
        "session_id": "session-test-001",
    }
