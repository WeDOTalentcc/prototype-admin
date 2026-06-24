"""GET /lia/command-catalog — catálogo de comandos acionáveis da LIA.

Fase 2 (2026-06-06): expõe as capabilities com `label` do capability_map.yaml
para o FE montar a categoria "Ações" do CommandPalette (Ctrl+/) + Cmd+K. DRY:
fonte única = capability_map. Dar um label a uma capability → ela aparece no
catálogo automaticamente (zero drift).

Não-sensível: rótulos estáticos, iguais para todo tenant — sem company scoping.
A navegação (páginas) NÃO entra aqui: ela é servida pelo catálogo do FE
(navigation-commands.ts, Fase 1) derivado de canonical-pages.ts.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.shared.services.capability_map_service import CapabilityMapService

router = APIRouter()


class CommandCatalogItem(BaseModel):
    intent: str
    label: str
    category: str = "action"
    requires_confirmation: bool = False
    modal_id: str | None = None
    destination_page: str | None = None  # H-6 fix: renamed from navigate_page (internal YAML key)
    ui_action: str | None = None  # H-6 fix: explicit FE action type (navigate_to | open_modal | None)


class CommandCatalogResponse(BaseModel):
    commands: list[CommandCatalogItem]


def build_command_catalog() -> list[CommandCatalogItem]:
    """Pure: deriva os comandos acionáveis (com label) do capability_map."""
    items: list[CommandCatalogItem] = []
    for intent, cap in CapabilityMapService.load().items():
        label = getattr(cap, "label", None)
        if not label:
            continue
        # H-6 fix: derive explicit ui_action for FE Command Palette
        if cap.navigate_page:
            _ui_action = "navigate_to"
        elif cap.modal_id:
            _ui_action = "open_modal"
        else:
            _ui_action = None
        items.append(
            CommandCatalogItem(
                intent=intent,
                label=label,
                category="action",
                requires_confirmation=cap.requires_confirmation,
                modal_id=cap.modal_id,
                destination_page=cap.navigate_page,  # H-6: renamed field
                ui_action=_ui_action,
            )
        )
    items.sort(key=lambda c: c.label)
    return items


@router.get("/command-catalog", response_model=CommandCatalogResponse)
async def get_command_catalog() -> CommandCatalogResponse:
    return CommandCatalogResponse(commands=build_command_catalog())
