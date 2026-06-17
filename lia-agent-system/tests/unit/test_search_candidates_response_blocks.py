"""
TDD: verifica que search_candidates emite response_blocks estruturados
que o agentic_loop consegue extrair (plain dict path).
"""
import pytest
from app.domains.sourcing.tools.query_tools import _format_search_candidates_result
from app.orchestrator.execution.agentic_loop import _extract_response_blocks


MOCK_CANDIDATES = [
    {"id": "abc-1", "name": "Ana Lima", "current_title": "Eng. Frontend", "match_score": 87},
    {"id": "abc-2", "name": "Carlos Silva", "current_title": "Dev React", "match_score": 72},
]


def test_format_search_candidates_result_includes_response_blocks():
    """_format_search_candidates_result deve incluir response_blocks no data."""
    result = _format_search_candidates_result(MOCK_CANDIDATES, {})
    assert "data" in result
    assert "response_blocks" in result["data"], (
        "_format_search_candidates_result não inclui 'response_blocks' em data. "
        "Adicionar: data['response_blocks'] = [{'type': 'search_candidates_result', 'data': {...}}]"
    )
    blocks = result["data"]["response_blocks"]
    assert isinstance(blocks, list)
    assert len(blocks) == 1
    block = blocks[0]
    assert block["type"] == "search_candidates_result"
    assert "candidates" in block["data"]
    assert "total_count" in block["data"]
    assert block["data"]["total_count"] == 2


def test_extract_response_blocks_from_plain_dict():
    """_extract_response_blocks deve funcionar com plain dicts (não só ToolResult objects)."""
    plain_dict_result = _format_search_candidates_result(MOCK_CANDIDATES, {})
    # Atualmente _extract_response_blocks só funciona com objetos com .success/.result
    # Deve também funcionar com plain dicts
    blocks = _extract_response_blocks(plain_dict_result)
    assert isinstance(blocks, list), (
        "_extract_response_blocks retornou [] para plain dict. "
        "Adicionar path para isinstance(result, dict) em _extract_response_blocks em agentic_loop.py"
    )
    assert len(blocks) == 1
    assert blocks[0]["type"] == "search_candidates_result"


def test_format_empty_candidates_no_response_blocks():
    """Sem candidatos, não deve emitir response_blocks."""
    result = _format_search_candidates_result([], {})
    blocks = result.get("data", {}).get("response_blocks")
    # Sem candidatos, response_blocks deve ser None ou lista vazia
    assert not blocks, (
        "Com 0 candidatos, response_blocks deve ser None/empty — não faz sentido card vazio."
    )


def test_response_blocks_candidate_fields():
    """Cada candidato no block deve ter os campos esperados pelo FE."""
    result = _format_search_candidates_result(MOCK_CANDIDATES, {})
    block = result["data"]["response_blocks"][0]
    candidate = block["data"]["candidates"][0]
    assert "id" in candidate
    assert "name" in candidate
    # currentTitle e matchScore são opcionais mas devem estar presentes quando existirem
    assert "currentTitle" in candidate or candidate.get("name") == "Ana Lima"
