import { describe, it, expect, vi } from 'vitest'
import { runBulkSequential } from '../runBulkSequential'

const items = [
  { id: '1', name: 'Ana' },
  { id: '2', name: 'Bruno' },
  { id: '3', name: 'Carla' },
]

describe('runBulkSequential', () => {
  it('retorna ok=true para cada item bem-sucedido', async () => {
    const action = vi.fn().mockResolvedValue({ sent: true })
    const results = await runBulkSequential(items, action)
    expect(results).toHaveLength(3)
    expect(results.every(r => r.ok)).toBe(true)
    expect(action).toHaveBeenCalledTimes(3)
  })

  it('retorna ok=false com reason para item que lança erro', async () => {
    const action = vi.fn()
      .mockResolvedValueOnce({ sent: true })
      .mockRejectedValueOnce(new Error('e-mail inválido'))
      .mockResolvedValueOnce({ sent: true })
    const results = await runBulkSequential(items, action)
    expect(results[0].ok).toBe(true)
    expect(results[1].ok).toBe(false)
    expect(results[1].reason).toBe('e-mail inválido')
    expect(results[2].ok).toBe(true)
  })

  it('chama onTick para cada item processado', async () => {
    const action = vi.fn().mockResolvedValue({})
    const ticks: number[] = []
    await runBulkSequential(items, action, (done) => ticks.push(done))
    expect(ticks).toEqual([1, 2, 3])
  })

  it('retorna array vazio para lista vazia', async () => {
    const action = vi.fn()
    const results = await runBulkSequential([], action)
    expect(results).toEqual([])
    expect(action).not.toHaveBeenCalled()
  })

  it('inclui id e name em cada resultado', async () => {
    const action = vi.fn().mockResolvedValue({})
    const results = await runBulkSequential([items[0]], action)
    expect(results[0].id).toBe('1')
    expect(results[0].name).toBe('Ana')
  })

  it('passa o resultado correto como terceiro arg do onTick', async () => {
    const action = vi.fn()
      .mockResolvedValueOnce({ a: 1 })
      .mockRejectedValueOnce(new Error('falhou'))
    const latests: unknown[] = []
    await runBulkSequential(
      [{ id: '1', name: 'Ana' }, { id: '2', name: 'Bruno' }],
      action,
      (_, __, latest) => latests.push(latest)
    )
    expect(latests[0]).toMatchObject({ id: '1', ok: true })
    expect(latests[1]).toMatchObject({ id: '2', ok: false, reason: 'falhou' })
  })

  it('serializa rejeição não-Error como JSON', async () => {
    const action = vi.fn().mockRejectedValueOnce({ code: 404, msg: 'not found' })
    const results = await runBulkSequential([{ id: '1', name: 'Ana' }], action)
    expect(results[0].ok).toBe(false)
    expect(results[0].reason).toContain('404')
  })
})
