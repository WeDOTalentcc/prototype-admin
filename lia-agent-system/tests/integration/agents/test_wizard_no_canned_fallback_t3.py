"""Task #1089 (T3) — sentinela arquitetural fail-loud do WizardSessionService.

Veta a reintrodução do dict ``_STAGE_DEFAULTS`` ou de strings canned
equivalentes em ``app/domains/job_creation/services/wizard_session_service.py``
e valida o path completo fail-loud (log error + audit row + tracker counter
+ mensagem hard-prefixada quando o LLM cheap está desabilitado).

Cenários:
  S1 — _STAGE_DEFAULTS NÃO existe como atributo do módulo.
  S2 — AST scan veta literais string canned ("preciso da sua aprovação",
       "Captei a vaga", "Vaga em criação", "Vaga criada com sucesso") em
       wizard_session_service.py.
  S3 — Fallback path emite log error + audit + Prometheus counter quando
       graph devolve resultado sem mensagem.
  S4 — _generate_fallback_reply com LIA_WIZARD_FALLBACK_LLM_DISABLED=1
       devolve mensagem hard-prefixada (não-confundível com produto).
"""
from __future__ import annotations

import ast
import asyncio
import importlib
import logging
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# sys.path bootstrap (espelha pattern dos sentinelas vizinhos T2/T6) para
# permitir execução standalone fora do pytest, sem PYTHONPATH manual.
_REPO_BACKEND_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_BACKEND_ROOT))

WSS_PATH = (
    Path(__file__).resolve().parents[3]
    / "app/domains/job_creation/services/wizard_session_service.py"
)

# Strings que NÃO podem reaparecer como literais isolados de fallback
# (foram o vetor original do bug do screenshot — repete 4× ignorando user).
_FORBIDDEN_CANNED_LITERALS = (
    "Descrição da vaga enriquecida — preciso da sua aprovação.",
    "Captei a vaga. Vou seguir para o próximo passo.",
    "Vaga em criação — vamos seguir.",
    "Vaga criada com sucesso.",
    "Perguntas de triagem WSI sugeridas — preciso da sua aprovação.",
)


