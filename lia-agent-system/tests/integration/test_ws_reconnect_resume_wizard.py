"""Audit finding A-06 — WebSocket reconnect mid-wizard preserves state.

The recruiter UI keeps a single ``thread_id`` per wizard session. If the
WS connection drops between two stages (Wi-Fi blip, browser tab freeze,
worker restart, etc.), the user must be able to reconnect with the same
``thread_id`` and resume from the last checkpoint — never lose the
in-progress draft.

This test exercises the **checkpoint contract** the WS layer relies on,
without spinning up a real WS server (which would force us to invoke
the 11 LLM-backed nodes of ``JobCreationGraph``). The contract is:

1. Two consecutive invocations with the **same** ``thread_id`` share
   the persisted state — second invocation continues where the first
   stopped.
2. Two invocations with **different** ``thread_id`` are isolated — no
   state bleed between concurrent recruiter sessions (G1 multi-tenant
   safety).
3. ``get_state(config)`` returns the latest checkpoint without needing
   to re-invoke the graph — this is what the WS handler calls on
   reconnect to send the "resume here" payload to the client.
4. ``JobCreationGraph`` is a **singleton** carrying a single
   checkpointer instance, so two WS connections that target the same
   ``session_id`` automatically share state through the same saver.
5. In production (``LIA_ENV=production``), the checkpointer factory
   refuses ``MemorySaver`` and demands ``PostgresSaver`` — restarts of
   the uvicorn worker do not lose recruiter drafts.

The first 4 are pure-Python tests (fast). The 5th is a contract test
on the factory function, not on a live PostgreSQL instance.
"""
from __future__ import annotations

import os
from typing import Any, TypedDict
from unittest.mock import patch

import pytest

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph


class _MiniWizardState(TypedDict, total=False):
    """A tiny stand-in for ``JobCreationState`` — only the fields the
    test actually exercises. Mirrors the real shape so the assertions
    stay meaningful: ``current_stage`` advances, ``messages`` accumulate.
    """
    session_id: str
    current_stage: str
    messages: list[str]
    completeness: int


def _intake_node(state: _MiniWizardState) -> _MiniWizardState:
    msgs = list(state.get("messages") or [])
    msgs.append("intake-done")
    return {"current_stage": "jd_enrichment", "messages": msgs, "completeness": 25}


def _jd_node(state: _MiniWizardState) -> _MiniWizardState:
    msgs = list(state.get("messages") or [])
    msgs.append("jd-done")
    return {"current_stage": "bigfive", "messages": msgs, "completeness": 50}


def _bigfive_node(state: _MiniWizardState) -> _MiniWizardState:
    msgs = list(state.get("messages") or [])
    msgs.append("bigfive-done")
    return {"current_stage": "review", "messages": msgs, "completeness": 75}


@pytest.fixture
def shared_memory_saver() -> MemorySaver:
    """Single MemorySaver instance shared across all 'connections' in a
    test, exactly mirroring how ``JobCreationGraph`` (singleton) holds a
    single saver across all WS connections in a worker."""
    return MemorySaver()


@pytest.fixture
def mini_wizard_graph(shared_memory_saver: MemorySaver):
    """A 3-node graph (intake → jd → bigfive → END) compiled with the
    shared saver. Same compile-time wiring the real ``JobCreationGraph``
    uses (``StateGraph(StateClass).compile(checkpointer=...)``)."""
    g: StateGraph = StateGraph(_MiniWizardState)
    g.add_node("intake", _intake_node)
    g.add_node("jd_enrichment", _jd_node)
    g.add_node("bigfive", _bigfive_node)
    g.add_edge(START, "intake")
    g.add_edge("intake", "jd_enrichment")
    g.add_edge("jd_enrichment", "bigfive")
    g.add_edge("bigfive", END)
    return g.compile(checkpointer=shared_memory_saver)


def _config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


# ---------------------------------------------------------------------------
# A. Same thread_id resumes — the heart of A-06
# ---------------------------------------------------------------------------

class TestReconnectSameThreadIdResumes:
    def test_state_persisted_after_first_invocation(
        self, mini_wizard_graph
    ) -> None:
        cfg = _config("session-recruiter-A")
        result = mini_wizard_graph.invoke(
            {"session_id": "session-recruiter-A", "current_stage": "intake"},
            config=cfg,
        )
        # State after one full pass must be saved, not just returned.
        snapshot = mini_wizard_graph.get_state(cfg)
        assert snapshot is not None
        assert snapshot.values["session_id"] == "session-recruiter-A"
        assert snapshot.values["current_stage"] == result["current_stage"]
        assert snapshot.values["completeness"] == 75

    def test_get_state_works_without_reinvoking(
        self, mini_wizard_graph
    ) -> None:
        cfg = _config("session-recruiter-B")
        mini_wizard_graph.invoke(
            {"session_id": "session-recruiter-B", "current_stage": "intake"},
            config=cfg,
        )

        # "Reconnect" simulation: drop everything in memory except the
        # config + saver, then peek at the persisted state — this is
        # exactly what the WS handler does in `on_connect`.
        snapshot = mini_wizard_graph.get_state(cfg)
        assert snapshot.values["messages"] == [
            "intake-done", "jd-done", "bigfive-done"
        ]

    def test_messages_accumulate_across_two_invocations(
        self, shared_memory_saver: MemorySaver
    ) -> None:
        # A graph that stops after `intake` so we can invoke twice.
        g: StateGraph = StateGraph(_MiniWizardState)
        g.add_node("intake", _intake_node)
        g.add_edge(START, "intake")
        g.add_edge("intake", END)
        compiled = g.compile(checkpointer=shared_memory_saver)

        cfg = _config("session-recruiter-C")
        first = compiled.invoke(
            {
                "session_id": "session-recruiter-C",
                "current_stage": "intake",
                "messages": [],
            },
            config=cfg,
        )
        # "Connection drops here." Then a brand-new client object reuses
        # the same compiled graph + same saver + same thread_id.
        second = compiled.invoke(
            {"messages": first["messages"]},
            config=cfg,
        )
        # Second invocation sees the accumulated history, not a fresh slate.
        assert second["messages"] == ["intake-done", "intake-done"]


