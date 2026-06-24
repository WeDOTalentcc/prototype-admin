import { describe, it, expect } from 'vitest'
import { partitionByContactability } from '../partitionByContactability'

const base = { id: '1', name: 'Ana' }

describe('partitionByContactability', () => {
  it('coloca em sendable candidato com e-mail válido (canal email)', () => {
    const { sendable, skipped } = partitionByContactability(
      [{ ...base, email: 'ana@empresa.com' }], 'email'
    )
    expect(sendable).toHaveLength(1)
    expect(skipped).toHaveLength(0)
  })

  it('coloca em skipped candidato sem e-mail (canal email)', () => {
    const { sendable, skipped } = partitionByContactability([base], 'email')
    expect(sendable).toHaveLength(0)
    expect(skipped[0].reason).toBe('e-mail ausente')
  })

  it('coloca em skipped candidato com e-mail inválido (canal email)', () => {
    const { sendable, skipped } = partitionByContactability(
      [{ ...base, email: 'nao-e-um-email' }], 'email'
    )
    expect(skipped[0].reason).toBe('e-mail inválido')
  })

  it('coloca em skipped candidato sem telefone (canal whatsapp)', () => {
    const { sendable, skipped } = partitionByContactability(
      [{ ...base, email: 'ana@e.com' }], 'whatsapp'
    )
    expect(skipped[0].reason).toBe('telefone ausente')
  })

  it('canal both exige email E telefone', () => {
    const { sendable, skipped } = partitionByContactability(
      [{ ...base, email: 'ana@e.com' }], 'both'
    )
    expect(skipped[0].reason).toBe('telefone ausente')
  })

  it('separa corretamente lista mista', () => {
    const candidates = [
      { id: '1', name: 'Ana', email: 'ana@e.com' },
      { id: '2', name: 'Bruno' },
      { id: '3', name: 'Carla', email: 'carla@e.com' },
    ]
    const { sendable, skipped } = partitionByContactability(candidates, 'email')
    expect(sendable.map(c => c.id)).toEqual(['1', '3'])
    expect(skipped.map(s => s.item.id)).toEqual(['2'])
  })
})