class WizardNoCannedFallbackT3(unittest.TestCase):
    # ---------------- S1 ----------------
    def test_S1_stage_defaults_attribute_removed(self):
        wss = importlib.import_module(
            "app.domains.job_creation.services.wizard_session_service"
        )
        self.assertFalse(
            hasattr(wss, "_STAGE_DEFAULTS"),
            "_STAGE_DEFAULTS deve permanecer REMOVIDO (Task #1089).",
        )

    # ---------------- S2 ----------------
    def test_S2_ast_scan_forbids_canned_string_literals(self):
        src = WSS_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src)
        offenders: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                value = node.value
                for canned in _FORBIDDEN_CANNED_LITERALS:
                    if canned in value:
                        offenders.append(
                            f"line {getattr(node, 'lineno', '?')}: {canned!r}"
                        )
        self.assertEqual(
            offenders, [],
            "Strings canned proibidas reapareceram em wizard_session_service.py "
            f"(Task #1089 / canonical-fix Caso #3-#4): {offenders}",
        )

    # ---------------- S2b ----------------
    def test_S2b_ast_scan_forbids_stage_defaults_dict_redefinition(self):
        """Veta a reintrodução do dict ``_STAGE_DEFAULTS`` por nome."""
        src = WSS_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == "_STAGE_DEFAULTS":
                        self.fail(
                            f"_STAGE_DEFAULTS reatribuído na linha "
                            f"{getattr(node, 'lineno', '?')} — Task #1089 "
                            f"baniu este dict (use _generate_fallback_reply)."
                        )
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.target.id == "_STAGE_DEFAULTS":
                    self.fail(
                        f"_STAGE_DEFAULTS reanotado na linha "
                        f"{getattr(node, 'lineno', '?')} — Task #1089."
                    )

    # ---------------- S3 ----------------
    def test_S3_emit_silent_fallback_writes_log_audit_and_tracker(self):
        wss = importlib.import_module(
            "app.domains.job_creation.services.wizard_session_service"
        )
        from app.shared.observability.wizard_fallback_tracker import (
            get_wizard_fallback_tracker,
        )
        tracker = get_wizard_fallback_tracker()
        tracker.reset()

        with self.assertLogs(wss.__name__, level=logging.ERROR) as cap, \
                patch.object(
                    wss, "asyncio", wraps=wss.asyncio
                ) as asyncio_mock:
            # Stub asyncio.create_task → captura chamada (audit) sem disparar
            # event loop em contexto sync de teste.
            captured: list[object] = []

            def _stub_create_task(coro):
                captured.append(coro)
                # close() para evitar RuntimeWarning de coro não-awaited.
                try:
                    coro.close()
                except Exception:
                    pass
                return None

            asyncio_mock.create_task = _stub_create_task
            wss._emit_silent_fallback(
                stage="jd_enrichment",
                company_id="00000000-0000-4000-a000-000000000001",
                session_id="sess-x",
                thread_id="wiz-abc12345-sess-x",
                conversation_tail=[{"role": "user", "content": "manda bala"}],
                cause="empty_message",
            )

        # (a) log error com contexto
        msg_blob = "\n".join(cap.output)
        self.assertIn("silent fallback invoked", msg_blob)
        self.assertIn("stage=jd_enrichment", msg_blob)
        self.assertIn("cause=empty_message", msg_blob)

        # (c) audit foi agendado via asyncio.create_task
        self.assertEqual(len(captured), 1, "audit row deve ser emitido 1×")

        # (d) tracker registrou o evento (counter Prometheus interno)
        state = tracker.get_state(
            session_id="sess-x",
            company_id="00000000-0000-4000-a000-000000000001",
        )
        # Threshold por sessão é 3 → state pode ser None com 1 evento; mas a
        # janela interna deve ter o evento gravado:
        with tracker._lock:  # type: ignore[attr-defined]
            sess_window = tracker._sessions.get("sess-x")
        self.assertIsNotNone(sess_window, "tracker deve ter registrado evento")
        self.assertEqual(len(sess_window.events), 1)
        self.assertEqual(sess_window.events[0].reason, "silent_empty_message")
        tracker.reset()

    # ---------------- S3b ----------------
    def test_S3b_prometheus_counter_increments(self):
        """Counter explícito ``lia_wizard_silent_fallback_total`` deve subir
        a cada chamada a ``_emit_silent_fallback`` (Task #1089 follow-up #2).
        """
        wss = importlib.import_module(
            "app.domains.job_creation.services.wizard_session_service"
        )
        if wss._SILENT_FALLBACK_COUNTER is None:
            self.skipTest("prometheus_client não disponível neste ambiente")
        labels = {
            "stage": "jd_enrichment",
            "company_id": "00000000-0000-4000-a000-000000000001",
            "cause": "empty_message",
        }
        before = wss._SILENT_FALLBACK_COUNTER.labels(**labels)._value.get()
        with patch.object(wss.asyncio, "create_task", lambda *a, **k: None):
            wss._emit_silent_fallback(
                stage="jd_enrichment",
                company_id="00000000-0000-4000-a000-000000000001",
                session_id="sess-counter",
                thread_id="wiz-cccc1111-sess-counter",
                conversation_tail=None,
                cause="empty_message",
            )
        after = wss._SILENT_FALLBACK_COUNTER.labels(**labels)._value.get()
        self.assertEqual(after - before, 1.0)

    # ---------------- S4 ----------------
    def test_S4_generate_fallback_reply_returns_hard_prefixed_when_llm_disabled(self):
        wss = importlib.import_module(
            "app.domains.job_creation.services.wizard_session_service"
        )
        os.environ["LIA_WIZARD_FALLBACK_LLM_DISABLED"] = "1"
        try:
            reply = asyncio.run(wss._generate_fallback_reply(
                stage="jd_enrichment",
                conversation_tail=[{"role": "user", "content": "tá liberado"}],
                tenant_snippet="Demo Company — setor: tecnologia",
            ))
        finally:
            del os.environ["LIA_WIZARD_FALLBACK_LLM_DISABLED"]
        self.assertIn(wss._FALLBACK_HARD_PREFIX, reply)
        self.assertIn("jd_enrichment", reply)
        # NUNCA igual aos canned proibidos.
        for canned in _FORBIDDEN_CANNED_LITERALS:
            self.assertNotIn(canned, reply)


