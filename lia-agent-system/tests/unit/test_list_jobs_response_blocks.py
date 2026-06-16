"""TDD: list_jobs emite response_blocks list_jobs_result.

Precedente: tests/unit/test_search_candidates_response_blocks.py (P2.4)
Produtor: app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry._format_list_jobs_result
"""
import pytest
from app.domains.recruiter_assistant.agents.jobs_mgmt_tool_registry import (
    _format_list_jobs_result,
)
from app.orchestrator.execution.agentic_loop import _extract_response_blocks


MOCK_JOBS = [
    {
        "id": "job-1",
        "title": "Engenheiro Frontend",
        "department": "Tech",
        "status": "publicada",
        "candidate_count": 12,
    },
    {
        "id": "job-2",
        "title": "Designer UX",
        "department": "Produto",
        "status": "ao_vivo",
        "candidate_count": 5,
    },
]


def test_format_list_jobs_includes_response_blocks():
    """Deve incluir response_blocks no data com type list_jobs_result."""
    result = _format_list_jobs_result(MOCK_JOBS, total=2)
    assert "data" in result
    assert "response_blocks" in result["data"], (
        "_format_list_jobs_result nao inclui 'response_blocks' em data. "
        "Adicionar: data['response_blocks'] = [{'type': 'list_jobs_result', 'data': {...}}]"
    )
    blocks = result["data"]["response_blocks"]
    assert isinstance(blocks, list)
    # deve ter pelo menos 1 bloco com type list_jobs_result
    ljr_blocks = [b for b in blocks if b.get("type") == "list_jobs_result"]
    assert len(ljr_blocks) == 1, (
        f"Esperado 1 bloco com type='list_jobs_result', encontrado {ljr_blocks}"
    )
    block = ljr_blocks[0]
    assert "jobs" in block["data"]
    assert "total_count" in block["data"]
    assert block["data"]["total_count"] == 2


def test_format_list_jobs_job_fields():
    """Cada job no block deve ter id e title (campos obrigatórios para JobSummary FE)."""
    result = _format_list_jobs_result(MOCK_JOBS, total=2)
    ljr_blocks = [b for b in result["data"]["response_blocks"] if b.get("type") == "list_jobs_result"]
    job = ljr_blocks[0]["data"]["jobs"][0]
    assert "id" in job, "Job no response_block deve ter 'id'"
    assert "title" in job, "Job no response_block deve ter 'title'"


def test_format_empty_jobs_no_list_jobs_result_block():
    """Sem jobs, nao deve emitir bloco list_jobs_result."""
    result = _format_list_jobs_result([], total=0)
    blocks = result.get("data", {}).get("response_blocks") or []
    ljr_blocks = [b for b in blocks if b.get("type") == "list_jobs_result"]
    assert not ljr_blocks, (
        "Com 0 jobs, nao deve haver bloco list_jobs_result — card vazio nao faz sentido."
    )


def test_extract_response_blocks_from_list_jobs():
    """_extract_response_blocks deve extrair o bloco list_jobs_result do plain dict."""
    result = _format_list_jobs_result(MOCK_JOBS, total=2)
    blocks = _extract_response_blocks(result)
    assert isinstance(blocks, list)
    ljr_blocks = [b for b in blocks if b.get("type") == "list_jobs_result"]
    assert len(ljr_blocks) == 1, (
        "_extract_response_blocks nao encontrou bloco list_jobs_result. "
        "Verificar que result['data']['response_blocks'] contem o bloco."
    )
    assert ljr_blocks[0]["type"] == "list_jobs_result"
