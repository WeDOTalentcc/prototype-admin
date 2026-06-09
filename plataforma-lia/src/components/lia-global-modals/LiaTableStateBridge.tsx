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
 * Montado globalmente em LIAGlobalModals — funciona de qualquer página.
 */
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
    }
    window.addEventListener("lia:apply_table_state", handle)
    return () => window.removeEventListener("lia:apply_table_state", handle)
  }, [])
  return null
}
