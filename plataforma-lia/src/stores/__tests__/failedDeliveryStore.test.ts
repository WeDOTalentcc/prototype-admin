import { describe, it, expect, beforeEach } from 'vitest'
import { useFailedDeliveryStore } from '../failedDeliveryStore'

beforeEach(() => {
  useFailedDeliveryStore.getState().clearAll()
})

describe('useFailedDeliveryStore', () => {
  it('começa vazio', () => {
    expect(Object.keys(useFailedDeliveryStore.getState().failures)).toHaveLength(0)
  })

  it('addFailure grava por candidateId', () => {
    useFailedDeliveryStore.getState().addFailure({
      candidateId: 'c1', reason: 'e-mail ausente', channel: 'email', at: 1000
    })
    expect(useFailedDeliveryStore.getState().hasFailure('c1')).toBe(true)
    expect(useFailedDeliveryStore.getState().getFailure('c1')?.reason).toBe('e-mail ausente')
  })

  it('clearFailure remove apenas o candidato alvo', () => {
    const s = useFailedDeliveryStore.getState()
    s.addFailure({ candidateId: 'c1', reason: 'x', channel: 'email', at: 1 })
    s.addFailure({ candidateId: 'c2', reason: 'y', channel: 'email', at: 2 })
    s.clearFailure('c1')
    expect(useFailedDeliveryStore.getState().hasFailure('c1')).toBe(false)
    expect(useFailedDeliveryStore.getState().hasFailure('c2')).toBe(true)
  })

  it('clearAll esvazia o store', () => {
    const s = useFailedDeliveryStore.getState()
    s.addFailure({ candidateId: 'c1', reason: 'x', channel: 'email', at: 1 })
    s.clearAll()
    expect(Object.keys(useFailedDeliveryStore.getState().failures)).toHaveLength(0)
  })
})
