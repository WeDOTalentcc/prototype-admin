// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useUnifiedCommunication } from '../useUnifiedCommunication'

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock('@/stores/failedDeliveryStore', () => ({
  useFailedDeliveryStore: { getState: () => ({ addFailure: vi.fn(), clearFailure: vi.fn() }) },
}))

describe('useUnifiedCommunication — injecao de feedback por IA', () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        body: 'Olá Maria, obrigado por participar do processo. Seguimos com outro perfil. Sucesso!',
        subject: 'Retorno sobre sua candidatura',
        high_risk: false,
        ai_personalized: true,
        fairness_blocked: false,
        uses_template_only: false,
        generated_by: 'lia_claude',
      }),
    }) as unknown as typeof fetch
  })
  afterEach(() => vi.clearAllMocks())

  it('busca e injeta o texto da IA ao abrir com aiFeedbackContext', async () => {
    const { result } = renderHook(() =>
      useUnifiedCommunication({
        isOpen: true,
        onClose: vi.fn(),
        propCandidate: { id: 'c1', name: 'Maria', role: 'Dev', email: 'm@x.com', phone: '' } as never,
        type: 'feedback',
        companyId: 'co-1',
        selectedCandidates: [],
        aiFeedbackContext: { vacancyCandidateId: 'vc-1', toStage: 'rejected', subStatus: 'over_qualified' },
      }),
    )

    await waitFor(() => expect(result.current.message).toContain('Maria'))
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/backend-proxy/transition/preview-feedback',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(result.current.aiFeedbackMeta?.generatedBy).toBe('lia_claude')
  })
})
