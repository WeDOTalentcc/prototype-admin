"""
Integration tests — W2.4: P1-8 + P1-11 auth em /api/v1/teams/tab/events.

Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md):
- P1-8: backend endpoint /tab/events nao declara Depends(get_current_user).
  Atacante chama direto (sem o proxy) com aad_object_id forjado e dispara
  proactive Adaptive Card para outro user.
- P1-11: useTeamsTabTracker envia Authorization header mas backend ignora
  (falsa sensacao de seguranca). Resolvido junto ao adicionar Depends.

Fix W2.4: Depends(get_current_user) + valida que payload.platform_user_id
(se enviado) corresponde ao current_user.id.
"""
from __future__ import annotations
import inspect
import pytest


class TestTabEventsAuth:
    def test_endpoint_declares_get_current_user_dependency(self):
        """Endpoint /tab/events deve usar Depends(get_current_user)."""
        import app.api.v1.teams as mod
        src = inspect.getsource(mod.teams_tab_events)
        assert "get_current_user" in src or "current_user" in src, (
            "/tab/events deve declarar Depends(get_current_user) (P1-8)"
        )

    def test_endpoint_validates_platform_user_id_against_current_user(self):
        """
        Se payload.platform_user_id for fornecido, deve bater com current_user.id
        (impede atacante de forjar eventos para outro user mesmo autenticado).
        """
        import app.api.v1.teams as mod
        src = inspect.getsource(mod.teams_tab_events)
        # Procura comparacao explicita entre platform_user_id e current_user.id
        assert "current_user.id" in src, (
            "/tab/events deve validar payload.platform_user_id contra current_user.id "
            "(P1-8 hardening)"
        )
