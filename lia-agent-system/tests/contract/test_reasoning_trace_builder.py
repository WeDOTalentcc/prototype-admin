"""Contract tests para reasoning_trace_builder — Onda 1 B2 canonical.

Testa heurística data_fields_accessed + truncation + LGPD invariant.
"""
from __future__ import annotations

import pytest

from app.domains.agent_studio.reasoning_trace_builder import (
    FORBIDDEN_LGPD_FIELDS,
    _infer_data_fields_accessed,
    build_reasoning_trace,
)
from lia_agents_core.agent_interface import AgentReasoningStep


class _FakeAIMessage:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


class _FakeToolMessage:
    def __init__(self, content="", tool_call_id="t1", name=""):
        self.content = content
        self.tool_call_id = tool_call_id
        self.name = name


def test_empty_messages_returns_empty_trace():
    assert build_reasoning_trace([]) == []


def test_search_candidates_tool_emits_action_step():
    msg = _FakeAIMessage(
        content="",
        tool_calls=[{"name": "search_candidates", "args": {"candidate_id": "abc"}}],
    )
    trace = build_reasoning_trace([msg])
    assert len(trace) == 1
    step = trace[0]
    assert step.step_type == "action"
    assert step.label == "Chamada: search_candidates"
    assert "email" in step.data_fields_accessed
    assert "nome" in step.data_fields_accessed


def test_tool_message_emits_observation_step():
    msg = _FakeToolMessage(content="Candidato Paulo encontrado", name="search_candidates")
    trace = build_reasoning_trace([msg])
    assert len(trace) == 1
    assert trace[0].step_type == "observation"
    assert "search_candidates" in trace[0].label


def test_ai_message_with_content_only_emits_thought_step():
    msg = _FakeAIMessage(content="Vou buscar candidatos da pool X")
    trace = build_reasoning_trace([msg])
    assert len(trace) == 1
    assert trace[0].step_type == "thought"


def test_truncates_at_max_steps_and_emits_summary():
    msgs = [_FakeAIMessage(content=f"Pensamento {i}") for i in range(40)]
    trace = build_reasoning_trace(msgs, max_steps=10)
    assert len(trace) == 10
    last = trace[-1]
    assert "e mais" in last.label
    assert last.step_type == "thought"


def test_lgpd_forbidden_fields_never_in_data_fields_accessed():
    """REGRA #1 LGPD Art. 9 — defense in depth.

    Mesmo se a tabela _TOOL_DATA_FIELDS algum dia ganhar regressão e
    incluir 'cpf', _infer_data_fields_accessed strip antes de retornar.
    """
    for forbidden in FORBIDDEN_LGPD_FIELDS:
        fields = _infer_data_fields_accessed("any_tool", {forbidden: "value"})
        assert forbidden not in fields, (
            f"LGPD regression: {forbidden} apareceu em data_fields_accessed"
        )


def test_lgpd_required_canonical_set_in_forbidden():
    """REGRA #2 LGPD — frozenset canonical contém os 5 mandatory."""
    required = {"cpf", "raca", "religiao", "genero", "estado_civil"}
    assert required.issubset(FORBIDDEN_LGPD_FIELDS)


def test_keyword_heuristic_phone_tool():
    fields = _infer_data_fields_accessed("get_phone_for_candidate", {})
    assert "telefone" in fields


def test_keyword_heuristic_resume_tool():
    fields = _infer_data_fields_accessed("read_resume", {})
    assert "curriculum" in fields


def test_step_returns_pydantic_model():
    """Sanity: trace items são AgentReasoningStep (deserializable JSONB)."""
    msg = _FakeAIMessage(content="raciocinando")
    trace = build_reasoning_trace([msg])
    assert all(isinstance(s, AgentReasoningStep) for s in trace)
    # Sanity model_dump roundtrip funciona
    dumped = trace[0].model_dump()
    assert "step_type" in dumped
    assert "data_fields_accessed" in dumped
