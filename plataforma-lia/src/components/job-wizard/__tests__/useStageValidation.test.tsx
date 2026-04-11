import { renderHook } from '@testing-library/react'
import React from 'react'

vi.mock('@/lib/pricing', () => ({
  CURRENCY_SYMBOL: 'R$',
}))

vi.mock('@/stores/wizard-store', () => ({
  useWizardStore: vi.fn(() => ({
    draft: null,
    draftId: null,
    setDraft: vi.fn(),
    setDraftId: vi.fn(),
    clearDraft: vi.fn(),
  })),
}))

vi.mock('@/hooks/company/useCompanyBenefits', () => ({
  useCompanyBenefits: () => ({
    benefits: [],
    isLoading: false,
    error: null,
  }),
}))

import { WizardProvider } from '../WizardContext'
import { useStageValidation } from '../hooks/useStageValidation'

function wrapper({ children }: { children: React.ReactNode }) {
  return <WizardProvider companyId="test-co">{children}</WizardProvider>
}

describe('useStageValidation — required field checks', () => {
  it('input-evaluation: returns error when cargo not detected', () => {
    const { result } = renderHook(() => useStageValidation('input-evaluation'), { wrapper })
    expect(result.current.isValid).toBe(false)
    expect(result.current.errors).toContain('Cargo não detectado')
  })

  it('input-evaluation: returns low completion with empty criteria', () => {
    const { result } = renderHook(() => useStageValidation('input-evaluation'), { wrapper })
    expect(result.current.completionPercentage).toBeLessThan(50)
  })

  it('job-description: returns error when cargo is empty', () => {
    const { result } = renderHook(() => useStageValidation('job-description'), { wrapper })
    expect(result.current.errors).toContain('Cargo é obrigatório')
    expect(result.current.isValid).toBe(false)
  })

  it('job-description: returns warnings for missing optional fields', () => {
    const { result } = renderHook(() => useStageValidation('job-description'), { wrapper })
    expect(result.current.warnings.some(w => w.includes('Área'))).toBe(true)
    expect(result.current.warnings.some(w => w.includes('Localidade'))).toBe(true)
  })

  it('competencies: returns error when fewer than 3 technical skills', () => {
    const { result } = renderHook(() => useStageValidation('competencies'), { wrapper })
    expect(result.current.errors.some(e => e.includes('Mínimo 3 competências técnicas'))).toBe(true)
    expect(result.current.isValid).toBe(false)
  })

  it('salary: returns warning when salary range not defined', () => {
    const { result } = renderHook(() => useStageValidation('salary'), { wrapper })
    expect(result.current.warnings.some(w => w.includes('salarial'))).toBe(true)
  })

  it('wsi-questions: returns error when fewer than 3 questions selected', () => {
    const { result } = renderHook(() => useStageValidation('wsi-questions'), { wrapper })
    expect(result.current.errors.some(e => e.includes('pelo menos 3 perguntas'))).toBe(true)
    expect(result.current.isValid).toBe(false)
  })

  it('review-publish: validates cargo and technical skills from previous stages', () => {
    const { result } = renderHook(() => useStageValidation('review-publish'), { wrapper })
    expect(result.current.errors.some(e => e.includes('Cargo'))).toBe(true)
    expect(result.current.errors.some(e => e.includes('técnicas'))).toBe(true)
  })

  it('search-calibration: always valid (no validation)', () => {
    const { result } = renderHook(() => useStageValidation('search-calibration'), { wrapper })
    expect(result.current.isValid).toBe(true)
    expect(result.current.completionPercentage).toBe(100)
  })
})
