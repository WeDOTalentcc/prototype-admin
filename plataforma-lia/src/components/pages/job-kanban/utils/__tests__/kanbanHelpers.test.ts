/**
 * Tests — kanbanHelpers utilities
 *
 * Covers calculateNotaLiaGeral:
 * - score 0 for candidate with all zeros
 * - perfect candidate scores 100
 * - only skillsMatch contributes to base (25% weight)
 * - only liaScore contributes to base (30% weight)
 * - only technicalTestScore contributes to base (25% weight)
 * - only englishTestScore contributes to base (20% weight)
 * - bonus urgency for approvalPending + aguardando_aprovacao_contato
 * - bonus etapa for stage === Final
 * - bonus triagem for triageComplete
 * - score capped at 100
 * - score minimum 0
 *
 * Covers getLiaAlerts:
 * - returns empty array for clean candidate
 * - urgent alert for aguardando_aprovacao_contato
 * - action alert for reprovado without feedback
 * - warning alert for candidate with warnings
 *
 * Covers getFilteredAndSortedCandidates:
 * - filters by search query on name
 * - sorts by notaLiaGeral desc by default
 */
import { describe, it, expect } from 'vitest'
import { calculateNotaLiaGeral, getLiaAlerts, getFilteredAndSortedCandidates } from '../kanbanHelpers'

const baseCandidateZero = {
  id: 'c0',
  name: 'Zero Candidate',
}

const baseCandidatePerfect = {
  id: 'c1',
  name: 'Perfect Candidate',
  skillsMatch: 100,
  liaScore: 100,
  technicalTestScore: 100,
  englishTestScore: 100,
  triageComplete: true,
  stage: 'Final',
}

describe('calculateNotaLiaGeral', () => {
  it('returns 0 for candidate with no score fields', () => {
    expect(calculateNotaLiaGeral(baseCandidateZero)).toBe(0)
  })

  it('returns 100 for perfect candidate', () => {
    // 25 + 30 + 25 + 20 + 5 (triagem) + 5 (Final) = 105 → capped at 100
    expect(calculateNotaLiaGeral(baseCandidatePerfect)).toBe(100)
  })

  it('skillsMatch 100 contributes 25 to base', () => {
    const score = calculateNotaLiaGeral({ id: 'x', name: 'x', skillsMatch: 100 })
    expect(score).toBe(25)
  })

  it('liaScore 100 contributes 30 to base', () => {
    const score = calculateNotaLiaGeral({ id: 'x', name: 'x', liaScore: 100 })
    expect(score).toBe(30)
  })

  it('technicalTestScore 100 contributes 25 to base', () => {
    const score = calculateNotaLiaGeral({ id: 'x', name: 'x', technicalTestScore: 100 })
    expect(score).toBe(25)
  })

  it('englishTestScore 100 contributes 20 to base', () => {
    const score = calculateNotaLiaGeral({ id: 'x', name: 'x', englishTestScore: 100 })
    expect(score).toBe(20)
  })

  it('approvalPending + aguardando_aprovacao_contato adds 10 bonus', () => {
    const score = calculateNotaLiaGeral({
      id: 'x', name: 'x',
      approvalPending: true,
      liaStatus: 'aguardando_aprovacao_contato',
    })
    expect(score).toBe(10)
  })

  it('stage Final adds 5 bonus', () => {
    const score = calculateNotaLiaGeral({ id: 'x', name: 'x', stage: 'Final' })
    expect(score).toBe(5)
  })

  it('triageComplete adds 5 bonus', () => {
    const score = calculateNotaLiaGeral({ id: 'x', name: 'x', triageComplete: true })
    expect(score).toBe(5)
  })

  it('score is capped at 100', () => {
    expect(calculateNotaLiaGeral(baseCandidatePerfect)).toBeLessThanOrEqual(100)
  })

  it('score is minimum 0 even with negative inputs', () => {
    const score = calculateNotaLiaGeral({ id: 'x', name: 'x', skillsMatch: -100 })
    expect(score).toBeGreaterThanOrEqual(0)
  })

  it('uses fitScore as fallback for skillsMatch', () => {
    const score = calculateNotaLiaGeral({ id: 'x', name: 'x', fitScore: 100 })
    expect(score).toBe(25)
  })

  it('uses score as fallback for liaScore', () => {
    const scoreVal = calculateNotaLiaGeral({ id: 'x', name: 'x', score: 100 })
    expect(scoreVal).toBe(30)
  })
})

