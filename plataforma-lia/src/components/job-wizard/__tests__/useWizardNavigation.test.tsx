import { renderHook, act } from '@testing-library/react'
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
import { useWizardNavigation } from '../hooks/useWizardNavigation'

function wrapper({ children }: { children: React.ReactNode }) {
  return <WizardProvider companyId="test-co">{children}</WizardProvider>
}

describe('useWizardNavigation — stage progression flow', () => {
  it('starts at first stage (input-evaluation)', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })
    expect(result.current.currentStage).toBe('input-evaluation')
    expect(result.current.currentStageIndex).toBe(0)
    expect(result.current.isFirstStage).toBe(true)
    expect(result.current.isLastStage).toBe(false)
  })

  it('advances to next stage via goToNextStage', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })

    act(() => result.current.goToNextStage())

    expect(result.current.currentStage).toBe('job-description')
    expect(result.current.currentStageIndex).toBe(1)
    expect(result.current.isFirstStage).toBe(false)
  })

  it('goes back to previous stage via goToPreviousStage', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })

    act(() => result.current.goToNextStage())
    expect(result.current.currentStage).toBe('job-description')

    act(() => result.current.goToPreviousStage())
    expect(result.current.currentStage).toBe('input-evaluation')
    expect(result.current.isFirstStage).toBe(true)
  })

  it('does not go before first stage', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })
    act(() => result.current.goToPreviousStage())
    expect(result.current.currentStage).toBe('input-evaluation')
    expect(result.current.currentStageIndex).toBe(0)
  })

  it('navigates through all 7 stages in order', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })
    const expectedStages = [
      'input-evaluation',
      'job-description',
      'competencies',
      'salary',
      'wsi-questions',
      'review-publish',
      'search-calibration',
    ]

    for (let i = 0; i < expectedStages.length; i++) {
      expect(result.current.currentStage).toBe(expectedStages[i])
      expect(result.current.currentStageIndex).toBe(i)
      if (i < expectedStages.length - 1) {
        act(() => result.current.goToNextStage())
      }
    }

    expect(result.current.isLastStage).toBe(true)
  })

  it('does not go past last stage', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })

    for (let i = 0; i < 7; i++) {
      act(() => result.current.goToNextStage())
    }

    expect(result.current.currentStage).toBe('search-calibration')
    act(() => result.current.goToNextStage())
    expect(result.current.currentStage).toBe('search-calibration')
  })

  it('goToStage jumps to a specific stage', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })

    act(() => result.current.goToStage('salary'))
    expect(result.current.currentStage).toBe('salary')
    expect(result.current.currentStageIndex).toBe(3)
  })

  it('shouldAutoAdvance returns false for review-publish', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })

    act(() => result.current.goToStage('review-publish'))
    expect(result.current.shouldAutoAdvance(1.0)).toBe(false)
  })

  it('shouldAutoAdvance returns true when confidence exceeds threshold', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })
    expect(result.current.shouldAutoAdvance(0.95)).toBe(true)
  })

  it('getStageProgress returns correct progress data', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })

    const progress = result.current.getStageProgress()
    expect(progress.current).toBe(1)
    expect(progress.total).toBe(7)
    expect(progress.percentage).toBeCloseTo(14.29, 1)

    act(() => result.current.goToNextStage())
    const p2 = result.current.getStageProgress()
    expect(p2.current).toBe(2)
    expect(p2.percentage).toBeCloseTo(28.57, 1)
  })

  it('currentStageConfig has correct title for each stage', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })
    expect(result.current.currentStageConfig.title).toBe('Avaliação')

    act(() => result.current.goToNextStage())
    expect(result.current.currentStageConfig.title).toBe('Descrição da Vaga')
  })

  it('navigating to search-calibration (last stage) signals submission readiness', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })
    act(() => result.current.goToStage('search-calibration'))
    expect(result.current.currentStage).toBe('search-calibration')
    expect(result.current.currentStageIndex).toBe(6)
  })

  it('navigating to review-publish (6th stage) signals publish readiness', () => {
    const { result } = renderHook(() => useWizardNavigation(), { wrapper })
    act(() => result.current.goToStage('review-publish'))
    expect(result.current.currentStage).toBe('review-publish')
    expect(result.current.currentStageIndex).toBe(5)
  })
})
