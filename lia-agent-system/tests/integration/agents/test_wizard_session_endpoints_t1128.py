"""Task #1128 — sentinela arquitetural dos endpoints canônicos de wizard session.

Cenários:
  S1 — Router registra exatamente um GET e um DELETE em
       ``/job-wizard/session/{session_id}`` (não pode colidir com o
       tombstone POST do `wizard.py`).
  S2 — Ambos endpoints declaram `get_current_user_or_demo` como dependência
       de autenticação (nada exposto pública).
  S3 — `reset_wizard_session` é IDEMPOTENTE quando a sessão já está
       inativa — devolve `success=True, was_active=False` sem tentar
       escrever no checkpointer.
  S4 — `get_wizard_session_state` devolve `active=False` quando o
       checkpointer não tem snapshot — não levanta 404, retorna shape
       padrão para o frontend tratar como "sem wizard".
  S5 — Ambos endpoints usam `derive_thread_id(company_id, session_id)`
       canônico — NÃO podem aceitar `thread_id` do cliente (T-1080
       canonical-fix).

Por que isso existe: antes de Task #1128 o cliente reabilitava o wizard
via `localStorage["lia-wizard-state-*"]`. A regressão clássica é
alguém reintroduzir um endpoint que aceite `thread_id` do cliente ou
deixe o reset cair em silêncio quando o checkpointer falha — ambos
ressuscitam o bug do screenshot ("Nova conversa não cancela o wizard").
"""
from __future__ import annotations

import ast
import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

_REPO_BACKEND_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_BACKEND_ROOT))

MODULE_PATH = (
    _REPO_BACKEND_ROOT / "app/api/v1/lia_assistant/wizard_session.py"
)


class WizardSessionEndpointsT1128(unittest.TestCase):
    # ---------------- S1 ----------------
    def test_S1_router_has_get_and_delete_session_endpoints(self):
        from app.api.v1.lia_assistant.wizard_session import router

        method_paths: set[tuple[str, str]] = set()
        for r in router.routes:
            methods = getattr(r, "methods", set()) or set()
            path = getattr(r, "path", "")
            for m in methods:
                method_paths.add((m, path))
        self.assertIn(
            ("GET", "/job-wizard/session/{session_id}"),
            method_paths,
            f"GET /job-wizard/session/{{session_id}} ausente. Rotas: {method_paths}",
        )
        self.assertIn(
            ("DELETE", "/job-wizard/session/{session_id}"),
            method_paths,
            f"DELETE /job-wizard/session/{{session_id}} ausente. Rotas: {method_paths}",
        )

    # ---------------- S2 ----------------
    def test_S2_endpoints_require_authenticated_user(self):
        src = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src)
        target_funcs = {"get_wizard_session_state", "reset_wizard_session"}
        found: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name in target_funcs:
                signature_src = ast.unparse(node.args)
                self.assertIn(
                    "get_current_user_or_demo",
                    signature_src,
                    f"{node.name} deve depender de get_current_user_or_demo. "
                    f"Sig: {signature_src}",
                )
                found.add(node.name)
        self.assertEqual(found, target_funcs, f"Funções faltantes: {target_funcs - found}")

    # ---------------- S3 ----------------
    def test_S3_reset_is_idempotent_on_inactive_session(self):
        from app.api.v1.lia_assistant import wizard_session as ws_mod

        user = MagicMock()
        user.company_id = "00000000-0000-4000-a000-000000000001"

        # Forçamos is_wizard_session_active=False e garantimos que NENHUMA
        # escrita no checkpointer ocorre nesse path (idempotência).
        with (
            patch.object(
                ws_mod,
                "is_wizard_session_active",
                new=AsyncMock(return_value=False),
            ),
            patch(
                "app.domains.job_creation.graph.get_job_creation_graph"
            ) as mock_get_graph,
        ):
            mock_graph = MagicMock()
            mock_get_graph.return_value = mock_graph

            result = asyncio.run(
                ws_mod.reset_wizard_session(
                    session_id="sess-1128-s3",
                    current_user=user,
                )
            )

            self.assertTrue(result.success)
            self.assertFalse(result.was_active)
            self.assertEqual(result.session_id, "sess-1128-s3")
            # Nenhuma escrita: graph nem deve ser construído nesse branch.
            mock_get_graph.assert_not_called()

    # ---------------- S4 ----------------
    def test_S4_get_returns_inactive_shape_when_no_snapshot(self):
        from app.api.v1.lia_assistant import wizard_session as ws_mod

        user = MagicMock()
        user.company_id = "00000000-0000-4000-a000-000000000001"

        with (
            patch.object(
                ws_mod,
                "_read_state_snapshot",
                new=AsyncMock(return_value=None),
            ),
            patch.object(
                ws_mod,
                "is_wizard_session_active",
                new=AsyncMock(return_value=False),
            ),
        ):
            result = asyncio.run(
                ws_mod.get_wizard_session_state(
                    session_id="sess-1128-s4",
                    current_user=user,
                )
            )

        self.assertFalse(result.active)
        self.assertIsNone(result.current_stage)
        self.assertEqual(result.completeness, 0.0)
        self.assertEqual(result.conversation_message_count, 0)
        self.assertEqual(result.stage_data, {})
        # thread_id ainda é determinístico mesmo em sessão inativa
        # (frontend usa para correlação de logs).
        self.assertTrue(result.thread_id.startswith("wiz-"))
        self.assertTrue(result.thread_id.endswith("-sess-1128-s4"))

    # ---------------- S5 ----------------
    def test_S5_client_supplied_thread_id_is_not_honored(self):
        """Sentinela anti-regressão T-1080: o thread_id é função pura de
        ``(company_id, session_id)`` — endpoints NÃO podem aceitar
        `thread_id` do cliente (query/body/header) para evitar bypass de
        tenant isolation."""
        src = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name in {
                "get_wizard_session_state",
                "reset_wizard_session",
            }:
                arg_names = {a.arg for a in node.args.args}
                self.assertNotIn(
                    "thread_id",
                    arg_names,
                    f"{node.name}: parâmetro `thread_id` proibido — derive "
                    f"server-side via derive_thread_id(company_id, session_id).",
                )


if __name__ == "__main__":
    unittest.main()
