import { renderHook } from '@testing-library/react'
import { vi, it, expect, describe, beforeEach } from 'vitest'

const mockOpenWithEntity = vi.fn()
vi.mock('@/contexts/lia-float-context', () => ({
  useLiaFloat: () => ({ openWithEntity: mockOpenWithEntity }),
}))

describe('useLiaEntitySelection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls openWithEntity with candidate entity', async () => {
    const { useLiaEntitySelection } = await import('../use-lia-entity-selection')
    const { result } = renderHook(() => useLiaEntitySelection())

    result.current.openEntityChat({ type: 'candidate', id: 'cand-123', name: 'João Silva' })

    expect(mockOpenWithEntity).toHaveBeenCalledWith({
      type: 'candidate',
      id: 'cand-123',
      name: 'João Silva',
      meta: undefined,
    })
  })

  it('calls openWithEntity with job entity', async () => {
    const { useLiaEntitySelection } = await import('../use-lia-entity-selection')
    const { result } = renderHook(() => useLiaEntitySelection())

    result.current.openEntityChat({ type: 'job', id: 'job-456', name: 'Desenvolvedor Sênior' })

    expect(mockOpenWithEntity).toHaveBeenCalledWith({
      type: 'job',
      id: 'job-456',
      name: 'Desenvolvedor Sênior',
      meta: undefined,
    })
  })

  it('passes meta when provided', async () => {
    const { useLiaEntitySelection } = await import('../use-lia-entity-selection')
    const { result } = renderHook(() => useLiaEntitySelection())
    const meta = { stage: 'entrevista', score: 0.9 }

    result.current.openEntityChat({ type: 'candidate', id: 'cand-789', name: 'Maria', meta })

    expect(mockOpenWithEntity).toHaveBeenCalledWith({
      type: 'candidate',
      id: 'cand-789',
      name: 'Maria',
      meta,
    })
  })
})
