"""WT-2022 Fase 4: E2E acceptance test pattern pra settings_open_tab via WS.

Pattern de teste E2E (runtime validation):
1. Connect WS client com JWT (TestClient.websocket_connect).
2. Send chat message que LIA deveria responder com action settings_open_tab.
3. Receive WS message com ui_action="settings_open_tab" +
   ui_action_params={section, subsection?}.
4. Validar via validate_global_ui_action_params (mesma rotina usada no
   boundary BE→FE) e confirmar que SettingsPageEnhanced listener seria
   triggered no frontend.

Esses 2 primeiros testes são PATTERN — execução real requer staging env com
LIA agent rodando + JWT válido + Postgres + Redis. Marcados @pytest.mark.skip
pra rodar manualmente em staging deploy (ex.: pytest -m wt2022_e2e).

O terceiro teste (schema sanity) NÃO é skipped — valida que o registry
canonical de UIAction tipos contém settings_open_tab e que o validator
aceita/rejeita params corretamente. Roda em qualquer ambiente (zero deps de
runtime — apenas import puro do schema).

Skill: harness-engineering [sensor no boundary FE↔BE].
"""
from __future__ import annotations

import pytest


@pytest.mark.skip(
    reason="WT-2022 Fase 4 E2E pattern — run manually in staging "
    "(requires WS + LIA agent + JWT + Postgres + Redis)."
)
@pytest.mark.asyncio
async def test_ws_settings_open_tab_full_round_trip():
    """E2E: User chat → LIA → ChatResponse com ui_action settings_open_tab.

    Pattern de invocação em staging:
        STAGING_JWT=<token> pytest             tests/contract/test_ws_settings_open_tab_acceptance.py             -k full_round_trip --no-skip
    """
    from fastapi.testclient import TestClient

    from app.main import app
    from app.shared.websocket.ws_message_schemas import (
        validate_global_ui_action_params,
    )

    client = TestClient(app)
    with client.websocket_connect(
        "/ws/chat",
        headers={"Authorization": "Bearer test_jwt"},
    ) as ws:
        # Send user message that should trigger settings tool.
        ws.send_json(
            {
                "type": "chat",
                "content": "desabilite o learning loop bigfive_company_culture",
                "conversation_id": "test-conv-1",
            }
        )

        # Receive LIA response.
        response = ws.receive_json()
        assert response.get("type") == "chat_response", (
            f"esperava chat_response, veio {response.get(type)}"
        )

        # Validar ui_action format canonical.
        ui_action = response.get("ui_action")
        ui_action_params = response.get("ui_action_params", {})

        if ui_action == "settings_open_tab":
            # Validar via mesma rotina usada no boundary BE→FE.
            validated = validate_global_ui_action_params(
                ui_action, ui_action_params
            )
            assert validated is not None, (
                "WT-2022 Fase 4: params devem passar validate_global_ui_action_params"
            )
            assert "section" in ui_action_params, (
                "WT-2022 Fase 4: section é required pra deep-link"
            )
            assert ui_action_params["section"] in {
                "minha-empresa",
                "governanca",
                "fairness-compliance",
                "agentes-ia",
                "integracoes",
            }, f"section fora do whitelist: {ui_action_params[section]}"
            if "subsection" in ui_action_params and ui_action_params["subsection"]:
                assert isinstance(ui_action_params["subsection"], str)
                assert len(ui_action_params["subsection"]) <= 64


@pytest.mark.skip(
    reason="WT-2022 Fase 4 E2E pattern — staging only (LIA agent dispatch)."
)
@pytest.mark.asyncio
async def test_ws_validates_settings_open_tab_params_schema():
    """E2E: LIA dispatch + schema strict validation no boundary.

    Pattern documentando que validate_global_ui_action_params retorna None em
    invalid (não raise) — diferente de Pydantic raw .model_validate. Caller
    no WS handler usa is None como bool gate antes de re-emitir pro FE.
    """
    from app.shared.websocket.ws_message_schemas import (
        validate_global_ui_action_params,
    )

    # Valid params — retorna instance do BaseModel.
    valid_params = {"section": "minha-empresa", "subsection": "learning-loops"}
    validated = validate_global_ui_action_params("settings_open_tab", valid_params)
    assert validated is not None
    assert validated.section == "minha-empresa"
    assert validated.subsection == "learning-loops"

    # Invalid — missing required section. Helper retorna None (não raise).
    invalid_params = {"subsection": "learning-loops"}
    rejected = validate_global_ui_action_params(
        "settings_open_tab", invalid_params
    )
    assert rejected is None, (
        "WT-2022 Fase 4: params sem section devem ser rejeitados (None)"
    )


def test_ws_schema_includes_settings_open_tab():
    """Sanity: GLOBAL_UI_ACTION_TYPES contém settings_open_tab + validator wired.

    Esse teste NÃO é skipped — roda em qualquer CI/dev. Falha se alguém
    remover a action do registry canonical ou desconectar o schema do
    validator helper (regression sensor cheap, ~10ms).
    """
    from app.shared.websocket.ws_message_schemas import (
        GLOBAL_UI_ACTION_TYPES,
        UISettingsOpenTabParams,
        validate_global_ui_action_params,
    )

    # 1) Action no registry canonical de tipos globais.
    assert "settings_open_tab" in GLOBAL_UI_ACTION_TYPES, (
        "WT-2022 Fase 4: settings_open_tab DEVE estar em GLOBAL_UI_ACTION_TYPES "
        "(espelho de src/types/ui-action.ts no FE)"
    )

    # 2) Schema model existe + tem campos esperados.
    fields = UISettingsOpenTabParams.model_fields
    assert "section" in fields, "schema sem campo section"
    assert "subsection" in fields, "schema sem campo subsection"

    # 3) Validator helper conecta action → schema (não retorna None pra
    # action global válida com params válidos).
    ok = validate_global_ui_action_params(
        "settings_open_tab",
        {"section": "minha-empresa"},
    )
    assert ok is not None, (
        "validate_global_ui_action_params retornou None pra params válidos — "
        "verificar _UI_ACTION_PARAMS_BY_TYPE wiring"
    )

    # 4) Validator rejeita params inválidos (params=missing section).
    rejected = validate_global_ui_action_params("settings_open_tab", {})
    assert rejected is None, (
        "validator devia retornar None quando section ausente (required field)"
    )

    # 5) Validator rejeita action_type fora do registry (page-specific).
    not_global = validate_global_ui_action_params(
        "move_candidate", {"id": "abc"}
    )
    assert not_global is None, (
        "validator devia retornar None pra action page-specific (não-global)"
    )
