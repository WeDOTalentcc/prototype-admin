import { describe, it, expect } from 'vitest'
import {
  classifyImplicitSignal,
  isAbandonmentCandidate,
  tokenOverlap,
} from '../implicit-feedback-detect'

const PIPELINE_ANSWER =
  'Montei o pipeline com sete etapas conforme o template padrão da vaga.'

describe('Task #1299 — implicit feedback client classifier', () => {
  describe('tokenOverlap', () => {
    it('is 0 for disjoint topics', () => {
      expect(
        tokenOverlap(PIPELINE_ANSWER, 'quanto custa o plano enterprise anual'),
      ).toBeLessThanOrEqual(0.08)
    })
    it('is high for an edited reuse of the same text', () => {
      const edited = PIPELINE_ANSWER.replace('sete', 'oito')
      expect(tokenOverlap(PIPELINE_ANSWER, edited)).toBeGreaterThanOrEqual(0.45)
    })
  })

  describe('isAbandonmentCandidate (conservative)', () => {
    it('rejects a short LIA answer', () => {
      expect(isAbandonmentCandidate('Ok.', 'vamos falar de outra coisa agora')).toBe(false)
    })
    it('rejects when LIA asked a question', () => {
      expect(
        isAbandonmentCandidate(
          'Posso seguir para a triagem desta vaga sênior?',
          'prefiro revisar os requisitos antes disso',
        ),
      ).toBe(false)
    })
    it('rejects a continuation/confirmation token', () => {
      for (const tok of ['sim', 'pode', 'vamos', 'ok', 'continua']) {
        expect(isAbandonmentCandidate(PIPELINE_ANSWER, tok)).toBe(false)
      }
    })
    it('rejects a too-short next message', () => {
      expect(isAbandonmentCandidate(PIPELINE_ANSWER, 'tudo bem')).toBe(false)
    })
    it('rejects a topical follow-up', () => {
      expect(
        isAbandonmentCandidate(
          PIPELINE_ANSWER,
          'muda o pipeline para incluir mais uma etapa no template da vaga',
        ),
      ).toBe(false)
    })
    it('accepts a clear topic switch', () => {
      expect(
        isAbandonmentCandidate(
          PIPELINE_ANSWER,
          'quanto custa o plano enterprise para faturamento anual',
        ),
      ).toBe(true)
    })
  })

  describe('classifyImplicitSignal', () => {
    it('returns null for empty inputs', () => {
      expect(classifyImplicitSignal('', 'algo')).toBeNull()
      expect(classifyImplicitSignal(PIPELINE_ANSWER, '')).toBeNull()
    })
    it('returns null for verbatim reuse (not a correction)', () => {
      expect(classifyImplicitSignal(PIPELINE_ANSWER, PIPELINE_ANSWER)).toBeNull()
    })
    it('detects correction_delta for an edited reuse', () => {
      const edited = PIPELINE_ANSWER.replace('sete', 'oito')
      expect(classifyImplicitSignal(PIPELINE_ANSWER, edited)).toBe('correction_delta')
    })
    it('detects abandonment for a topic switch', () => {
      expect(
        classifyImplicitSignal(
          PIPELINE_ANSWER,
          'quanto custa o plano enterprise para faturamento anual',
        ),
      ).toBe('abandonment')
    })
    it('returns null for an ordinary short continuation', () => {
      expect(classifyImplicitSignal(PIPELINE_ANSWER, 'sim, pode seguir')).toBeNull()
    })
  })
})
