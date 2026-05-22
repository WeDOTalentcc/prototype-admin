"""
Pytest fixtures for agent testing.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# W1-002 (2026-05-22): legacy import removed; symbols não usados ou
# helper foi deletado (create_mock_agent_response sem callers).


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing agents without API calls."""
    mock = MagicMock()
    mock.claude = MagicMock()
    mock.claude.ainvoke = AsyncMock(return_value=MagicMock(
        content='{"success": true, "message": "Test response"}'
    ))
    mock.gemini = MagicMock()
    mock.gemini.ainvoke = AsyncMock(return_value=MagicMock(
        content='{"success": true, "message": "Test response"}'
    ))
    return mock


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    mock = MagicMock()
    mock.execute = AsyncMock(return_value=MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    ))
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    return mock


@pytest.fixture
def sample_job_data() -> Dict[str, Any]:
    """Sample job vacancy data for testing."""
    return {
        "id": "job-123",
        "title": "Senior Python Developer",
        "description": "We are looking for a senior Python developer with FastAPI experience.",
        "company_id": "company-456",
        "seniority": "senior",
        "location": "Remote",
        "salary_range": {"min": 15000, "max": 25000},
        "requirements": [
            "5+ years Python experience",
            "FastAPI or Django",
            "PostgreSQL",
            "Docker/Kubernetes"
        ],
        "competencies": [
            {"name": "Python", "weight": 0.25, "type": "technical"},
            {"name": "FastAPI", "weight": 0.20, "type": "technical"},
            {"name": "PostgreSQL", "weight": 0.15, "type": "technical"},
            {"name": "Team Collaboration", "weight": 0.20, "type": "behavioral"},
            {"name": "Problem Solving", "weight": 0.20, "type": "behavioral"}
        ]
    }


@pytest.fixture
def sample_candidate_data() -> Dict[str, Any]:
    """Sample candidate data for testing."""
    return {
        "id": "candidate-789",
        "name": "João Silva",
        "email": "joao.silva@example.com",
        "phone": "+5511999999999",
        "linkedin": "https://linkedin.com/in/joaosilva",
        "years_experience": 5,
        "cv_text": """
        João Silva - Senior Python Developer
        
        Experience:
        - 5 years as Python Developer at TechCorp
        - Built APIs serving 1M+ requests/day
        - Led team of 4 developers
        - Implemented microservices architecture
        
        Skills:
        - Python, FastAPI, Django
        - PostgreSQL, Redis, MongoDB
        - Docker, Kubernetes, AWS
        - Git, CI/CD, TDD
        """,
        "competencies_scores": [
            {"name": "Python", "autodeclaracao_score": 4.0, "contextual_score": 4.5},
            {"name": "FastAPI", "autodeclaracao_score": 4.0, "contextual_score": 4.0},
            {"name": "PostgreSQL", "autodeclaracao_score": 3.5, "contextual_score": 3.5}
        ]
    }


@pytest.fixture
def sample_interview_data() -> Dict[str, Any]:
    """Sample interview data for testing."""
    return {
        "candidate_id": "candidate-789",
        "job_id": "job-123",
        "years_experience": 5.0,
        "technical_responses": [
            {
                "question": "Rate your Python skills 1-5",
                "response": "I would rate myself 4 out of 5. I have 5 years experience building FastAPI applications.",
                "competency": "Python"
            }
        ],
        "behavioral_responses": [
            {
                "question": "Tell me about a time you worked in a team",
                "response": "I led a team of 4 developers to deliver a microservices platform on time.",
                "competency": "Team Collaboration"
            }
        ],
        "competencies": [
            {
                "name": "Python",
                "autodeclaracao_score": 4.0,
                "contextual_score": 4.5,
                "weight": 0.25,
                "response_text": "4 de 5. Tenho 5 anos de experiência com FastAPI, implementei APIs que atendem 1 milhão de requisições por dia.",
                "evidence": ["FastAPI", "1M requests/day", "5 years experience"]
            }
        ]
    }


@pytest.fixture
def sample_context() -> Dict[str, Any]:
    """Sample agent context for testing."""
    return {
        "company_id": "company-456",
        "user_id": "user-123",
        "session_id": "session-abc",
        "tenant_id": "tenant-001"
    }
