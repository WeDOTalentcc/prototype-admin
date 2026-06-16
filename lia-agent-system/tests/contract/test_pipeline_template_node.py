"""Contract tests: pipeline_template_node canonical (Sprint Pipeline Templates Opção B).

Sprint Pipeline Templates Afya 2026-05-26 — Fase 5 (graph wiring TDD canonical green).

Garante (10 testes):
1. stage está em STAGE_ORDER posição idx 2 (entre jd_enrichment e bigfive)
2. stage está em HITL_STAGES
3. stage está no Literal WizardStage
4. node emite ui_action="suggest_pipeline_template" + data.templates lista
5. data.allow_skip is True
6. fail-open quando state vazio (sem company_id) — node não crasha
7. requires_approval=True + completeness=0.17 (idx 2/12)
8. stage_history ganha "pipeline_template"
9. build_graph não levanta + node está registrado
10. legacy heuristic fallback quando DB vazia
"""
from __future__ import annotations

import typing
from unittest.mock import patch, MagicMock

import pytest

from app.contracts.wizard_contract import WizardStage
from app.domains.job_creation.state import (
    HITL_STAGES,
    STAGE_ORDER,
    calculate_completeness,
)


# ---------------------------------------------------------------------------
# 1-3: Stage canonical declarations
# ---------------------------------------------------------------------------


def test_pipeline_template_in_stage_order():
    """Test 1: pipeline_template está em STAGE_ORDER entre jd_enrichment e bigfive (idx 2)."""
    assert "pipeline_template" in STAGE_ORDER
    idx = STAGE_ORDER.index("pipeline_template")
    assert STAGE_ORDER[idx - 1] == "jd_enrichment"
    assert STAGE_ORDER[idx + 1] == "bigfive"
    assert idx == 2  # 0=intake, 1=jd_enrichment, 2=pipeline_template


def test_pipeline_template_in_hitl_stages():
    """Test 2: pipeline_template está em HITL_STAGES (requires_approval canonical)."""
    assert "pipeline_template" in HITL_STAGES


def test_pipeline_template_in_wizard_stage_literal():
    """Test 3: pipeline_template está no Literal WizardStage (TS auto-gen source)."""
    assert "pipeline_template" in typing.get_args(WizardStage)


# ---------------------------------------------------------------------------
# 4-8: pipeline_template_node behavior
# ---------------------------------------------------------------------------


@pytest.fixture
def base_state():
    """State mínimo canonical (campos exigidos pelo node)."""
    return {
        "session_id": "test-sess",
        "user_id": "test-user",
        "workspace_id": 1,
        "company_id": "11111111-1111-1111-1111-111111111111",
        "auth_token": "test-token",
        "language": "pt-BR",
        "current_stage": "jd_enrichment",
        "stage_history": ["intake", "jd_enrichment"],
        "error": None,
        "user_query": "",
        "conversation_messages": [],
        "raw_input": "",
        "parsed_title": "Senior Software Engineer",
        "parsed_department": "Engineering",
        "parsed_seniority": "senior",
        "parsed_location": None,
        "parsed_model": None,
        "intake_confidence": 0.9,
        "jd_raw": None,
        "jd_enriched": None,
        "jd_quality_score": 80.0,
        "jd_quality_warnings": [],
        "jd_approved": True,
        "interview_stages": [],
    }


def test_node_emits_ui_action_suggest_pipeline_template(base_state):
    """Test 4: node emite ws_stage_payload.ui_action='suggest_pipeline_template'."""
    from app.domains.job_creation.graph import pipeline_template_node

    # Mock DB suggestion: top-3 templates retornados
    fake_db = {
        "templates": [
            {"template_id": "uuid-1", "name": "Engineering Senior", "description": "x",
             "stages_count": 5, "score": 0.92},
            {"template_id": "uuid-2", "name": "Engineering Mid", "description": "y",
             "stages_count": 4, "score": 0.75},
        ],
        "top_score": 0.92,
        "should_suggest": True,
    }
    with patch(
        "app.domains.job_creation.graph._build_pipeline_template_db_suggestion",
        return_value=fake_db,
    ):
        result = pipeline_template_node(base_state)

    payload = result["ws_stage_payload"]
    assert payload["type"] == "wizard_stage"
    assert payload["stage"] == "pipeline_template"
    assert payload["ui_action"] == "suggest_pipeline_template"
    assert isinstance(payload["data"]["templates"], list)
    assert len(payload["data"]["templates"]) == 2
    assert payload["data"]["suggested_template_id"] == "uuid-1"


