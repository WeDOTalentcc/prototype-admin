import React from "react"
import { Compass, Sparkles } from "lucide-react"
import {
  CANONICAL_PAGES,
  canonicalPageToUrl,
  canonicalPageLabel,
  type CanonicalPageValue,
} from "@/lib/canonical-pages"
import type { CommandItem } from "@/components/ui/command-palette"

/**
 * Fase 1 catálogo de navegação (2026-06-06): a lista de comandos de navegação
 * da LIA DERIVA da fonte ÚNICA `canonical-pages.ts` (lockstep-sincronizada com
 * o backend `canonical_pages.py` pelo sensor check_canonical_pages_sync.py).
 *
 * Toda página navegável (canonicalPageToUrl != null; exclui detalhes que
 * precisam de id e o sentinel general) vira um item — adicionar uma página
 * canonical faz o comando aparecer AUTOMATICAMENTE (zero drift, zero hardcode).
 *
 * Consumido por: (1) CommandPalette do chat (Ctrl+/) categoria "Navegação";
 * (2) Card "Navegar com a LIA" na Central de Ajuda.
 */
export interface NavCatalogItem {
  page: CanonicalPageValue
  label: string
  url: string
}

export function navigationCatalog(locale: string = "pt"): NavCatalogItem[] {
  const out: NavCatalogItem[] = []
  for (const page of Object.values(CANONICAL_PAGES) as CanonicalPageValue[]) {
    const url = canonicalPageToUrl(page, locale)
    if (!url) continue // detalhes-sem-id + general
    out.push({ page, label: canonicalPageLabel(page), url })
  }
  return out
}

export function buildNavigationCommands(opts: {
  locale: string
  navigate: (url: string) => void
}): CommandItem[] {
  return navigationCatalog(opts.locale).map((item) => ({
    id: `nav-${item.page}`,
    label: `Ir para ${item.label}`,
    description: `Abrir ${item.label}`,
    icon: <Compass className="w-4 h-4" />,
    category: "navigation" as const,
    onSelect: () => opts.navigate(item.url),
  }))
}


/**
 * Fase 2 (2026-06-06): comandos de AÇÃO derivados do catálogo do backend
 * (capability_map, via useCommandCatalog). onSelect manda o label como mensagem
 * pra LIA, que roteia para a capability (abre modal / navega / confirma HITL).
 */
export interface CatalogActionItem {
  intent: string
  label: string
  category?: string
  requires_confirmation?: boolean
}

export function buildActionCommands(
  items: CatalogActionItem[],
  sendMessage: (text: string) => void,
): CommandItem[] {
  return items.map((item) => ({
    id: `action-${item.intent}`,
    label: item.label,
    description: item.requires_confirmation
      ? "Abre com confirmação na tela"
      : "Pedir à IA",
    icon: <Sparkles className="w-4 h-4" />,
    category: "actions" as const,
    onSelect: () => sendMessage(item.label),
  }))
}
