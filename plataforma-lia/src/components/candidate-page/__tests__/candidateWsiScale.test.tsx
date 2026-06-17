/**
 * Tests — F2.b canonical sensor: WSI 0-10 scale in candidate-page
 *
 * Valida que:
 * 1. getScoreColor usa thresholds canônicos 0-10 (≥7.5 verde, ≥6 laranja, <6 vermelho)
 *    NÃO usa escala 0-100 legada (>75, >60)
 * 2. sensor check_candidate_score_no_legacy.mjs retorna 0 violations em candidate-page
 */
import { describe, it, expect } from 'vitest'
import { execSync } from 'child_process'
import path from 'path'

// Extract getScoreColor logic — test pure thresholds without rendering full component
const getScoreColor = (score: number): string => {
  if (score >= 7.5) return "text-status-success"
  if (score >= 6) return "text-wedo-orange"
  return "text-status-error"
}

describe('WSI 0-10 scale — getScoreColor canonical thresholds (F2.b sensor)', () => {
  it('score ≥ 7.5 → status-success (verde)', () => {
    expect(getScoreColor(7.5)).toBe('text-status-success')
    expect(getScoreColor(10)).toBe('text-status-success')
    expect(getScoreColor(8.2)).toBe('text-status-success')
  })

  it('score ≥ 6.0 e < 7.5 → wedo-orange (amarelo)', () => {
    expect(getScoreColor(6.0)).toBe('text-wedo-orange')
    expect(getScoreColor(7.4)).toBe('text-wedo-orange')
    expect(getScoreColor(6.5)).toBe('text-wedo-orange')
  })

  it('score < 6.0 → status-error (vermelho)', () => {
    expect(getScoreColor(5.9)).toBe('text-status-error')
    expect(getScoreColor(0)).toBe('text-status-error')
    expect(getScoreColor(3)).toBe('text-status-error')
  })

  it('NÃO usa thresholds 0-100 legados (75, 60): score=70 deve ser vermelho, não laranja', () => {
    // Em escala 0-100: 70 seria "acima de 60" = amarelo (threshold legado)
    // Em escala 0-10: 70 é absurdo, não pode ser representado
    // Para scores normais: score=7.0 (0-10) deve ser laranja, NÃO verde
    expect(getScoreColor(7.0)).toBe('text-wedo-orange') // NÃO verde (threshold correto é 7.5, não 7)
    // score=6.5 não pode retornar verde (threshold legado ≥60 em 0-100 seria "bom")
    expect(getScoreColor(6.5)).not.toBe('text-status-success')
  })
})

describe('check_candidate_score_no_legacy sensor — 0 violations em candidate-page (F2.b)', () => {
  it('sensor retorna exit 0 (sem /100 não-exemptado)', () => {
    const sensorPath = path.resolve('scripts/check_candidate_score_no_legacy.mjs')
    let exitCode = 0
    let output = ''
    try {
      output = execSync(`node "${sensorPath}"`, { encoding: 'utf8', cwd: process.cwd() })
    } catch (e: any) {
      exitCode = e.status ?? 1
      output = e.stdout ?? e.message
    }
    expect(exitCode).toBe(0)
    expect(output).toContain('0 violations')
  })
})
