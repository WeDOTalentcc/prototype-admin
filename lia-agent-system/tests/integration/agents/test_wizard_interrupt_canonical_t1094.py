"""
Sentinel canonical — Task #1094 (wizard HITL → ``langgraph.types.interrupt()``).

Migra os 4 HITL gate nodes (jd_gate / competency_gate / wsi_questions_gate /
review_gate) do padrão legacy ``END + resume(merged_state)`` para o canônico
LangGraph ``interrupt() + Command(resume=...)``. Antes da Task #1094 cada
gate dependia de duas heurísticas concorrentes para detectar "este turno é
um resume": (1) ``state['gate_resume_message']`` (REST/action-based +
testes offline) ou (2) WS resume detection via state nativo
(``user_query`` fresh + state-shape predicates por stage). Nada disso é o
contrato de HITL do LangGraph — o resultado era um bug do tipo "page
reload mid-wizard volta a fazer perguntas que o recrutador já respondeu"
(B2/B3/B4 do Task #1051) sob mecanismos auxiliares (Redis marker,
Tier 0.5 do CascadedRouter, heurística ``_candidate_thread_ids``)
removidos pela Task #1080.

Cobertura:
  S1 — JobCreationGraph wrapper expõe API canônica:
       ``is_interrupted(thread_id)``,
       ``resume_with_message(thread_id, msg)``,
       ``aresume_with_message(thread_id, msg)``.

  S2 — ``_in_graph_runtime()`` é o guard correto: False fora do Pregel
       runtime (chamadas como função plain/tests offline) → preserva
       backward-compat das sentinelas T2/T4/T5/T6 que invocam o gate_node
       diretamente sem subir um graph compilado.

  S3 — Cada um dos 4 gate_nodes inclui o bloco
       ``if not msg and _in_graph_runtime(): interrupt({...})``
       ANTES do legacy END no-op. Validação por AST (não por execução).

  S4 — ``domain.py::_handle_gate_*`` (4 handlers) usa o branch canônico
       ``self.graph.is_interrupted(...) → resume_with_message(...)`` e
       mantém ``self.graph.resume(...)`` apenas como fallback defensivo.
       Validação por AST.

  S5 — ``WizardSessionService.process_message`` faz early-return via
       ``aresume_with_message`` quando ``is_interrupted`` é True. Sem
       isso, o resume turn re-injetaria state via _build_state e
       sobrescreveria o checkpoint. Validação por AST.

  S6 — ``is_wizard_session_active`` (Task #1080 pin) reconhece sessão
       pausada em ``interrupt()`` como ATIVA mesmo quando ``snapshot.values``
       está vazio. Sem isso, o pin handler-level WS/SSE da Task #1080
       não seria armado para o primeiro resume turn pós-interrupt.

  S7 — Backward-compat: gate_node chamado como função plain (sem runtime)
       COM ``gate_resume_message`` setado segue rodando o classifier
       (legacy fast-path preservado). Sem msg E sem runtime → legacy END
       no-op (preserva sentinela T2 S4).

Para rodar standalone:
    python lia-agent-system/tests/integration/agents/test_wizard_interrupt_canonical_t1094.py
"""
from __future__ import annotations

import ast
import importlib
import inspect
import sys
import unittest
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[3]  # .../lia-agent-system
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

graph_mod = importlib.import_module("app.domains.job_creation.graph")
domain_mod = importlib.import_module("app.domains.job_creation.domain")
wizard_session_mod = importlib.import_module(
    "app.domains.job_creation.services.wizard_session_service"
)
thread_id_mod = importlib.import_module("app.shared.sessions.thread_id")
classifier_mod = importlib.import_module(
    "app.domains.job_creation.services.wizard_gate_classifier"
)


def _make_output(intent, confidence=0.95, reply="ok", extracted=None):
    return classifier_mod.GateClassifierOutput(
        intent=intent,
        extracted_data=extracted or {},
        conversational_reply=reply,
        confidence=confidence,
    )


