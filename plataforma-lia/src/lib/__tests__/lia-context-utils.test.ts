/**
 * Tests for lia-context-utils.ts — TDD P0-2 (2026-06-18)
 *
 * Pure function tests — no React, no side effects.
 */
import { describe, it, expect } from 'vitest'
import { kanbanFiltersToLia, jobFiltersToLia } from '../lia-context-utils'
import type { KanbanFiltersPersisted } from '@/components/kanban/hooks/use-filters-persistence'
import type { JobFiltersState } from '@/stores/job-filters-store'

const BASE_KANBAN: KanbanFiltersPersisted = {
  searchQuery: '',
  stageFilter: [],
  scoreMin: null,
  statusFilter: null,
  workModelFilter: null,
  sortColumn: 'notaLiaGeral',
  sortDirection: 'desc',
}

describe('kanbanFiltersToLia', () => {
  it('retorna [] quando nenhum filtro está ativo', () => {
    expect(kanbanFiltersToLia(BASE_KANBAN)).toEqual([])
  })

  it('inclui busca quando searchQuery preenchido', () => {
    const result = kanbanFiltersToLia({ ...BASE_KANBAN, searchQuery: 'python' })
    expect(result).toContain('busca: "python"')
  })

  it('ignora searchQuery com apenas espaços', () => {
    const result = kanbanFiltersToLia({ ...BASE_KANBAN, searchQuery: '   ' })
    expect(result).toEqual([])
  })

  it('inclui etapas quando stageFilter tem valores', () => {
    const result = kanbanFiltersToLia({ ...BASE_KANBAN, stageFilter: ['triagem', 'entrevista'] })
    expect(result.some(f => f.includes('triagem') && f.includes('entrevista'))).toBe(true)
  })

  it('inclui score quando scoreMin está definido', () => {
    const result = kanbanFiltersToLia({ ...BASE_KANBAN, scoreMin: 70 })
    expect(result).toContain('score ≥ 70')
  })

  it('inclui status quando statusFilter está definido', () => {
    const result = kanbanFiltersToLia({ ...BASE_KANBAN, statusFilter: 'ativo' })
    expect(result).toContain('status: ativo')
  })

  it('inclui modelo quando workModelFilter está definido', () => {
    const result = kanbanFiltersToLia({ ...BASE_KANBAN, workModelFilter: 'remoto' })
    expect(result).toContain('modelo: remoto')
  })

  it('combina múltiplos filtros ativos', () => {
    const result = kanbanFiltersToLia({
      ...BASE_KANBAN,
      searchQuery: 'python',
      scoreMin: 80,
      workModelFilter: 'hibrido',
    })
    expect(result.length).toBe(3)
    expect(result).toContain('score ≥ 80')
  })
})

function createBaseJobFilters(): JobFiltersState {
  return {
    selectedStatusFilter: 'todas',
    selectedDaysFilter: 'todas',
    advancedFilters: {},
    booleanSearch: '',
    searchTerm: '',
  }
}

describe('jobFiltersToLia', () => {
  it('retorna [] quando nenhum filtro está ativo', () => {
    expect(jobFiltersToLia(createBaseJobFilters())).toEqual([])
  })

  it('inclui busca quando searchTerm preenchido', () => {
    const result = jobFiltersToLia({ ...createBaseJobFilters(), searchTerm: 'engenheiro' })
    expect(result).toContain('busca: "engenheiro"')
  })

  it('inclui status quando não é "todas"', () => {
    const result = jobFiltersToLia({ ...createBaseJobFilters(), selectedStatusFilter: 'publicada' })
    expect(result).toContain('status: publicada')
  })

  it('NÃO inclui status quando é "todas"', () => {
    const result = jobFiltersToLia({ ...createBaseJobFilters(), selectedStatusFilter: 'todas' })
    expect(result).toEqual([])
  })

  it('inclui filtros avançados quando têm valores', () => {
    const result = jobFiltersToLia({
      ...createBaseJobFilters(),
      advancedFilters: { departments: ['Engineering', 'Product'] },
    })
    expect(result.some(f => f.includes('departments'))).toBe(true)
  })
})
