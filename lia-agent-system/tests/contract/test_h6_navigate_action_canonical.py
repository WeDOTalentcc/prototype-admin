"""
H-6 RED sensor -- navigate_page vs navigate_to contract mismatch.

Bug (H-6):
  backend produtores usam "navigate_page" como nome de campo YAML (cap.navigate_page)
  e inadvertidamente esse valor vaza para o campo ui_action no command_catalog.py.
  O FE GLOBAL_UI_ACTION_TYPES e useUIAction.ts so conhecem "navigate_to" (nao
  "navigate_page"). Resultado: qualquer diretiva emitida com ui_action="navigate_page"
  e silenciosamente descartada pelo _ACTIONABLE_TOOL_UI_ACTIONS allowlist e pelo FE.

Estado RED esperado (antes do fix):
  - Invariante 1: PASSA -- allowlists ja estao corretas (navigate_page nao esta la)
  - Invariante 2: FALHA -- CommandCatalogItem tem campo navigate_page (ambiguo/perigoso)
  - Invariante 3: PASSA -- rail_a ja usa _UI_ACTION_NAVIGATE = "navigate_to"
  - Invariante 4: PASSA -- ui_tool_registry ja emite navigate_to
  - Invariante 5: FALHA -- serializer aceita navigate_page sem normalizar -> navigate_to
  - Invariante 6: FALHA -- CommandCatalogItem nao tem campo ui_action explicito

Skill: lia-testing TDD PARTE 1 (RED state).
Harness: sensor computacional (sem LLM, puro import/schema check).
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


# ---------------------------------------------------------------------------
# Invariante 1 -- "navigate_page" NAO pertence a nenhum allowlist BE
# ---------------------------------------------------------------------------

class TestNavigatePageNotInAllowlists:
    """navigate_page e um campo YAML interno, NAO um tipo de ui_action FE.
    Os allowlists BE DEVEM conter apenas tipos que o FE conhece (navigate_to).
    """

    def test_navigate_page_not_in_actionable_tool_ui_actions(self):
        """_ACTIONABLE_TOOL_UI_ACTIONS nao deve conter navigate_page."""
        from app.orchestrator.execution.agentic_loop import (
            _ACTIONABLE_TOOL_UI_ACTIONS,
        )
        assert "navigate_page" not in _ACTIONABLE_TOOL_UI_ACTIONS, (
            "BLOCKER H-6: navigate_page esta em _ACTIONABLE_TOOL_UI_ACTIONS. "
            "Agentes podem emitir essa string como ui_action e ela chegaria ao FE "
            "mas o FE nao tem handler para ela (so tem navigate_to). "
            "Remover navigate_page do allowlist; tipo correto e navigate_to."
        )

    def test_navigate_page_not_in_fe_tool_ui_actions(self):
        """_FE_TOOL_UI_ACTIONS nao deve conter navigate_page."""
        from app.orchestrator.execution.main_orchestrator import (
            _FE_TOOL_UI_ACTIONS,
        )
        assert "navigate_page" not in _FE_TOOL_UI_ACTIONS, (
            "BLOCKER H-6: navigate_page esta em _FE_TOOL_UI_ACTIONS. "
            "Supervisor path emitiria para o FE mas FE nao tem case para ela. "
            "Tipo correto: navigate_to."
        )

    def test_navigate_page_not_in_fallback_actionable(self):
        """_FALLBACK_ACTIONABLE nao deve conter navigate_page."""
        from app.shared.ui_action_sink import _FALLBACK_ACTIONABLE
        assert "navigate_page" not in _FALLBACK_ACTIONABLE, (
            "BLOCKER H-6: navigate_page esta em _FALLBACK_ACTIONABLE. "
            "Tipo correto: navigate_to."
        )

    def test_navigate_page_not_in_ws_message_schemas(self):
        """GLOBAL_UI_ACTION_TYPES (BE mirror do FE) nao deve conter navigate_page."""
        from app.shared.websocket.ws_message_schemas import GLOBAL_UI_ACTION_TYPES
        assert "navigate_page" not in GLOBAL_UI_ACTION_TYPES, (
            "BLOCKER H-6: navigate_page esta em GLOBAL_UI_ACTION_TYPES. "
            "Esse schema e o mirror BE do FE -- ambos devem ter navigate_to, nao navigate_page. "
            "Fix: remover navigate_page de GLOBAL_UI_ACTION_TYPES."
        )

    def test_navigate_to_IS_in_all_allowlists(self):
        """navigate_to DEVE estar em todos os allowlists (invariante positiva)."""
        from app.orchestrator.execution.agentic_loop import (
            _ACTIONABLE_TOOL_UI_ACTIONS,
        )
        from app.orchestrator.execution.main_orchestrator import (
            _FE_TOOL_UI_ACTIONS,
        )
        from app.shared.ui_action_sink import _FALLBACK_ACTIONABLE
        from app.shared.websocket.ws_message_schemas import GLOBAL_UI_ACTION_TYPES

        assert "navigate_to" in _ACTIONABLE_TOOL_UI_ACTIONS, (
            "navigate_to deve estar em _ACTIONABLE_TOOL_UI_ACTIONS"
        )
        assert "navigate_to" in _FE_TOOL_UI_ACTIONS, (
            "navigate_to deve estar em _FE_TOOL_UI_ACTIONS"
        )
        assert "navigate_to" in _FALLBACK_ACTIONABLE, (
            "navigate_to deve estar em _FALLBACK_ACTIONABLE"
        )
        assert "navigate_to" in GLOBAL_UI_ACTION_TYPES, (
            "navigate_to deve estar em GLOBAL_UI_ACTION_TYPES"
        )


# ---------------------------------------------------------------------------
# Invariante 2 -- CommandCatalogItem nao expoe campo ambiguo "navigate_page"
# ---------------------------------------------------------------------------

class TestCommandCatalogDoesNotExposeNavigatePage:
    """O campo navigate_page em CommandCatalogItem e o valor YAML interno
    (alias de pagina como 'vagas', 'dashboard') -- nao e um tipo ui_action.
    Expor esse campo com o mesmo nome cria confusao e risco de o FE usar
    'navigate_page' como ui_action string.

    Fix esperado: renomear para 'destination_page' ou adicionar campo
    'ui_action' explicito derivado da capability.
    """

    def test_command_catalog_item_navigate_page_field_is_renamed_or_removed(self):
        """CommandCatalogItem NAO deve ter campo chamado 'navigate_page'.

        O nome 'navigate_page' colide com o padrao de ui_action strings e
        cria confusao. O campo deve ser renomeado para 'destination_page'
        ou o catalogo deve expor explicitamente qual ui_action usar.

        RED: este teste FALHA porque CommandCatalogItem tem campo navigate_page.
        """
        from app.api.v1.lia_assistant.command_catalog import CommandCatalogItem

        schema = CommandCatalogItem.model_json_schema()
        field_names = set(schema.get("properties", {}).keys())

        assert "navigate_page" not in field_names, (
            "H-6 BUG: CommandCatalogItem expoe campo 'navigate_page' -- nome colide "
            "com padrao ui_action (FE so conhece 'navigate_to'). "
            "FIX: renomear para 'destination_page' ou adicionar campo "
            "'ui_action': 'navigate_to' para o FE saber o tipo correto. "
            f"Campos atuais: {sorted(field_names)}"
        )

    def test_command_catalog_item_has_explicit_ui_action_field(self):
        """CommandCatalogItem DEVE ter campo 'ui_action' para o FE saber
        qual acao disparar para capabilities de navegacao.

        RED: este teste FALHA porque CommandCatalogItem nao tem campo ui_action.
        """
        from app.api.v1.lia_assistant.command_catalog import CommandCatalogItem

        schema = CommandCatalogItem.model_json_schema()
        field_names = set(schema.get("properties", {}).keys())

        assert "ui_action" in field_names, (
            "H-6 FIX PENDENTE: CommandCatalogItem nao tem campo 'ui_action'. "
            "Sem esse campo, o FE Command Palette nao sabe qual acao disparar "
            "para capabilities de navegacao. "
            "FIX: adicionar ui_action: str derivado do capability_map "
            "('navigate_to' para caps com navigate_page, 'open_modal' para caps com modal_id)."
        )


# ---------------------------------------------------------------------------
# Invariante 3 -- rail_a emite navigate_to (nao navigate_page) como ui_action
# ---------------------------------------------------------------------------

class TestRailAEmitsNavigateTo:
    """rail_a_capability_check.py DEVE emitir ui_action='navigate_to'
    para capabilities com chat_executable=False e navigate_page definido.
    Fixado como sensor de nao-regressao (ja funciona, mas deve continuar).
    """

    @pytest.mark.asyncio
    async def test_rail_a_navigate_page_cap_emits_navigate_to(self):
        """Capability com navigate_page -> ui_action deve ser 'navigate_to'."""
        cap = SimpleNamespace(
            chat_executable=False,
            modal_id=None,
            navigate_page="vagas",
            navigate_fallback=None,
            navigate_query=None,
            entity_required=[],
        )
        with patch(
            "app.shared.services.capability_map_service.CapabilityMapService.get",
            return_value=cap,
        ):
            from app.orchestrator.guards.rail_a_capability_check import (
                check_rail_a_capability,
            )
            result = await check_rail_a_capability(
                context={"metadata": {"intent_hint": "ir_para_vagas", "source": "rail_a"}},
                message="ir para vagas",
                company_id="test-company",
                db=AsyncMock(),
            )

        assert result is not None, "Rail A deve retornar payload para navigate_page cap"
        actual_action = result.get("ui_action")
        assert actual_action == "navigate_to", (
            f"H-6 sensor: rail_a deve emitir ui_action='navigate_to', "
            f"recebeu: '{actual_action}'. "
            f"ui_action='navigate_page' nao e reconhecido pelo FE."
        )
        assert actual_action != "navigate_page", (
            "H-6 BLOCKER: rail_a emite ui_action='navigate_page' -- "
            "FE ira silenciosamente descartar essa diretiva."
        )

    @pytest.mark.asyncio
    async def test_rail_a_navigate_fallback_cap_emits_navigate_to(self):
        """Capability com navigate_fallback -> ui_action deve ser 'navigate_to'."""
        cap = SimpleNamespace(
            chat_executable=False,
            modal_id=None,
            navigate_page=None,
            navigate_fallback="/jobs",
            navigate_query=None,
            entity_required=[],
        )
        with patch(
            "app.shared.services.capability_map_service.CapabilityMapService.get",
            return_value=cap,
        ):
            from app.orchestrator.guards.rail_a_capability_check import (
                check_rail_a_capability,
            )
            result = await check_rail_a_capability(
                context={"metadata": {"intent_hint": "ir_fallback", "source": "rail_a"}},
                message="ir para o fallback",
                company_id="test-company",
                db=AsyncMock(),
            )

        assert result is not None
        actual_action = result.get("ui_action")
        assert actual_action == "navigate_to", (
            f"Rail A navigate_fallback path deve emitir 'navigate_to', "
            f"recebeu: '{actual_action}'"
        )


# ---------------------------------------------------------------------------
# Invariante 4 -- ui_tool_registry emite navigate_to (nao navigate_page)
# ---------------------------------------------------------------------------

class TestUiToolRegistryEmitsNavigateTo:
    """ui_tool_registry._wrap_open_ui DEVE emitir ui_action='navigate_to'
    para capabilities sem modal_id mas com navigate_page.
    Fixado como sensor de nao-regressao.
    """

    @pytest.mark.asyncio
    async def test_open_ui_navigate_page_cap_emits_navigate_to(self):
        """open_ui com cap sem modal mas com navigate_page -> navigate_to."""
        cap = SimpleNamespace(
            modal_id=None,
            navigate_page="vagas",
            settings_section=None,
            navigate_query=None,
            required_role=None,
            entity_required=[],
            navigate_fallback=None,
            requires_confirmation=False,
        )
        with patch(
            "app.shared.services.capability_map_service.CapabilityMapService.get",
            return_value=cap,
        ):
            with patch(
                "app.domains.recruiter_assistant.agents.ui_tool_registry._ui_capabilities",
                return_value={"ir_para_vagas": cap},
            ):
                from app.domains.recruiter_assistant.agents.ui_tool_registry import (
                    _wrap_open_ui,
                )
                result = await _wrap_open_ui(
                    capability="ir_para_vagas",
                    entity_ids={},
                    company_id="company-test",
                )

        assert result.get("success") is True, f"Resultado inesperado: {result}"
        data = result.get("data", {})
        actual_action = data.get("ui_action")
        assert actual_action == "navigate_to", (
            f"H-6 sensor: ui_tool_registry deve emitir ui_action='navigate_to', "
            f"recebeu: '{actual_action}'. "
            f"ui_action='navigate_page' nao e reconhecido pelo FE."
        )
        assert actual_action != "navigate_page", (
            "H-6 BLOCKER: ui_tool_registry emite ui_action='navigate_page' -- "
            "FE ira silenciosamente descartar essa diretiva."
        )


# ---------------------------------------------------------------------------
# Invariante 5 -- serializer nao deve aceitar navigate_page sem normalizar
# ---------------------------------------------------------------------------

class TestNavigationSerializerContractIsIncorrect:
    """test_navigation_serializer.py tem testes que fixam navigate_page como
    ui_action valido -- mas o FE nao reconhece navigate_page.

    O serialize_message aceita qualquer string em ui_action -- mas o FE
    useUIAction.ts so rota tipos em GLOBAL_UI_ACTION_TYPES. Qualquer
    ui_action='navigate_page' chegaria ao FE e seria tratado como
    'lia:unhandled_ui_action' (re-emitido como custom event sem handler).

    RED: este teste FALHA porque o serializer aceita navigate_page sem normalizar.
    """

    def test_navigate_page_string_not_valid_fe_action(self):
        """'navigate_page' como string nao e um tipo FE valido."""
        FE_CANONICAL = frozenset({
            "navigate_to",
            "open_modal",
            "close_modal",
            "open_offer_review",
            "wizard_step",
            "open_panel",
            "close_panel",
            "scroll_to",
            "settings_open_tab",
            "open_communication_modal",
            "open_schedule_modal",
            "open_screening_modal",
            "apply_table_state",
            "select_rows",
            "bulk_execute",
            "start_wizard_seeded",
        })
        assert "navigate_page" not in FE_CANONICAL, (
            "Inesperado: 'navigate_page' esta no FE_CANONICAL -- "
            "verificar se o FE foi atualizado e este teste precisa ser revisado."
        )

    def test_serializer_rejects_or_normalizes_navigate_page(self):
        """serialize_message DEVE normalizar ou rejeitar navigate_page -> navigate_to.

        RED: FALHA porque o serializer aceita navigate_page e retorna navigate_page
        (sem normalizar). O FE descarta qualquer ui_action desconhecido silenciosamente.
        """
        from app.shared.chat_event_serializer import serialize_message

        result = serialize_message(
            "Navegando.",
            ui_action="navigate_page",
            ui_action_params={"page": "vagas"},
        )

        # O serializer ACEITA navigate_page (mostrando o bug):
        # Se este assert falhar, o serializer ja normalizou (fix aplicado).
        current_value = result.get("ui_action")

        # O que DEVERIA acontecer (RED -- este assert FALHA):
        assert current_value == "navigate_to", (
            f"H-6 FIX PENDENTE: serialize_message retornou ui_action='{current_value}' "
            "para input 'navigate_page' sem normalizar para 'navigate_to'. "
            "O FE nao tem handler para 'navigate_page' e vai descartar silenciosamente. "
            "FIX OPCAO A: serializer normaliza navigate_page -> navigate_to automaticamente. "
            "FIX OPCAO B: serializer rejeita tipos invalidos (raise ValueError). "
            "FIX OPCAO C: produtores upstream nunca emitem navigate_page como ui_action "
            "(command_catalog usa campo ui_action='navigate_to' explicitamente)."
        )


# ---------------------------------------------------------------------------
# Invariante 6 -- capability_map.yaml navigate_page -> ui_action navigate_to
#                 no command-catalog (campo explicito)
# ---------------------------------------------------------------------------

class TestCommandCatalogNavigatePageCapabilities:
    """Capabilities com navigate_page no YAML devem resultar em
    ui_action='navigate_to' (nao 'navigate_page') quando o FE as acionar.

    build_command_catalog() deve produzir items onde o campo de acao
    explicito e 'navigate_to', nao 'navigate_page'.

    RED: FALHA porque CommandCatalogItem nao tem campo ui_action.
    """

    def test_catalog_items_with_navigate_page_have_navigate_to_ui_action(self):
        """Items do catalogo com destino de pagina devem ter ui_action='navigate_to'."""
        from app.api.v1.lia_assistant.command_catalog import build_command_catalog

        items = build_command_catalog()
        navigate_items = [
            i for i in items
            if getattr(i, "navigate_page", None) is not None
        ]

        if not navigate_items:
            # Se navigate_page foi removido do schema (fix aplicado), ok -- mas
            # neste caso ui_action deve existir como campo
            all_items = items
            for item in all_items:
                assert hasattr(item, "ui_action"), (
                    f"H-6: CommandCatalogItem para '{item.intent}' nao tem campo "
                    f"'ui_action'. O FE Command Palette nao sabe qual acao disparar. "
                    f"FIX: adicionar campo ui_action derivado da capability."
                )
            return

        for item in navigate_items:
            # RED: falha aqui porque item nao tem campo ui_action
            assert hasattr(item, "ui_action"), (
                f"H-6 FIX PENDENTE: CommandCatalogItem para intent='{item.intent}' "
                f"tem navigate_page='{item.navigate_page}' mas nao tem campo 'ui_action'. "
                f"O FE nao sabe qual acao disparar. "
                f"FIX: adicionar ui_action='navigate_to' ao item do catalogo."
            )
            if hasattr(item, "ui_action"):
                assert item.ui_action == "navigate_to", (
                    f"H-6 BLOCKER: CommandCatalogItem para '{item.intent}' tem "
                    f"ui_action='{item.ui_action}' -- deve ser 'navigate_to'. "
                    f"O FE nao reconhece '{item.ui_action}'."
                )