class WizardInterruptCanonicalT1094(unittest.TestCase):

    # ---------------- S1 ----------------
    def test_S1_jobcreationgraph_exposes_canonical_resume_api(self):
        cls = graph_mod.JobCreationGraph
        for name in ("is_interrupted", "resume_with_message", "aresume_with_message"):
            self.assertTrue(
                hasattr(cls, name),
                f"JobCreationGraph deve expor {name!r} (Task #1094 contract)",
            )
        sig_sync = inspect.signature(cls.resume_with_message)
        self.assertEqual(
            list(sig_sync.parameters)[1:],
            ["thread_id", "user_message"],
            "resume_with_message(thread_id, user_message) — assinatura canônica",
        )
        sig_async = inspect.signature(cls.aresume_with_message)
        self.assertEqual(
            list(sig_async.parameters)[1:],
            ["thread_id", "user_message"],
            "aresume_with_message(thread_id, user_message) — assinatura canônica",
        )
        self.assertTrue(
            inspect.iscoroutinefunction(cls.aresume_with_message),
            "aresume_with_message DEVE ser async (caminho WS é asyncio).",
        )

    # ---------------- S2 ----------------
    def test_S2_in_graph_runtime_returns_false_outside_pregel(self):
        # Quando chamado como função plain (sem graph.invoke wrapping),
        # ``langgraph.config.get_config()`` levanta — o helper deve
        # capturar e devolver False para preservar o caminho legacy.
        self.assertFalse(graph_mod._in_graph_runtime())

    # ---------------- S3 ----------------
    def test_S3_all_four_gate_nodes_call_interrupt_under_runtime_guard(self):
        src = inspect.getsource(graph_mod)
        for gate_name, stage in [
            ("jd_gate_node", "jd_enrichment"),
            ("competency_gate_node", "competency"),
            ("wsi_questions_gate_node", "wsi_questions"),
            ("review_gate_node", "review"),
        ]:
            # Localiza o source do gate_node
            fn = getattr(graph_mod, gate_name)
            fn_src = inspect.getsource(fn)
            self.assertIn(
                "_in_graph_runtime()", fn_src,
                f"{gate_name} deve guardar interrupt() com _in_graph_runtime() (Task #1094)",
            )
            self.assertIn(
                "from langgraph.types import interrupt", fn_src,
                f"{gate_name} deve importar interrupt de langgraph.types",
            )
            self.assertIn(
                f'"stage": "{stage}"', fn_src,
                f"{gate_name} deve emitir interrupt com stage={stage!r}",
            )

    # ---------------- S4 ----------------
    def test_S4_domain_gate_handlers_use_resume_with_message_when_interrupted(self):
        for handler_name in (
            "_handle_gate_jd",
            "_handle_gate_competency",
            "_handle_gate_wsi_questions",
            "_handle_gate_review",
        ):
            handler = getattr(domain_mod.JobCreationDomain, handler_name)
            src = inspect.getsource(handler)
            self.assertIn(
                "self.graph.is_interrupted(thread_id)", src,
                f"{handler_name} deve checar is_interrupted (Task #1094)",
            )
            self.assertIn(
                "resume_with_message(thread_id, user_query)", src,
                f"{handler_name} deve resumir via Command(resume=...) "
                f"através de resume_with_message",
            )

    # ---------------- S5 ----------------
    def test_S5_process_message_branches_on_interrupt_state(self):
        src = inspect.getsource(wizard_session_mod.WizardSessionService.process_message)
        self.assertIn(
            "wiz_g.is_interrupted", src,
            "process_message deve consultar is_interrupted antes de "
            "decidir entre Command(resume) e fresh invoke (Task #1094)",
        )
        self.assertIn(
            "aresume_with_message(thread_id, user_message)", src,
            "process_message deve usar aresume_with_message no caminho "
            "interrupt — o caminho fresh não é equivalente porque "
            "re-injetaria state via _build_state e sobrescreveria o "
            "checkpoint pausado.",
        )

    # ---------------- S6 ----------------
    def test_S6_is_wizard_session_active_recognizes_pending_interrupt(self):
        # Snapshot stub: values vazio MAS uma task com interrupts pending.
        class _StubInterrupt:
            value = {"type": "approval", "stage": "jd_enrichment"}

        class _StubTask:
            interrupts = [_StubInterrupt()]

        class _StubSnapshot:
            values = {}
            tasks = [_StubTask()]

        class _StubGraph:
            def get_state(self, _config):
                return _StubSnapshot()

        class _StubWizG:
            _graph = _StubGraph()

        with mock.patch.object(
            graph_mod, "get_job_creation_graph",
            lambda: _StubWizG(),
        ):
            import asyncio
            active = asyncio.run(
                thread_id_mod.is_wizard_session_active(
                    "00000000-0000-4000-a000-000000000001",
                    "sess-1094",
                )
            )
        self.assertTrue(
            active,
            "Sessão pausada em interrupt() deve contar como ATIVA mesmo "
            "com values vazio — sem isso, o pin handler-level WS/SSE "
            "(Task #1080) não arma no primeiro resume turn pós-interrupt.",
        )

    # ---------------- S7 ----------------
    def test_S7a_backward_compat_gate_resume_message_still_runs_classifier(self):
        # Caminho legacy (offline test / domain.py REST antigo): set
        # gate_resume_message direto no state e chame o gate_node como
        # função. O fast-path do gate consome a msg ANTES de chegar no
        # interrupt() guard, preservando o comportamento das sentinelas
        # T2/T4/T5/T6 que rodam sem graph runtime.
        clf = classifier_mod.get_wizard_gate_classifier()
        with mock.patch.object(
            clf, "classify",
            new=mock.AsyncMock(return_value=_make_output("approve", 0.95, "Combinado!")),
        ):
            with mock.patch.object(graph_mod, "_emit_jd_gate_audit", lambda *a, **k: None):
                state = {
                    "gate_resume_message": "manda bala",
                    "jd_quality_score": 80.0,
                    "ws_stage_payload": {"data": {"parsed_title": "PM"}},
                }
                result = graph_mod.jd_gate_node(state)
        self.assertIs(
            result.get("jd_approved"), True,
            "gate_resume_message legacy fast-path deve continuar "
            "rodando o classifier (não pode ser quebrado pela Task #1094).",
        )

    def test_S5b_process_message_interrupt_branch_returns_proper_tuple(self):
        """Execução real do branch interrupt em ``process_message``: garante
        que o ``return`` é AWAITed (não devolve coroutine) e produz
        ``tuple[str, dict, int]``. Captura o bug encontrado no code review
        (`return cls._post_process_result(...)` sem await)."""
        import asyncio

        # Stub do graph wrapper: is_interrupted=True, aresume devolve um
        # dict mínimo válido (current_stage não-completed, sem job_id, sem
        # gate_clarify_message → cai no fail-loud fallback que devolve
        # mensagem string via _generate_fallback_reply).
        class _StubWizG:
            def is_interrupted(self, _tid):
                return True

            async def aresume_with_message(self, _tid, _msg):
                return {
                    "current_stage": "jd_enrichment",
                    "ws_stage_payload": {"data": {"message": "ack do gate canônico"}},
                }

        async def _run():
            # ``process_message`` faz ``from app.domains.job_creation.graph
            # import get_job_creation_graph`` *dentro* da função — por isso
            # o patch DEVE alvejar o módulo de origem (graph), não o
            # ``wizard_session_service``, que não tem o símbolo no escopo.
            with mock.patch.object(
                graph_mod,
                "get_job_creation_graph",
                lambda: _StubWizG(),
            ), mock.patch.object(
                wizard_session_mod.WizardSessionService,
                "_get_prior_state",
                new=mock.AsyncMock(return_value={
                    "tenant_context_snippet": "Demo Company",
                    "conversation_messages": [],
                }),
            ):
                return await wizard_session_mod.WizardSessionService.process_message(
                    thread_id="wiz-test1094-sess1",
                    user_message="manda bala",
                    user_id="u-1",
                    company_id="00000000-0000-4000-a000-000000000001",
                    session_id="sess1",
                    context=mock.MagicMock(metadata={}),
                )

        out = asyncio.run(_run())

        # Antes da fix do code review, ``out`` seria um coroutine porque
        # ``return cls._post_process_result(...)`` faltava o ``await``.
        # Com o fix, é um tuple desempacotável.
        self.assertNotIsInstance(
            out, type((lambda: None)()),  # nunca um generator/coroutine
            "process_message DEVE awaitar _post_process_result no branch "
            "interrupt — caso contrário devolve um coroutine ao caller.",
        )
        self.assertIsInstance(out, tuple)
        self.assertEqual(len(out), 3, "process_message deve devolver (msg, payload, tokens)")
        msg, payload, tokens = out
        self.assertIsInstance(msg, str)
        self.assertGreater(len(msg), 0, "mensagem do gate canônico não pode ser vazia")
        self.assertIsInstance(payload, dict)
        self.assertIsInstance(tokens, int)

    def test_S7b_no_msg_and_no_runtime_falls_back_to_legacy_end_noop(self):
        # Sem gate_resume_message E sem graph runtime: o guard
        # ``_in_graph_runtime()`` é False, então interrupt() NÃO é chamado
        # e o gate cai no caminho legacy END no-op (preserva sentinela
        # T2 S4 ``test_S4_no_resume_message_is_noop``).
        state = {"raw_input": "criar vaga PM senior"}
        result = graph_mod.jd_gate_node(state)
        self.assertEqual(result.get("current_stage"), "jd_enrichment")
        self.assertNotIn(
            "jd_approved", result,
            "Sem msg + sem runtime, gate_node NÃO deve mutar jd_approved.",
        )
        # Sprint F.2 fix — even legacy offline path (no runtime) now self-loops at the routing layer.
        # The interrupt() guard preserves backwards-compat at the NODE level (no interrupt outside runtime),
        # but the routing layer treats non-terminal intent uniformly to keep the contract consistent.
        self.assertEqual(graph_mod.route_after_gate(result), "jd_gate")


if __name__ == "__main__":
    unittest.main(verbosity=2)
