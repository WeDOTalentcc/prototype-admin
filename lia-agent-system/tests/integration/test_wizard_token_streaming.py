"""PM-02 (Audit Rev 4) — token streaming via `astream_events("v2")`.

Contract tests for the wire-up between the WS layer and the canonical
`JobCreationGraph`:

  1. `JobCreationGraph.stream_invoke()` drives the compiled graph via
     `astream_events("v2")`, forwards LLM chunks to `on_token`, and
     materializes the terminal state from the top-level `on_chain_end`
     event (parity with `invoke()`).
  2. `_resume_wizard_canonical_streaming()` wires the streaming helper
     into the WS resume path: pulls prior state, applies recruiter
     updates, calls `stream_invoke()`, returns
     `(message, stage_payload, tokens_emitted)`.
  3. Token extraction failures and `on_token` callback errors NEVER
     break the wizard run — the final state is still returned.

These are pure-Python contract tests (no real WS). The real WS flow is
covered by `test_ws_reconnect_resume_wizard.py` for state persistence.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, AsyncIterator
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.easy

from app.api.v1.chat_shared import _resume_wizard_canonical_streaming
from app.domains.job_creation.graph import JobCreationGraph


def _chat_event(text: str) -> dict[str, Any]:
    return {
        "event": "on_chat_model_stream",
        "data": {"chunk": SimpleNamespace(content=text)},
    }


def _graph_end_event(final_state: dict, *, name: str = "LangGraph", parent_ids=None) -> dict[str, Any]:
    ev = {
        "event": "on_chain_end",
        "name": name,
        "data": {"output": final_state},
    }
    if parent_ids is not None:
        ev["parent_ids"] = parent_ids
    return ev


def _node_end_event(state: dict, name: str = "intake_node") -> dict[str, Any]:
    return {
        "event": "on_chain_end",
        "name": name,
        "parent_ids": ["root-run-id"],
        "data": {"output": state},
    }


async def _aiter(events: list[dict]) -> AsyncIterator[dict]:
    for ev in events:
        yield ev


# ---------------------------------------------------------------------------
# JobCreationGraph.stream_invoke
# ---------------------------------------------------------------------------


class TestStreamInvoke:

    @pytest.mark.asyncio
    async def test_emits_tokens_and_captures_final_state(self):
        wiz_g = JobCreationGraph()
        terminal = {"current_stage": "completed", "ws_stage_payload": {"data": {"message": "ok"}}}
        events = [
            _chat_event("Vou "),
            _chat_event("criar "),
            _chat_event("a vaga."),
            _graph_end_event(terminal),
        ]

        captured: list[str] = []

        async def on_token(t: str) -> None:
            captured.append(t)

        with patch.object(wiz_g._graph, "astream_events", lambda *a, **kw: _aiter(events)):
            final, n = await wiz_g.stream_invoke(
                {"current_stage": "intake", "workspace_id": "c-1", "session_id": "s-1"},
                "thread-1",
                on_token=on_token,
            )

        assert n == 3
        assert captured == ["Vou ", "criar ", "a vaga."]
        assert final == terminal

    @pytest.mark.asyncio
    async def test_falls_back_to_seed_state_when_no_terminal_event(self):
        """If the graph end event is filtered out, the seed state is the
        sane fallback so callers never see a None."""
        wiz_g = JobCreationGraph()
        seed = {"current_stage": "intake", "workspace_id": "c-1", "session_id": "s-1"}
        events = [_chat_event("partial")]

        async def on_token(_):
            pass

        with patch.object(wiz_g._graph, "astream_events", lambda *a, **kw: _aiter(events)):
            final, n = await wiz_g.stream_invoke(seed, "thread-2", on_token=on_token)

        assert n == 1
        assert final == seed

    @pytest.mark.asyncio
    async def test_root_detection_via_empty_parent_ids(self):
        """Hardening (architect feedback): if LangGraph renames the root
        run, detection must still succeed via empty ``parent_ids``."""
        wiz_g = JobCreationGraph()
        terminal = {"current_stage": "completed", "ws_stage_payload": {}}
        events = [
            _chat_event("a"),
            _node_end_event({"current_stage": "intake"}, name="intake_node"),
            _graph_end_event(terminal, name="SomeNewName", parent_ids=[]),
        ]

        async def on_token(_):
            pass

        with patch.object(wiz_g._graph, "astream_events", lambda *a, **kw: _aiter(events)):
            final, _ = await wiz_g.stream_invoke({}, "thread-root", on_token=on_token)
        assert final == terminal

    @pytest.mark.asyncio
    async def test_node_end_events_do_not_overwrite_root_state(self):
        """Subgraph/node ``on_chain_end`` events must NOT clobber the
        terminal state captured from the root run."""
        wiz_g = JobCreationGraph()
        terminal = {"current_stage": "completed"}
        events = [
            _graph_end_event(terminal, parent_ids=[]),
            _node_end_event({"current_stage": "intake"}),
        ]

        async def on_token(_):
            pass

        with patch.object(wiz_g._graph, "astream_events", lambda *a, **kw: _aiter(events)):
            final, _ = await wiz_g.stream_invoke({}, "thread-noclobber", on_token=on_token)
        assert final == terminal

    @pytest.mark.asyncio
    async def test_tertiary_fallback_picks_state_shaped_payload(self):
        """If no root marker is detectable, the last state-shaped
        payload (carrying ``current_stage``) is preferred over the seed."""
        wiz_g = JobCreationGraph()
        seed = {"current_stage": "intake", "session_id": "s-x"}
        events = [
            _node_end_event({"current_stage": "wsi_questions", "session_id": "s-x"}, name="wsi_node"),
        ]

        async def on_token(_):
            pass

        with patch.object(wiz_g._graph, "astream_events", lambda *a, **kw: _aiter(events)):
            final, _ = await wiz_g.stream_invoke(seed, "thread-tert", on_token=on_token)
        # Tertiary fallback: state-shaped node payload wins over seed.
        assert final.get("current_stage") == "wsi_questions"

    @pytest.mark.asyncio
    async def test_on_token_failure_isolated(self):
        wiz_g = JobCreationGraph()
        events = [
            _chat_event("a"),
            _chat_event("b"),
            _chat_event("c"),
            _graph_end_event({"current_stage": "done"}),
        ]

        async def flaky(t: str) -> None:
            if t == "b":
                raise RuntimeError("ws failed")

        with patch.object(wiz_g._graph, "astream_events", lambda *a, **kw: _aiter(events)):
            final, n = await wiz_g.stream_invoke({}, "thread-3", on_token=flaky)

        # Only "a" and "c" succeeded; "b" was isolated.
        assert n == 2
        assert final == {"current_stage": "done"}


# ---------------------------------------------------------------------------
# _resume_wizard_canonical_streaming
# ---------------------------------------------------------------------------


class TestResumeWizardCanonicalStreaming:

    @pytest.mark.asyncio
    async def test_wires_stream_invoke_with_merged_state(self):
        """Verifies the WS resume path merges prior state + recruiter
        updates and forwards `on_token` to the graph stream."""
        recorded: dict[str, Any] = {}

        async def fake_stream_invoke(state, thread_id, on_token):
            recorded["state"] = state
            recorded["thread_id"] = thread_id
            await on_token("hello ")
            await on_token("world")
            return (
                {
                    "current_stage": "wsi_questions",
                    "ws_stage_payload": {
                        "type": "wizard.stage",
                        "data": {"message": "Perguntas WSI prontas."},
                    },
                },
                2,
            )

        prior_snapshot = SimpleNamespace(values={"intake_payload": {"title": "Eng"}})
        captured_tokens: list[str] = []

        async def on_token(t: str) -> None:
            captured_tokens.append(t)

        from app.domains.job_creation import graph as graph_module

        with patch.object(graph_module.job_creation_graph, "stream_invoke", fake_stream_invoke), \
             patch.object(graph_module.job_creation_graph._graph, "get_state", return_value=prior_snapshot):
            msg, payload, tokens = await _resume_wizard_canonical_streaming(
                "thread-77",
                {
                    "context": {"hitl_approved": True, "draft": {"approved": True}},
                    "approval_payload": {"reviewer": "u-1"},
                },
                on_token,
            )

        assert tokens == 2
        assert captured_tokens == ["hello ", "world"]
        assert msg == "Perguntas WSI prontas."
        assert payload["data"]["message"] == "Perguntas WSI prontas."
        assert recorded["thread_id"] == "thread-77"
        # Merged state carries prior + recruiter updates + hitl_approved.
        merged = recorded["state"]
        assert merged.get("intake_payload") == {"title": "Eng"}
        assert merged.get("hitl_approved") is True
        assert merged.get("reviewer") == "u-1"
        assert merged.get("draft") == {"approved": True}

    @pytest.mark.asyncio
    async def test_falls_back_message_when_payload_empty(self):
        async def fake_stream_invoke(state, thread_id, on_token):
            return ({"current_stage": "intake"}, 0)

        from app.domains.job_creation import graph as graph_module

        prior_snapshot = SimpleNamespace(values={})
        async def on_token(_):
            pass

        with patch.object(graph_module.job_creation_graph, "stream_invoke", fake_stream_invoke), \
             patch.object(graph_module.job_creation_graph._graph, "get_state", return_value=prior_snapshot):
            msg, payload, tokens = await _resume_wizard_canonical_streaming(
                "thread-88", {"context": {}, "approval_payload": {}}, on_token,
            )

        assert tokens == 0
        assert msg == "Captei a vaga. Vou seguir para o próximo passo."
        assert payload == {}

    @pytest.mark.asyncio
    async def test_uuid_company_id_sse_wizard_does_not_ask_for_company(self, monkeypatch):
        """Task #967 regression: SSE wizard path with UUID ``company_id``
        (Demo Company canônica) must NEVER ask the recruiter for the
        company name/ID in the chat. Reproduces the exact flow used by
        ``app/api/v1/agent_chat_sse.py`` (lines 332-353): handler resolves
        the tenant snippet and calls ``WizardSessionService.process_message``
        with both the snippet and the JWT-verified UUID ``company_id``.

        Three contracts in one test:
          1. ``state["company_id"]`` chega ao grafo como UUID normalizado
             (root cause #1 — ``CompanyId.parse`` aceita UUID v4).
          2. ``state["tenant_context_snippet"]`` chega ao grafo
             (root cause #2 — propagação via ``_CONTEXT_CARRY_KEYS``).
          3. A primeira resposta da LIA NÃO contém frases-sintoma do bug
             ("qual o ID da empresa?", "qual a empresa?", "informe a
             empresa", "sua empresa,") — contrato user-facing canônico.
        """
        from app.domains.job_creation import graph as graph_mod
        from app.domains.job_creation.services import wizard_session_service as wss_mod

        monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "true")

        DEMO_COMPANY_UUID = "00000000-0000-4000-a000-000000000001"
        captured: dict[str, Any] = {}

        class _FakeGraph:
            async def stream_invoke(self, state, thread_id, on_token=None):
                captured["state"] = state
                # Resposta canônica: response builder lê de
                # ws_stage_payload.data.message — devolve uma resposta
                # SAUDÁVEL (mencionando a Demo Company), provando que com
                # snippet propagado a LIA não precisa perguntar a empresa.
                return (
                    {
                        "current_stage": "intake",
                        "company_id": state.get("company_id"),
                        "ws_stage_payload": {
                            "data": {
                                "message": (
                                    "Perfeito! Vamos criar essa vaga "
                                    "para a Demo Company."
                                ),
                            },
                        },
                    },
                    0,
                )

        monkeypatch.setattr(graph_mod, "get_job_creation_graph", lambda: _FakeGraph())

        async def _fake_prior_state(_cls, _thread_id):
            return {}

        monkeypatch.setattr(
            wss_mod.WizardSessionService, "_get_prior_state",
            classmethod(_fake_prior_state),
        )

        # Snippet é o mesmo formato injetado pelo handler SSE em
        # agent_chat_sse.py:339-342 (TenantContext.to_prompt_snippet +
        # build_authenticated_snippet).
        snippet = (
            "Empresa: Demo Company (Tecnologia)\n"
            "Plano: enterprise\nTimezone: America/Sao_Paulo\n"
            "Authenticated as company_id=00000000-0000-4000-a000-000000000001"
        )

        msg, _payload, _tokens = await wss_mod.WizardSessionService.process_message(
            thread_id="wiz-sse-967",
            user_message="Quero criar uma vaga de Engenheiro de Software",
            user_id="recruiter-1",
            company_id=DEMO_COMPANY_UUID,
            session_id="sse-sess-967",
            context={
                "tenant_context_snippet": snippet,
                "metadata": {"channel": "sse"},
            },
            on_token=None,
        )

        # Contrato 1: UUID company_id chega ao grafo normalizado
        assert captured["state"]["company_id"] == DEMO_COMPANY_UUID
        # Contrato 2: snippet propagado via _CONTEXT_CARRY_KEYS
        assert captured["state"]["tenant_context_snippet"] == snippet
        # Contrato 3 (user-facing): a LIA NUNCA pergunta a empresa
        bug_phrases = [
            "qual o id da empresa",
            "qual a empresa",
            "id da sua empresa",
            "informe a empresa",
            "informe o id da empresa",
            "preciso saber a empresa",
            "em qual empresa",
        ]
        msg_lower = (msg or "").lower()
        for phrase in bug_phrases:
            assert phrase not in msg_lower, (
                f"Resposta do wizard contém frase-sintoma do bug Task #967: "
                f"{phrase!r}\nResposta completa: {msg!r}"
            )

    @pytest.mark.asyncio
    async def test_handles_missing_prior_state_snapshot(self):
        """Checkpointer miss must not break resume — empty prior state is
        the safe degradation."""
        async def fake_stream_invoke(state, thread_id, on_token):
            # Verify the merge happened against an empty prior.
            assert state == {"hitl_approved": True}
            return ({"current_stage": "completed"}, 0)

        from app.domains.job_creation import graph as graph_module

        async def on_token(_):
            pass

        def _raise(*_a, **_kw):
            raise RuntimeError("no checkpoint")

        with patch.object(graph_module.job_creation_graph, "stream_invoke", fake_stream_invoke), \
             patch.object(graph_module.job_creation_graph._graph, "get_state", side_effect=_raise):
            msg, payload, tokens = await _resume_wizard_canonical_streaming(
                "thread-99", {"context": {}, "approval_payload": {}}, on_token,
            )

        assert tokens == 0
        assert msg == "Vaga criada com sucesso."
        assert payload == {}
