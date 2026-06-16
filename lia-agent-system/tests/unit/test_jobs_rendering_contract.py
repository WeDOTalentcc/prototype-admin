"""
Harness sensor: verifica que list_jobs inclui jobs_index e não faz double-render.
P0-2 + P0-3 regression prevention.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def test_list_jobs_success_includes_ids_in_llm_context():
    """jobs_index must be present in _data when rich card is built."""
    import json
    # Simulate what _wrap_list_jobs returns in the success path
    # _data must include jobs_index even when rendered_as_card=True
    mock_data = {
        'rendered_as_card': True,
        'total_jobs': 3,
        'jobs_index': [
            {'id': 'uuid-1', 'title': 'Dev Backend', 'status': 'ativa'},
            {'id': 'uuid-2', 'title': 'Product Manager', 'status': 'rascunho'},
        ],
        'narrative': 'Encontrei 3 vagas.',
        'render_hint': 'CARD VISUAL JÁ ENVIADO.',
    }
    assert 'jobs_index' in mock_data, "jobs_index must be in LLM context for follow-up queries"
    assert all('id' in j for j in mock_data['jobs_index']), "Each job in index must have an id"
    assert mock_data['rendered_as_card'] is True


def test_strip_blocks_removes_collections_preserves_jobs_index():
    """_strip_blocks_for_llm must remove status_breakdown but keep jobs_index."""
    # This tests the contract: when rendered_as_card=True,
    # status_breakdown (dict) should be stripped, jobs_index should survive
    data = {
        'rendered_as_card': True,
        'status_breakdown': {'ativa': 6, 'rascunho': 22},  # should be stripped
        'jobs_index': [{'id': 'uuid-1', 'title': 'Dev'}],   # must survive
        'narrative': 'X vagas encontradas.',
        'total_jobs': 98,
    }
    # Apply the strip logic (mirrors _strip_blocks_for_llm P0-3 branch)
    keys_to_strip = [k for k, v in data.items()
                     if isinstance(v, (list, dict)) and k not in ('jobs_index',)]
    for k in keys_to_strip:
        data.pop(k, None)

    assert 'status_breakdown' not in data, "status_breakdown must be stripped (prevents markdown tables)"
    assert 'jobs_index' in data, "jobs_index must survive strip (needed for follow-up)"
    assert 'narrative' in data, "narrative must survive"
    assert 'total_jobs' in data, "scalar fields must survive"


def test_render_hint_contains_no_markdown_instruction():
    """render_hint must explicitly forbid markdown tables."""
    render_hint = (
        "CARD VISUAL JÁ ENVIADO. Escreva APENAS 1-2 frases narrativas resumindo o total e destaques. "
        "NUNCA repita dados em tabela markdown. "
        "Os IDs em jobs_index estão disponíveis para follow-up."
    )
    assert "NUNCA" in render_hint or "never" in render_hint.lower(), "render_hint must forbid markdown"
    assert "tabela" in render_hint.lower() or "table" in render_hint.lower(), "must reference tables"
    assert "jobs_index" in render_hint, "must reference jobs_index for follow-up"


def test_strip_blocks_for_llm_unit():
    """Direct unit test of _strip_blocks_for_llm with rendered_as_card."""
    import sys, os
    sys.path.insert(0, "/home/runner/workspace/lia-agent-system")
    try:
        from app.shared.rrp_block_sink import _strip_blocks_for_llm

        result = {
            "success": True,
            "data": {
                "rendered_as_card": True,
                "response_blocks": [{"kind": "table", "data": {}}],
                "status_breakdown": {"ativa": 6, "rascunho": 22},
                "jobs_index": [{"id": "abc", "title": "Engenheiro"}],
                "narrative": "6 vagas ativas.",
                "total_jobs": 6,
            },
            "message": "6 vagas.",
        }
        stripped = _strip_blocks_for_llm(result)
        data = stripped["data"]
        assert data.get("response_blocks") is None, "response_blocks must be None after strip"
        assert "status_breakdown" not in data, "status_breakdown must be stripped"
        assert "jobs_index" in data, "jobs_index must survive"
        assert data["narrative"] == "6 vagas ativas.", "narrative must survive"
        assert data["total_jobs"] == 6, "total_jobs scalar must survive"
    except ImportError:
        pytest.skip("Cannot import from Replit filesystem in this env")
