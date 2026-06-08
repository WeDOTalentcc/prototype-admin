import React from 'react'
import { describe, it, expect, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import { renderEmailCell } from '../ContactCells'
import { useFailedDeliveryStore } from '@/stores/failedDeliveryStore'

const candidate = {
  id: 'c1', name: 'Ana', email: 'ana@e.com',
  source: 'local', pearch_profile_id: null, has_email: true,
} as any

beforeEach(() => useFailedDeliveryStore.getState().clearAll())

describe('renderEmailCell — delivery failure badge', () => {
  it('nao mostra badge de falha quando nao ha falha registrada', () => {
    const { container } = render(<>{renderEmailCell(candidate, {}, () => {}, undefined, undefined)}</>)
    expect(container.querySelector('[aria-label*="ltimo envio falhou"]')).toBeNull()
  })

  it('mostra badge de falha quando failedDeliveryStore tem a entry', () => {
    useFailedDeliveryStore.getState().addFailure({
      candidateId: 'c1', reason: 'e-mail invalido', channel: 'email', at: 1000
    })
    const { container } = render(<>{renderEmailCell(candidate, {}, () => {}, undefined, undefined)}</>)
    expect(container.querySelector('[aria-label*="ltimo envio falhou"]')).not.toBeNull()
  })
})