class WizardProcessMessageFailLoudT3(unittest.IsolatedAsyncioTestCase):
    """End-to-end (architect follow-up #1 + #3) — exercita
    ``WizardSessionService.process_message`` para confirmar que ambos os
    paths fail-loud (invoke_exception + empty stage_data) emitem
    log error + Prometheus counter + audit + retornam fallback contextual
    em vez de propagar exceção ou devolver canned."""

    async def asyncSetUp(self):
        os.environ["LIA_WIZARD_FALLBACK_LLM_DISABLED"] = "1"
        self._wss = importlib.import_module(
            "app.domains.job_creation.services.wizard_session_service"
        )
        # tracker reset entre cenários
        from app.shared.observability.wizard_fallback_tracker import (
            get_wizard_fallback_tracker,
        )
        get_wizard_fallback_tracker().reset()

    async def asyncTearDown(self):
        del os.environ["LIA_WIZARD_FALLBACK_LLM_DISABLED"]

    def _counter_value(self, *, stage, cause):
        if self._wss._SILENT_FALLBACK_COUNTER is None:
            return None
        return self._wss._SILENT_FALLBACK_COUNTER.labels(
            stage=stage,
            company_id="00000000-0000-4000-a000-000000000001",
            cause=cause,
        )._value.get()

    async def _run(self, *, fake_graph, expected_cause_substr):
        wss = self._wss
        cls = wss.WizardSessionService

        # Stubs para evitar DB/checkpointer reais.
        async def _no_prior_state(_thread_id):
            return None

        captured_audit_calls: list[object] = []

        def _capture_create_task(coro):
            captured_audit_calls.append(coro)
            try:
                coro.close()
            except Exception:
                pass
            return None

        # ``get_job_creation_graph`` é importado lazy dentro de
        # ``process_message`` — patchar no módulo de origem.
        graph_mod = importlib.import_module("app.domains.job_creation.graph")
        with patch.object(cls, "_get_prior_state", new=_no_prior_state), \
                patch.object(
                    graph_mod, "get_job_creation_graph", lambda: fake_graph,
                ), \
                patch.object(wss.asyncio, "create_task", _capture_create_task), \
                self.assertLogs(wss.__name__, level=logging.ERROR) as cap:
            msg, payload, tokens = await cls.process_message(
                thread_id="wiz-deadbeef-sess-e2e",
                user_message="manda bala",
                user_id="user-x",
                company_id="00000000-0000-4000-a000-000000000001",
                session_id="sess-e2e",
                context=None,
            )

        log_blob = "\n".join(cap.output)
        self.assertIn("silent fallback invoked", log_blob)
        self.assertIn(expected_cause_substr, log_blob)
        # Audit row foi agendado
        self.assertGreaterEqual(len(captured_audit_calls), 1)
        # Hard prefix retornado (LLM disabled)
        self.assertIn(wss._FALLBACK_HARD_PREFIX, msg)
        # Não validamos payload exato — invoke_exception devolve {}, empty
        # message path devolve o ws_stage_payload do graph result.
        self.assertIsInstance(payload, dict)
        return tokens

    # ---------------- S5 ----------------
    async def test_S5_process_message_handles_invoke_exception_fail_loud(self):
        """Architect follow-up #1: graph.stream_invoke raise → fail-loud,
        NÃO propaga, devolve mensagem hard-prefixada."""
        before = self._counter_value(stage="unknown", cause="invoke_exception:RuntimeError")

        class _RaisingGraph:
            async def stream_invoke(self, state, thread_id, on_token=None):
                raise RuntimeError("boom from graph")

        await self._run(
            fake_graph=_RaisingGraph(),
            expected_cause_substr="invoke_exception:RuntimeError",
        )
        after = self._counter_value(stage="unknown", cause="invoke_exception:RuntimeError")
        if before is not None and after is not None:
            self.assertEqual(after - before, 1.0)

    # ---------------- S6 ----------------
    async def test_S6_process_message_handles_empty_message_fail_loud(self):
        """Architect follow-up #3: graph devolve dict sem message nem
        gate_clarify_message → fail-loud + LLM/hard-prefix em vez de canned."""
        before = self._counter_value(stage="jd_enrichment", cause="empty_message")

        class _EmptyGraph:
            async def stream_invoke(self, state, thread_id, on_token=None):
                return (
                    {
                        "current_stage": "jd_enrichment",
                        "ws_stage_payload": {"data": {}},
                        # nenhum gate_clarify_message, nenhum message,
                        # nenhum response_text → vai cair no fail-loud.
                    },
                    0,
                )

        await self._run(
            fake_graph=_EmptyGraph(),
            expected_cause_substr="cause=empty_message",
        )
        after = self._counter_value(stage="jd_enrichment", cause="empty_message")
        if before is not None and after is not None:
            self.assertEqual(after - before, 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
