"""Contract test for AgentOutput.reasoning_trace + AgentReasoningStep schema.

Wave 0 Fix 4 (2026-05-27) — preparatório Onda 1 Studio Control Room.

Pina:
  - AgentReasoningStep aceita os 4 step_types canonical
  - score, matched, detail são opcionais
  - data_fields_accessed é list[str] (LGPD audit trail)
  - AgentOutput.reasoning_trace default = None (backward-compat)
  - AgentOutput.reasoning_steps (legacy List[str]) preservado

Se este teste falhar, qualquer agent serializer/consumer do trace quebra.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from lia_agents_core.agent_interface import AgentOutput, AgentReasoningStep


class TestAgentReasoningStep:
    def test_minimal_step(self):
        s = AgentReasoningStep(step_type="thought", label="Pensando...")
        assert s.step_type == "thought"
        assert s.label == "Pensando..."
        assert s.score is None
        assert s.matched is None
        assert s.detail is None
        assert s.data_fields_accessed == []

    def test_full_step_criterion(self):
        s = AgentReasoningStep(
            step_type="criterion",
            label="Experiência >= 3 anos",
            score=0.82,
            matched=True,
            detail="Candidato tem 5 anos de Python",
            data_fields_accessed=["experience_years", "skills"],
        )
        assert s.score == pytest.approx(0.82)
        assert s.matched is True
        assert "experience_years" in s.data_fields_accessed

    def test_all_four_step_types(self):
        for st in ("criterion", "thought", "action", "observation"):
            s = AgentReasoningStep(step_type=st, label="x")
            assert s.step_type == st

    def test_rejects_invalid_step_type(self):
        with pytest.raises(ValidationError):
            AgentReasoningStep(step_type="reflection", label="x")

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            AgentReasoningStep(step_type="criterion", label="x", score=1.5)
        with pytest.raises(ValidationError):
            AgentReasoningStep(step_type="criterion", label="x", score=-0.1)

    def test_data_fields_accessed_serializes_for_lgpd(self):
        s = AgentReasoningStep(
            step_type="action",
            label="Ler currículo",
            data_fields_accessed=["cv_text", "skills"],
        )
        payload = s.model_dump()
        assert payload["data_fields_accessed"] == ["cv_text", "skills"]


class TestAgentOutputReasoningTrace:
    def test_default_is_none_backward_compat(self):
        out = AgentOutput(message="oi")
        assert out.reasoning_trace is None
        # legacy field preservado
        assert out.reasoning_steps == []

    def test_can_populate_trace(self):
        steps = [
            AgentReasoningStep(step_type="criterion", label="Exp>=3", score=0.82, matched=True),
            AgentReasoningStep(step_type="criterion", label="Loc SP", score=0.30, matched=False),
        ]
        out = AgentOutput(message="recomendo", reasoning_trace=steps)
        assert out.reasoning_trace is not None
        assert len(out.reasoning_trace) == 2
        assert out.reasoning_trace[0].matched is True
        assert out.reasoning_trace[1].matched is False

    def test_serialization_roundtrip(self):
        out = AgentOutput(
            message="x",
            reasoning_trace=[
                AgentReasoningStep(
                    step_type="action",
                    label="Tool: search",
                    data_fields_accessed=["cv_text"],
                )
            ],
        )
        payload = out.model_dump_json()
        assert "reasoning_trace" in payload
        assert "data_fields_accessed" in payload

        re_parsed = AgentOutput.model_validate_json(payload)
        assert re_parsed.reasoning_trace is not None
        assert re_parsed.reasoning_trace[0].step_type == "action"

    def test_empty_list_vs_none(self):
        out_none = AgentOutput(message="x")
        out_empty = AgentOutput(message="x", reasoning_trace=[])
        assert out_none.reasoning_trace is None
        assert out_empty.reasoning_trace == []
