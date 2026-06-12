"""TDD P2.6-BE: calibration tool (_handle_calibrate_agent) emite response_blocks calibration_result."""
import sys
sys.path.insert(0, "/home/runner/workspace/lia-agent-system")

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


MOCK_CANDIDATES = [
    {"id": "c1", "name": "Ana Lima", "current_title": "Engenheira de Software", "skills": []},
    {"id": "c2", "name": "Carlos Silva", "current_title": "Desenvolvedor Python", "skills": []},
    {"id": "c3", "name": "Maria Costa", "current_title": "Tech Lead", "skills": []},
]


def _get_calibration_block(data: dict) -> dict | None:
    blocks = (data or {}).get("response_blocks", [])
    for b in blocks:
        if b.get("type") == "calibration_result":
            return b
    return None


def _make_context():
    from app.domains.base import DomainContext
    return DomainContext(
        domain_id="agent_studio",
        user_id="u1",
        session_id="sess-test",
        tenant_id="test-company-123",
    )


async def _run_calibrate(candidates_list):
    """Helper: run _handle_calibrate_agent with mocked deps."""
    from app.domains.agent_studio.domain import AgentStudioDomain

    domain = AgentStudioDomain()
    context = _make_context()

    mock_orch = MagicMock()
    mock_orch.get_calibration_candidates = AsyncMock(return_value=candidates_list)

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()

    async def fake_db_gen():
        yield mock_db

    mock_metering = MagicMock()
    mock_metering.record_studio_usage = AsyncMock()

    with patch("app.services.sourcing_agent_orchestrator.SourcingAgentOrchestrator", return_value=mock_orch) as _:
        with patch("app.core.database.get_db", return_value=fake_db_gen()) as _:
            with patch("app.services.studio_metering_service.studio_metering_service", mock_metering) as _:
                response = await domain._handle_calibrate_agent(
                    {"agent_id": "agent-abc"}, context
                )
    return response


@pytest.mark.asyncio
async def test_calibration_result_includes_response_blocks():
    """calibrate_agent deve incluir response_blocks quando ha candidatos."""
    response = await _run_calibrate(MOCK_CANDIDATES)
    assert response.success
    data = response.data if isinstance(response.data, dict) else {}
    block = _get_calibration_block(data)
    assert block is not None, f"Esperado bloco calibration_result em response_blocks. data={data}"
    assert "candidates" in block["data"]
    assert "average_score" in block["data"]


@pytest.mark.asyncio
async def test_calibration_average_score_zero_when_no_scores():
    """average_score deve ser 0.0 quando candidatos nao tem score."""
    response = await _run_calibrate(MOCK_CANDIDATES)
    data = response.data if isinstance(response.data, dict) else {}
    block = _get_calibration_block(data)
    assert block is not None
    avg = block["data"]["average_score"]
    assert isinstance(avg, float)
    assert avg == 0.0  # MOCK_CANDIDATES tem score 0


@pytest.mark.asyncio
async def test_calibration_candidate_fields_normalized():
    """Candidatos normalizados devem ter id, name, score."""
    response = await _run_calibrate(MOCK_CANDIDATES)
    data = response.data if isinstance(response.data, dict) else {}
    block = _get_calibration_block(data)
    assert block is not None
    candidates = block["data"]["candidates"]
    assert len(candidates) == 3
    c = candidates[0]
    assert c["id"] == "c1"
    assert c["name"] == "Ana Lima"
    assert isinstance(c["score"], float)
    assert "stage" in c


@pytest.mark.asyncio
async def test_empty_calibration_no_response_block():
    """Sem candidatos -> response sem bloco calibration_result."""
    response = await _run_calibrate([])
    data = response.data if isinstance(response.data, dict) else {}
    block = _get_calibration_block(data)
    assert block is None, "Nao deve emitir bloco quando nao ha candidatos"


def test_normalize_calibration_candidate_helper():
    """_normalize_calibration_candidate deve aceitar varios shapes de campo."""
    from app.domains.agent_studio.domain import _normalize_calibration_candidate

    c1 = _normalize_calibration_candidate({"id": "abc", "name": "Joao"})
    assert c1["id"] == "abc"
    assert c1["name"] == "Joao"
    assert c1["score"] == 0.0

    c2 = _normalize_calibration_candidate({"candidate_id": "xyz", "full_name": "Maria", "match_score": 85})
    assert c2["id"] == "xyz"
    assert c2["name"] == "Maria"
    assert c2["score"] == 85.0

    c3 = _normalize_calibration_candidate({"id": "q1", "name": "Pedro", "calibration_score": 72.5})
    assert c3["score"] == 72.5