def test_node_emits_allow_skip_true(base_state):
    """Test 5: data.allow_skip is True (recrutador pode escolher padrão da empresa)."""
    from app.domains.job_creation.graph import pipeline_template_node

    with patch(
        "app.domains.job_creation.graph._build_pipeline_template_db_suggestion",
        return_value=None,
    ):
        result = pipeline_template_node(base_state)
    assert result["ws_stage_payload"]["data"]["allow_skip"] is True


def test_node_with_no_company_id_fail_open(base_state):
    """Test 6: node fail-open quando state vazio/sem company_id — não crasha."""
    from app.domains.job_creation.graph import pipeline_template_node

    minimal_state = {
        "session_id": "x",
        "stage_history": [],
        "parsed_title": None,
        "parsed_seniority": None,
    }
    # NÃO deve levantar exception
    result = pipeline_template_node(minimal_state)
    assert result["current_stage"] == "pipeline_template"
    # templates pode ser [] mas allow_skip continua True
    assert result["ws_stage_payload"]["data"]["allow_skip"] is True


def test_node_requires_approval_and_completeness(base_state):
    """Test 7: requires_approval=True + completeness=0.17 (idx 2/12)."""
    from app.domains.job_creation.graph import pipeline_template_node

    with patch(
        "app.domains.job_creation.graph._build_pipeline_template_db_suggestion",
        return_value=None,
    ):
        result = pipeline_template_node(base_state)

    assert result["requires_approval"] is True
    expected_completeness = calculate_completeness("pipeline_template")
    assert result["completeness"] == expected_completeness
    # Sanity: idx 2 / (len-1) = 2/11 = 0.18 rounded. Verifica que está entre 0.1-0.25.
    assert 0.1 <= expected_completeness <= 0.25


def test_node_stage_history_appended(base_state):
    """Test 8: stage_history ganha 'pipeline_template' (sem duplicar)."""
    from app.domains.job_creation.graph import pipeline_template_node

    with patch(
        "app.domains.job_creation.graph._build_pipeline_template_db_suggestion",
        return_value=None,
    ):
        result = pipeline_template_node(base_state)
    assert "pipeline_template" in result["stage_history"]
    # Idempotência: chamando 2x não duplica
    result2 = pipeline_template_node(result)
    assert result2["stage_history"].count("pipeline_template") == 1


# ---------------------------------------------------------------------------
# 9-10: Graph builder + fallback
# ---------------------------------------------------------------------------


def test_graph_builder_includes_pipeline_template_node():
    """Test 9: build_graph não levanta + pipeline_template é node registrado (ambos modes)."""
    from app.domains.job_creation.graph import create_job_creation_graph

    # Legacy mode (use_llm_gates=False)
    g_legacy = create_job_creation_graph(use_llm_gates=False)
    assert g_legacy is not None
    # Internal LangGraph: nodes are stored in builder.nodes dict
    assert "pipeline_template" in g_legacy.nodes

    # LLM gates mode (use_llm_gates=True)
    g_llm = create_job_creation_graph(use_llm_gates=True)
    assert g_llm is not None
    assert "pipeline_template" in g_llm.nodes


def test_legacy_heuristic_fallback_when_db_empty(base_state):
    """Test 10: legacy heuristic fallback quando DB suggestion None (allow_skip mantido)."""
    from app.domains.job_creation.graph import pipeline_template_node

    # DB suggestion returns None → node deve still emit allow_skip=True
    # com suggestions_data.pipeline_template populado pelo heuristic legacy.
    with patch(
        "app.domains.job_creation.graph._build_pipeline_template_db_suggestion",
        return_value=None,
    ):
        result = pipeline_template_node(base_state)

    payload = result["ws_stage_payload"]
    assert payload["data"]["allow_skip"] is True
    # Retrocompat — heuristic legacy ainda emite seu output em suggestions_data
    suggestions_data = payload["data"].get("suggestions_data", {})
    # Title "Senior Software Engineer" → matches _TECHNICAL_KEYWORDS heuristic
    legacy = suggestions_data.get("pipeline_template")
    assert legacy is not None
    assert "suggested_type" in legacy
    # DB sub-key segue None quando DB vazia
    assert suggestions_data.get("pipeline_template_db") is None
