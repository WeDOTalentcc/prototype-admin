"""TDD/sensor P0 (2026-06-06): dedup de SystemMessage em turno de continuacao.

Pina que _messages_for_continuation remove o SystemMessage re-injetado quando o
checkpointer ja tem estado (turno 2+), evitando 'Received multiple non-consecutive
system messages' que quebrava todo turno apos o 1o no chat (langgraph_base._run_graph).
"""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from lia_agents_core.langgraph_base import _messages_for_continuation


def test_turno1_sem_estado_mantem_system():
    msgs = [SystemMessage(content="persona"), HumanMessage(content="oi")]
    assert _messages_for_continuation(msgs, has_prior_state=False) is msgs


def test_continuacao_remove_system_reinjetado():
    msgs = [SystemMessage(content="persona"), HumanMessage(content="turno 2")]
    out = _messages_for_continuation(msgs, has_prior_state=True)
    assert [type(m).__name__ for m in out] == ["HumanMessage"]
    assert out[0].content == "turno 2"


def test_continuacao_preserva_human_e_ai():
    msgs = [
        SystemMessage(content="s"), HumanMessage(content="a"),
        AIMessage(content="b"), HumanMessage(content="c"),
    ]
    out = _messages_for_continuation(msgs, has_prior_state=True)
    assert [type(m).__name__ for m in out] == ["HumanMessage", "AIMessage", "HumanMessage"]


def test_none_ou_vazio_nao_quebra():
    assert _messages_for_continuation(None, has_prior_state=True) == []
    assert _messages_for_continuation([], has_prior_state=True) == []
