"""Sensor AD3 — agentic loop extrai/acumula response_blocks de tool results.

Pina _extract_response_blocks (helper que o loop usa pra promover blocos RRP
emitidos por tools-as-renderers). Sem isso, o caminho dominante (agentic loop)
nunca emitiria RRP — o gap que deixou o moat invisivel em perguntas naturais.
"""
from app.orchestrator.execution.agentic_loop import _extract_response_blocks


class _FakeResult:
    def __init__(self, success, result):
        self.success = success
        self.result = result


def test_extracts_blocks_from_tool_data():
    r = _FakeResult(True, {"data": {"response_blocks": [{"kind": "comparison_table"}]}})
    assert _extract_response_blocks(r) == [{"kind": "comparison_table"}]


def test_empty_when_no_blocks():
    assert _extract_response_blocks(_FakeResult(True, {"data": {}})) == []


def test_empty_when_tool_failed():
    r = _FakeResult(False, {"data": {"response_blocks": [{"kind": "x"}]}})
    assert _extract_response_blocks(r) == []


def test_empty_on_none_or_bad_shape():
    assert _extract_response_blocks(None) == []
    assert _extract_response_blocks(_FakeResult(True, "not-a-dict")) == []
    assert _extract_response_blocks(_FakeResult(True, {"data": "x"})) == []
