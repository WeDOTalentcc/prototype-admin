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


if __name__ == "__main__":
    unittest.main(verbosity=2)
