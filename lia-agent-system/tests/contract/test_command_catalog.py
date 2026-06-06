"""Fase 2 contract — GET /lia/command-catalog deriva do capability_map (DRY).

Sensor: só capabilities COM label entram; campos batem com o capability_map;
ações user-facing presentes; ordenado por label.
"""
from __future__ import annotations

import pytest

from app.api.v1.lia_assistant.command_catalog import (
    build_command_catalog,
    get_command_catalog,
)
from app.shared.services.capability_map_service import CapabilityMapService


class TestCommandCatalog:
    def test_only_labeled_caps_included(self):
        intents = {c.intent for c in build_command_catalog()}
        for intent, cap in CapabilityMapService.load().items():
            if cap.label:
                assert intent in intents, f"cap com label '{intent}' faltando no catálogo"
            else:
                assert intent not in intents, f"cap sem label '{intent}' não deveria aparecer"

    def test_user_facing_actions_present(self):
        labels = {c.label for c in build_command_catalog()}
        for expected in [
            "Comparar candidatos",
            "Ver score do candidato",
            "Encerrar vaga",
            "Enviar comunicação",
        ]:
            assert expected in labels, f"ação '{expected}' ausente do catálogo"

    def test_fields_match_capability_map(self):
        for c in build_command_catalog():
            cap = CapabilityMapService.get(c.intent)
            assert cap is not None
            assert c.label == cap.label
            assert c.requires_confirmation == cap.requires_confirmation
            assert c.modal_id == cap.modal_id
            assert c.category == "action"

    def test_sorted_by_label(self):
        labels = [c.label for c in build_command_catalog()]
        assert labels == sorted(labels)

    @pytest.mark.asyncio
    async def test_endpoint_returns_catalog(self):
        resp = await get_command_catalog()
        assert len(resp.commands) >= 10
        assert all(c.label for c in resp.commands)
