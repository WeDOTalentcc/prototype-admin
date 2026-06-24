/**
 * lia-context-utils — pure converters: UI filter state → lia-context string[].
 *
 * These functions translate Zustand filter objects into human-readable strings
 * that the backend format_view_context() renders in the agent system prompt as
 * "Filtros ativos: ...". Pure functions — zero React hooks, zero side effects.
 *
 * P0-2 (2026-06-18): wires active_filters signal to lia-context-store.
 * Called by use-filters-persistence.ts and job-filters-store.ts.
 */

import type { KanbanFiltersPersisted } from '@/components/kanban/hooks/use-filters-persistence'
import type { JobFiltersState } from '@/stores/job-filters-store'

/**
 * Convert kanban pipeline filters into lia-context filter strings.
 * Returns [] when no filter is active (caller should call setLiaFilters(null)).
 */
export function kanbanFiltersToLia(filters: KanbanFiltersPersisted): string[] {
  const active: string[] = []

  if (filters.searchQuery.trim()) {
    active.push(`busca: "${filters.searchQuery.trim()}"`)
  }
  if (filters.stageFilter.length > 0) {
    active.push(`etapas: ${filters.stageFilter.join(', ')}`)
  }
  if (filters.scoreMin !== null) {
    active.push(`score ≥ ${filters.scoreMin}`)
  }
  if (filters.statusFilter) {
    active.push(`status: ${filters.statusFilter}`)
  }
  if (filters.workModelFilter) {
    active.push(`modelo: ${filters.workModelFilter}`)
  }

  return active
}

/**
 * Convert job list filters (Página Vagas) into lia-context filter strings.
 * Returns [] when no filter is active.
 */
export function jobFiltersToLia(filters: JobFiltersState): string[] {
  const active: string[] = []

  if (filters.searchTerm.trim()) {
    active.push(`busca: "${filters.searchTerm.trim()}"`)
  }
  if (filters.selectedStatusFilter && filters.selectedStatusFilter !== 'todas') {
    active.push(`status: ${filters.selectedStatusFilter}`)
  }
  if (filters.selectedDaysFilter && filters.selectedDaysFilter !== 'todas') {
    active.push(`período: ${filters.selectedDaysFilter}`)
  }
  if (filters.booleanSearch.trim()) {
    active.push(`busca booleana: "${filters.booleanSearch.trim()}"`)
  }

  const advanced = filters.advancedFilters ?? {}
  const advancedActive = Object.entries(advanced)
    .filter(([, v]) => Array.isArray(v) && v.length > 0)
    .map(([k, v]) => `${k}: ${(v as string[]).join(', ')}`)

  active.push(...advancedActive)

  return active
}
