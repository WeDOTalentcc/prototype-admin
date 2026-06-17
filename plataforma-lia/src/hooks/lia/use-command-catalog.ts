"use client"

/**
 * Fase 2 (2026-06-06): catálogo de comandos ACIONÁVEIS da LIA, derivado do
 * capability_map (backend) via /api/backend-proxy/lia/command-catalog. Consumido
 * pelo CommandPalette (Ctrl+/) p/ popular a categoria "Ações". DRY: dar label a
 * uma capability no yaml → ela aparece aqui (zero drift, sem hardcode no FE).
 */
import { useQuery } from "@tanstack/react-query"

export interface CommandCatalogItem {
  intent: string
  label: string
  category: string
  requires_confirmation?: boolean
  modal_id?: string | null
  navigate_page?: string | null
}

export function useCommandCatalog() {
  return useQuery<CommandCatalogItem[]>({
    queryKey: ["lia-command-catalog"],
    queryFn: async () => {
      const res = await fetch("/api/backend-proxy/lia/command-catalog")
      if (!res.ok) throw new Error(`command-catalog HTTP ${res.status}`)
      const json = await res.json()
      // o proxy desembrulha o envelope; o endpoint retorna { commands: [...] }
      const commands = json?.commands ?? json?.data?.commands ?? []
      return Array.isArray(commands) ? commands : []
    },
    staleTime: 5 * 60_000, // catálogo é estático — cache 5min
  })
}
