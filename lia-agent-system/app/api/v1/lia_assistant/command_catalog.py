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
    navigate_page: str | None = None


class CommandCatalogResponse(BaseModel):
    commands: list[CommandCatalogItem]


def build_command_catalog() -> list[CommandCatalogItem]:
    """Pure: deriva os comandos acionáveis (com label) do capability_map."""
    items: list[CommandCatalogItem] = []
    for intent, cap in CapabilityMapService.load().items():
        label = getattr(cap, "label", None)
        if not label:
            continue
        items.append(
            CommandCatalogItem(
                intent=intent,
                label=label,
                category="action",
                requires_confirmation=cap.requires_confirmation,
                modal_id=cap.modal_id,
                navigate_page=cap.navigate_page,
            )
        )
    items.sort(key=lambda c: c.label)
    return items


@router.get("/command-catalog", response_model=CommandCatalogResponse)
async def get_command_catalog() -> CommandCatalogResponse:
    return CommandCatalogResponse(commands=build_command_catalog())
