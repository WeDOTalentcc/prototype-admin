"""
tests/unit/test_structured_data_shapes.py — R-027

Snapshot tests pinning each StructuredData shape + StructuredDataAdapter behavior.
Prevents silent regression when structured_data schema changes.
"""
import pytest
from app.shared.chat_types import (
    ActionResultStructuredData,
    JobsManagementStructuredData,
    KanbanStructuredData,
    ScoreStructuredData,
    StructuredDataAdapter,
    TalentStructuredData,
)


class TestStructuredDataModels:
    def test_kanban_defaults(self):
        sd = KanbanStructuredData()
        assert sd.kind == "kanban"
        assert sd.candidates == []
        assert sd.suggested_actions == []

    def test_kanban_with_data(self):
        sd = KanbanStructuredData(
            candidates=[{"id": "c1", "name": "Alice"}],
            suggested_actions=["Schedule interview"],
            score_breakdown={"technical": 0.85},
        )
        assert sd.candidates[0]["name"] == "Alice"
        assert sd.score_breakdown["technical"] == pytest.approx(0.85)

    def test_jobs_management_defaults(self):
        sd = JobsManagementStructuredData()
        assert sd.kind == "jobs_management"
        assert sd.state_updates is None

    def test_talent_defaults(self):
        sd = TalentStructuredData()
        assert sd.kind == "talent"
        assert sd.total_found == 0

    def test_score_defaults(self):
        sd = ScoreStructuredData()
        assert sd.kind == "score"
        assert sd.confidence == 0.0

    def test_action_result_defaults(self):
        sd = ActionResultStructuredData()
        assert sd.kind == "action_result"
        assert sd.data == {}


class TestStructuredDataAdapterUnwrap:
    def test_none_passthrough(self):
        assert StructuredDataAdapter.unwrap(None) is None

    def test_no_double_wrap(self):
        sd = {"candidates": [{"id": "c1"}], "total_found": 1}
        result = StructuredDataAdapter.unwrap(sd)
        assert result == sd  # unchanged

    def test_double_wrap_detected_and_fixed(self):
        """Bug R-027: cache serialization could produce {"structured_data": {...}}."""
        inner = {"kind": "kanban", "candidates": []}
        double_wrapped = {"structured_data": inner}
        result = StructuredDataAdapter.unwrap(double_wrapped)
        assert result == inner

    def test_double_wrap_only_when_single_key(self):
        """Do NOT unwrap if dict has other keys besides structured_data."""
        sd = {"structured_data": {"kind": "kanban"}, "extra": "value"}
        result = StructuredDataAdapter.unwrap(sd)
        assert result == sd  # not unwrapped — has extra key


class TestStructuredDataAdapterParse:
    def test_parse_kanban(self):
        sd = {"kind": "kanban", "candidates": [{"id": "x"}]}
        result = StructuredDataAdapter.parse(sd)
        assert isinstance(result, KanbanStructuredData)
        assert result.candidates[0]["id"] == "x"

    def test_parse_talent(self):
        sd = {"kind": "talent", "total_found": 42}
        result = StructuredDataAdapter.parse(sd)
        assert isinstance(result, TalentStructuredData)
        assert result.total_found == 42

    def test_parse_score(self):
        sd = {"kind": "score", "score_breakdown": {"tech": 0.9}, "confidence": 0.8}
        result = StructuredDataAdapter.parse(sd)
        assert isinstance(result, ScoreStructuredData)
        assert result.confidence == pytest.approx(0.8)

    def test_unknown_kind_fallback_to_dict(self):
        sd = {"kind": "unknown_future_kind", "data": "something"}
        result = StructuredDataAdapter.parse(sd)
        assert isinstance(result, dict)  # safe fallback
        assert result["kind"] == "unknown_future_kind"

    def test_no_kind_fallback_to_dict(self):
        sd = {"candidates": [{"id": "c1"}]}
        result = StructuredDataAdapter.parse(sd)
        assert isinstance(result, dict)

    def test_double_wrap_then_parse(self):
        """Unwrap then parse — end-to-end for cache hit path."""
        inner = {"kind": "talent", "total_found": 7}
        double_wrapped = {"structured_data": inner}
        result = StructuredDataAdapter.parse(double_wrapped)
        assert isinstance(result, TalentStructuredData)
        assert result.total_found == 7

    def test_parse_none_returns_none(self):
        assert StructuredDataAdapter.parse(None) is None

    def test_parse_never_raises_on_invalid_schema(self):
        """Even with invalid data for a known kind, falls back gracefully."""
        sd = {"kind": "kanban", "candidates": "not-a-list"}
        result = StructuredDataAdapter.parse(sd)
        # Either typed (if pydantic coerces) or raw dict — never raises
        assert result is not None