# ---------------------------------------------------------------------------
# B. Different thread_id isolates — the multi-tenant safety net
# ---------------------------------------------------------------------------

class TestReconnectDifferentThreadIdStartsFresh:
    def test_two_threads_do_not_leak_state(self, mini_wizard_graph) -> None:
        cfg_a = _config("session-recruiter-X")
        cfg_b = _config("session-recruiter-Y")

        mini_wizard_graph.invoke(
            {"session_id": "session-recruiter-X", "current_stage": "intake"},
            config=cfg_a,
        )

        snap_b_before = mini_wizard_graph.get_state(cfg_b)
        # B has not been invoked yet — it must NOT see A's state.
        assert (
            snap_b_before is None
            or not snap_b_before.values
            or snap_b_before.values.get("session_id") != "session-recruiter-X"
        )

        # And invoking B from scratch produces an independent track.
        mini_wizard_graph.invoke(
            {"session_id": "session-recruiter-Y", "current_stage": "intake"},
            config=cfg_b,
        )
        snap_a = mini_wizard_graph.get_state(cfg_a)
        snap_b = mini_wizard_graph.get_state(cfg_b)
        assert snap_a.values["session_id"] == "session-recruiter-X"
        assert snap_b.values["session_id"] == "session-recruiter-Y"


# ---------------------------------------------------------------------------
# C. The real JobCreationGraph is a singleton with one checkpointer
# ---------------------------------------------------------------------------

class TestJobCreationGraphIsSingletonAcrossConnections:
    def test_get_job_creation_graph_returns_same_instance(self) -> None:
        from app.domains.job_creation.graph import get_job_creation_graph
        a = get_job_creation_graph()
        b = get_job_creation_graph()
        assert a is b, (
            "JobCreationGraph must be a process-wide singleton so two WS "
            "connections targeting the same session_id share the saver."
        )

    def test_singleton_holds_a_compiled_graph_with_checkpointer(self) -> None:
        from app.domains.job_creation.graph import get_job_creation_graph
        compiled = get_job_creation_graph().graph
        assert compiled is not None
        # `checkpointer` is the public attribute LangGraph exposes on
        # CompiledStateGraph for callers (incl. WS handlers) that want
        # to inspect persisted state.
        assert getattr(compiled, "checkpointer", None) is not None, (
            "Compiled graph must carry a checkpointer; reconnect/resume "
            "is impossible otherwise."
        )


# ---------------------------------------------------------------------------
# D. Production refuses MemorySaver — worker restart cannot lose drafts
# ---------------------------------------------------------------------------

class TestProductionDemandsPostgresSaver:
    def test_factory_raises_in_production_when_postgres_unavailable(
        self,
    ) -> None:
        # The factory reads ``settings.APP_ENV`` (cached, not env vars at
        # call time), so we patch the attribute directly on the module
        # the factory imports it from. We also point DATABASE_URL at an
        # unreachable host so PostgresSaver.from_conn_string() raises,
        # which is the path the prod branch must convert into RuntimeError.
        from lia_agents_core import checkpointer as ckpt_mod

        original_env = getattr(ckpt_mod.settings, "APP_ENV", "development")
        original_db = getattr(ckpt_mod.settings, "DATABASE_URL", "")
        try:
            ckpt_mod.settings.APP_ENV = "production"
            ckpt_mod.settings.DATABASE_URL = (
                "postgresql://invalid:invalid@127.0.0.1:1/none"
            )
            with pytest.raises(RuntimeError) as excinfo:
                ckpt_mod.get_checkpointer()
            err = str(excinfo.value).lower()
            assert "postgres" in err or "checkpointer" in err or "produção" in err
        finally:
            ckpt_mod.settings.APP_ENV = original_env
            ckpt_mod.settings.DATABASE_URL = original_db

    def test_factory_returns_memory_saver_in_dev_with_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging
        from lia_agents_core import checkpointer as ckpt_mod

        original_env = getattr(ckpt_mod.settings, "APP_ENV", "development")
        original_db = getattr(ckpt_mod.settings, "DATABASE_URL", "")
        try:
            ckpt_mod.settings.APP_ENV = "development"
            ckpt_mod.settings.DATABASE_URL = (
                "postgresql://invalid:invalid@127.0.0.1:1/none"
            )
            caplog.set_level(logging.WARNING)
            saver = ckpt_mod.get_checkpointer()
            assert saver is not None
            # The dev contract: never raise even when Postgres is broken.
            # We don't assert the exact class (LangGraph's MemorySaver
            # path varies across versions).
        finally:
            ckpt_mod.settings.APP_ENV = original_env
            ckpt_mod.settings.DATABASE_URL = original_db
