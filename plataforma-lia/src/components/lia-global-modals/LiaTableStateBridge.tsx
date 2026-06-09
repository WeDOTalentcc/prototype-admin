"use client"

import { useEffect } from "react"
import { useCandidatesStore } from "@/stores/candidates-store"

/**
 * LiaTableStateBridge — ponte in-page (Fase 2 slice 1).
 *
 * Aplica filtro/busca/ordenação vindos do chat à tabela JÁ ABERTA, sem
 * navegar nem mutar dados. Escuta `lia:apply_table_state` (despachado pelo
 * `useUIAction` quando a action global `apply_table_state` chega do backend)
 * e dirige o store da superfície.
 *
 * Slice 1: só a superfície "candidates" (funil) via `useCandidatesStore`.
 * Superfícies futuras (jobs, etc.) entram aqui em slices seguintes.
 *
 * Fase 2 funil tabs: `patch.tab` troca a aba do Funil via `setActiveTab`
 * (search/favorites/lists/history/saved-searches/agents).
 *
 * Montado globalmente em LIAGlobalModals — funciona de qualquer página.
 */
type ActiveTab =
  | "search"
  | "favorites"
  | "lists"
  | "history"
  | "saved-searches"
  | "agents"

const VALID_TABS: ReadonlySet<string> = new Set<ActiveTab>([
  "search",
  "favorites",
  "lists",
  "history",
  "saved-searches",
  "agents",
])

export function LiaTableStateBridge() {
  useEffect(() => {
    function handle(e: Event) {
      const { surface, patch } =
        (e as CustomEvent<{ surface: string; patch: Record<string, unknown> }>)
          .detail ?? {}
      if (surface !== "candidates" || !patch) return
      const s = useCandidatesStore.getState()
      if (typeof patch.search === "string") s.setSearchTerm(patch.search)
      if (typeof patch.sortBy === "string") s.setSortBy(patch.sortBy)
      if (patch.sortOrder === "asc" || patch.sortOrder === "desc")
        s.setSortOrder(patch.sortOrder)
      if (Array.isArray(patch.quickFilters))
        s.setQuickFilters(new Set(patch.quickFilters as string[]))
      if (typeof patch.tab === "string" && VALID_TABS.has(patch.tab))
        s.setActiveTab(patch.tab as ActiveTab)
    }
    function handleSelectRows(e: Event) {
      const { surface, mode, ids } = (
        e as CustomEvent<{
          surface: string
          mode: string
          ids?: string[]
        }>
      ).detail ?? {}
      if (surface !== "candidates") return
      const s = useCandidatesStore.getState()
      if (mode === "clear") {
        s.clearSelection()
      } else if (mode === "set" && Array.isArray(ids)) {
        s.setSelectedCandidates(new Set(ids as string[]))
      } else if (mode === "add" && Array.isArray(ids)) {
        const current = s.selectedCandidates
        s.setSelectedCandidates(new Set([...current, ...(ids as string[])]))
      }
    }

    window.addEventListener("lia:apply_table_state", handle)
    window.addEventListener("lia:select_rows", handleSelectRows)
    return () => {
      window.removeEventListener("lia:apply_table_state", handle)
      window.removeEventListener("lia:select_rows", handleSelectRows)
    }
  }, [])
  return null
}
