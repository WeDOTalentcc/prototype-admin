import { describe, it, expect } from 'vitest'
import { formatDate, formatRelativeTime, formatFileSize } from '../format-utils'

// Lock de regressão: o card do candidato exibia "Gerado pela LIA em Invalid Date"
// porque `new Date(x).toLocaleDateString()` retorna a string literal "Invalid Date"
// (sem lançar) para entradas inválidas, e o try/catch não pegava. Estes testes
// fixam o contrato: NUNCA emitir "Invalid Date".

describe('formatDate', () => {
  const invalidInputs: Array<string | number | Date | null | undefined> = [
    undefined,
    null,
    '',
    'garbage',
    'not-a-date',
    NaN,
    new Date('invalid'),
  ]

  it('retorna string vazia para entradas inválidas/ausentes', () => {
    for (const input of invalidInputs) {
      expect(formatDate(input)).toBe('')
    }
  })

  it('NUNCA retorna a string "Invalid Date"', () => {
    for (const input of invalidInputs) {
      expect(formatDate(input)).not.toContain('Invalid Date')
    }
  })

  it('formata uma data ISO válida em dd/mm/aaaa por padrão', () => {
    const out = formatDate('2026-06-05T14:23:45.000Z')
    expect(out).toMatch(/^\d{2}\/\d{2}\/\d{4}$/)
    expect(out).not.toContain('Invalid Date')
  })

  it('aceita um objeto Date válido', () => {
    const out = formatDate(new Date('2026-01-15T00:00:00.000Z'))
    expect(out).toMatch(/^\d{2}\/\d{2}\/\d{4}$/)
  })

  it('respeita opções de formato customizadas', () => {
    const out = formatDate('2026-06-05T00:00:00.000Z', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
    expect(out).not.toContain('Invalid Date')
    expect(out.length).toBeGreaterThan(0)
  })
})

describe('formatRelativeTime', () => {
  it('retorna string vazia para entradas inválidas e nunca "Invalid Date"', () => {
    for (const input of [undefined, null, '', 'garbage'] as Array<string | null | undefined>) {
      const out = formatRelativeTime(input)
      expect(out).toBe('')
      expect(out).not.toContain('Invalid Date')
    }
  })

  it('formata datas antigas sem emitir "Invalid Date"', () => {
    const out = formatRelativeTime('2020-01-01T00:00:00.000Z')
    expect(out).not.toContain('Invalid Date')
    expect(out.length).toBeGreaterThan(0)
  })
})

describe('formatFileSize', () => {
  it('formata bytes e trata zero/NaN', () => {
    expect(formatFileSize(0)).toBe('0 B')
    expect(formatFileSize(NaN)).toBe('0 B')
    expect(formatFileSize(1024)).toBe('1 KB')
  })
})
