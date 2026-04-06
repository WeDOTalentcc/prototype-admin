import { filterKanbanCandidates, type KanbanFilterCriteria } from '../filter-utils'
import type { KanbanCandidate } from '../../types'

function makeCandidate(overrides: Partial<KanbanCandidate> & { id: string; name: string }): KanbanCandidate {
  return {
    stage: 'sourcing',
    email: '',
    role: '',
    location: '',
    skills: [],
    score: 0,
    ...overrides,
  } as KanbanCandidate
}

const candidates: KanbanCandidate[] = [
  makeCandidate({ id: '1', name: 'Ana Silva', role: 'Frontend Dev', location: 'São Paulo', score: 85, skills: ['React', 'TypeScript'], workModel: 'remoto', status: 'active', currentCompany: 'TechCo' }),
  makeCandidate({ id: '2', name: 'Bruno Costa', role: 'Backend Dev', location: 'Rio de Janeiro', score: 60, skills: ['Python', 'Django'], workModel: 'híbrido', status: 'pending' }),
  makeCandidate({ id: '3', name: 'Carla Mendes', role: 'Designer', location: 'Curitiba', score: 92, skills: ['Figma', 'CSS'], workModel: 'presencial', status: 'active', origin: 'linkedin' }),
]

describe('filterKanbanCandidates', () => {
  it('returns all candidates with no filters', () => {
    expect(filterKanbanCandidates(candidates, {})).toHaveLength(3)
  })

  it('filters by name search query', () => {
    const result = filterKanbanCandidates(candidates, { searchQuery: 'ana' })
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('1')
  })

  it('filters by role search query', () => {
    const result = filterKanbanCandidates(candidates, { searchQuery: 'designer' })
    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('Carla Mendes')
  })

  it('filters by skill search query', () => {
    const result = filterKanbanCandidates(candidates, { searchQuery: 'react' })
    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('Ana Silva')
  })

  it('filters by location search query', () => {
    const result = filterKanbanCandidates(candidates, { searchQuery: 'rio' })
    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('Bruno Costa')
  })

  it('filters by company search query', () => {
    const result = filterKanbanCandidates(candidates, { searchQuery: 'techco' })
    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('Ana Silva')
  })

  it('filters by minimum score', () => {
    const result = filterKanbanCandidates(candidates, { kanbanScoreMin: 80 })
    expect(result).toHaveLength(2)
    expect(result.map(c => c.name)).toEqual(['Ana Silva', 'Carla Mendes'])
  })

  it('filters by status', () => {
    const result = filterKanbanCandidates(candidates, { kanbanStatusFilter: 'active' })
    expect(result).toHaveLength(2)
  })

  it('filters by work model', () => {
    const result = filterKanbanCandidates(candidates, { kanbanWorkModelFilter: 'remoto' })
    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('Ana Silva')
  })

  it('filters by origin', () => {
    const result = filterKanbanCandidates(candidates, { kanbanOriginFilter: ['linkedin'] })
    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('Carla Mendes')
  })

  it('combines multiple filters', () => {
    const filters: KanbanFilterCriteria = {
      kanbanScoreMin: 80,
      kanbanStatusFilter: 'active',
    }
    const result = filterKanbanCandidates(candidates, filters)
    expect(result).toHaveLength(2)
  })

  it('returns empty when no candidates match', () => {
    const result = filterKanbanCandidates(candidates, { searchQuery: 'nonexistent' })
    expect(result).toHaveLength(0)
  })

  it('ignores score filter when value is 0 or null', () => {
    expect(filterKanbanCandidates(candidates, { kanbanScoreMin: 0 })).toHaveLength(3)
    expect(filterKanbanCandidates(candidates, { kanbanScoreMin: null })).toHaveLength(3)
  })
})
