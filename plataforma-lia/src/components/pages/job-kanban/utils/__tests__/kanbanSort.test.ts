import { sortKanbanCandidates, KANBAN_SORT_FIELDS, DEFAULT_KANBAN_SORT_FIELD, DEFAULT_KANBAN_SORT_ORDER } from '../kanbanHelpers'

// Minimal candidate shape matching KanbanCandidateBase
function makeCandidate(overrides: Record<string, unknown> = {}) {
  return {
    id: overrides.id ?? 'c-1',
    name: (overrides.name as string) ?? 'Ana',
    score: overrides.score as number | undefined,
    liaScore: overrides.liaScore as number | undefined,
    skillsMatch: overrides.skillsMatch as number | undefined,
    fitScore: overrides.fitScore as number | undefined,
    needsAction: overrides.needsAction as boolean | undefined,
    appliedDate: overrides.appliedDate as string | undefined,
    technicalTestScore: overrides.technicalTestScore as number | undefined,
    englishTestScore: overrides.englishTestScore as number | undefined,
  }
}

describe('sortKanbanCandidates', () => {
  const candidates = [
    makeCandidate({ id: 'c-1', name: 'Carlos', score: 60, appliedDate: '15/01/2026' }),
    makeCandidate({ id: 'c-2', name: 'Ana', score: 90, appliedDate: '10/01/2026' }),
    makeCandidate({ id: 'c-3', name: 'Bruno', score: 75, appliedDate: '20/01/2026' }),
  ]

  it('defaults to score desc', () => {
    const sorted = sortKanbanCandidates(candidates)
    expect(sorted.map(c => c.id)).toEqual(['c-2', 'c-3', 'c-1'])
  })

  it('sorts by score asc', () => {
    const sorted = sortKanbanCandidates(candidates, 'score', 'asc')
    expect(sorted.map(c => c.id)).toEqual(['c-1', 'c-3', 'c-2'])
  })

  it('sorts by name asc', () => {
    const sorted = sortKanbanCandidates(candidates, 'name', 'asc')
    expect(sorted.map(c => c.name)).toEqual(['Ana', 'Bruno', 'Carlos'])
  })

  it('sorts by name desc', () => {
    const sorted = sortKanbanCandidates(candidates, 'name', 'desc')
    expect(sorted.map(c => c.name)).toEqual(['Carlos', 'Bruno', 'Ana'])
  })

  it('sorts by appliedDate desc', () => {
    const sorted = sortKanbanCandidates(candidates, 'appliedDate', 'desc')
    // String sort: "20/01" > "15/01" > "10/01"
    expect(sorted.map(c => c.id)).toEqual(['c-3', 'c-1', 'c-2'])
  })

  it('sorts by fitScore desc', () => {
    const items = [
      makeCandidate({ id: 'a', fitScore: 30 }),
      makeCandidate({ id: 'b', fitScore: 80 }),
      makeCandidate({ id: 'c', fitScore: 50 }),
    ]
    const sorted = sortKanbanCandidates(items, 'fitScore', 'desc')
    expect(sorted.map(c => c.id)).toEqual(['b', 'c', 'a'])
  })

  it('needsAction candidates float to top regardless of sort field', () => {
    const items = [
      makeCandidate({ id: 'low', score: 10, needsAction: false }),
      makeCandidate({ id: 'action', score: 5, needsAction: true }),
      makeCandidate({ id: 'high', score: 95, needsAction: false }),
    ]
    const sorted = sortKanbanCandidates(items, 'score', 'desc')
    expect(sorted[0].id).toBe('action')
    expect(sorted[1].id).toBe('high')
    expect(sorted[2].id).toBe('low')
  })

  it('returns a new array (does not mutate input)', () => {
    const original = [...candidates]
    const sorted = sortKanbanCandidates(candidates)
    expect(sorted).not.toBe(candidates)
    expect(candidates.map(c => c.id)).toEqual(original.map(c => c.id))
  })

  it('handles empty array', () => {
    const sorted = sortKanbanCandidates([])
    expect(sorted).toEqual([])
  })

  it('handles candidates with missing scores gracefully', () => {
    const items = [
      makeCandidate({ id: 'a', score: undefined }),
      makeCandidate({ id: 'b', score: 50 }),
    ]
    const sorted = sortKanbanCandidates(items, 'score', 'desc')
    expect(sorted[0].id).toBe('b')
    expect(sorted[1].id).toBe('a')
  })

  it('prefers liaScore over score when both present', () => {
    const items = [
      makeCandidate({ id: 'a', liaScore: 90, score: 10 }),
      makeCandidate({ id: 'b', liaScore: 40, score: 95 }),
    ]
    const sorted = sortKanbanCandidates(items, 'score', 'desc')
    // liaScore takes precedence: 90 > 40
    expect(sorted[0].id).toBe('a')
  })
})

describe('KANBAN_SORT_FIELDS', () => {
  it('exposes 5 sort fields', () => {
    expect(Object.keys(KANBAN_SORT_FIELDS)).toHaveLength(5)
  })

  it('has expected fields', () => {
    expect(KANBAN_SORT_FIELDS).toHaveProperty('score')
    expect(KANBAN_SORT_FIELDS).toHaveProperty('name')
    expect(KANBAN_SORT_FIELDS).toHaveProperty('appliedDate')
    expect(KANBAN_SORT_FIELDS).toHaveProperty('fitScore')
    expect(KANBAN_SORT_FIELDS).toHaveProperty('notaLiaGeral')
  })
})

describe('defaults', () => {
  it('default sort is score desc', () => {
    expect(DEFAULT_KANBAN_SORT_FIELD).toBe('score')
    expect(DEFAULT_KANBAN_SORT_ORDER).toBe('desc')
  })
})