describe('getLiaAlerts', () => {
  it('returns empty array for clean candidate', () => {
    const alerts = getLiaAlerts({ id: 'c1', name: 'Clean' })
    expect(alerts).toHaveLength(0)
  })

  it('returns urgent alert for aguardando_aprovacao_contato', () => {
    const alerts = getLiaAlerts({
      id: 'c1', name: 'Pending',
      approvalPending: true,
      liaStatus: 'aguardando_aprovacao_contato',
    })
    expect(alerts).toHaveLength(1)
    expect(alerts[0].type).toBe('urgent')
    expect(alerts[0].label).toBe('Aprovar Contato')
  })

  it('returns urgent alert for triagem_completa', () => {
    const alerts = getLiaAlerts({
      id: 'c1', name: 'Triaged',
      approvalPending: true,
      liaStatus: 'triagem_completa',
    })
    expect(alerts.some(a => a.label === 'Aprovar Entrevista')).toBe(true)
  })

  it('returns action alert for reprovado without feedback', () => {
    const alerts = getLiaAlerts({
      id: 'c2', name: 'Rejected',
      status: 'reprovado',
      feedbackStatus: 'pending',
    })
    expect(alerts.some(a => a.type === 'action')).toBe(true)
  })

  it('does not return action alert if feedback already sent', () => {
    const alerts = getLiaAlerts({
      id: 'c2', name: 'Rejected with feedback',
      status: 'reprovado',
      feedbackStatus: 'feedback_enviado',
    })
    expect(alerts.some(a => a.type === 'action')).toBe(false)
  })

  it('returns warning alert for candidate with warnings > 0', () => {
    const alerts = getLiaAlerts({
      id: 'c3', name: 'Warning',
      warnings: 2,
    })
    expect(alerts.some(a => a.type === 'warning')).toBe(true)
    expect(alerts.find(a => a.type === 'warning')?.label).toContain('2')
  })
})

describe('getFilteredAndSortedCandidates', () => {
  const candidates = [
    { id: 'a', name: 'Alice', role: 'Engineer', skillsMatch: 80 },
    { id: 'b', name: 'Bob', role: 'Designer', skillsMatch: 40 },
    { id: 'c', name: 'Charlie', role: 'Manager', skillsMatch: 60 },
  ]

  it('returns all candidates when no filter', () => {
    const result = getFilteredAndSortedCandidates(() => candidates, '', [], 'notaLiaGeral', 'desc')
    expect(result).toHaveLength(3)
  })

  it('filters by search query on name', () => {
    const result = getFilteredAndSortedCandidates(() => candidates, 'alice', [], 'notaLiaGeral', 'desc')
    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('Alice')
  })

  it('filters by search query on role', () => {
    const result = getFilteredAndSortedCandidates(() => candidates, 'designer', [], 'notaLiaGeral', 'desc')
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('b')
  })

  it('sorts by notaLiaGeral desc — higher skillsMatch first', () => {
    const result = getFilteredAndSortedCandidates(() => candidates, '', [], 'notaLiaGeral', 'desc')
    expect(result[0].id).toBe('a') // Alice: 80 skillsMatch → highest score
  })

  it('sorts by notaLiaGeral asc — lower score first', () => {
    const result = getFilteredAndSortedCandidates(() => candidates, '', [], 'notaLiaGeral', 'asc')
    expect(result[0].id).toBe('b') // Bob: 40 skillsMatch → lowest score
  })

  it('returns empty array when no candidates match search', () => {
    const result = getFilteredAndSortedCandidates(() => candidates, 'xyznotfound', [], 'notaLiaGeral', 'desc')
    expect(result).toHaveLength(0)
  })

  it('filters by stage when tableStageFilter provided', () => {
    const withStages = [
      { id: 'a', name: 'Alice', role: 'Engineer', skillsMatch: 80, stage: 'Triagem' },
      { id: 'b', name: 'Bob', role: 'Designer', skillsMatch: 40, stage: 'Entrevista' },
      { id: 'c', name: 'Charlie', role: 'Manager', skillsMatch: 60, stage: 'Entrevista' },
    ]
    const result = getFilteredAndSortedCandidates(() => withStages, '', ['Triagem'], 'notaLiaGeral', 'desc')
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('a')
  })
})
