import React from 'react'
import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { renderSourceCell } from '../SourceCell'

const localCand = { id: 'c1', name: 'Ana', source: 'local', pearch_profile_id: null } as any
const globalCand = { id: 'c2', name: 'Bob', source: 'pearch', pearch_profile_id: 'p1' } as any

describe('renderSourceCell — tooltip (Radix primitive, escapes overflow clipping)', () => {
  it('renderiza icone para fonte local dentro de um trigger Radix', () => {
    const { container } = render(<>{renderSourceCell(localCand)}</>)
    const cell = container.querySelector('[data-testid="source-cell"]')
    expect(cell).not.toBeNull()
    expect(cell?.querySelector('svg')).not.toBeNull()
    // asChild Radix Trigger injeta data-state no elemento — prova que usa o primitivo
    expect(cell?.getAttribute('data-state')).not.toBeNull()
  })

  it('renderiza icone para fonte global dentro de um trigger Radix', () => {
    const { container } = render(<>{renderSourceCell(globalCand)}</>)
    const cell = container.querySelector('[data-testid="source-cell"]')
    expect(cell).not.toBeNull()
    expect(cell?.querySelector('svg')).not.toBeNull()
    expect(cell?.getAttribute('data-state')).not.toBeNull()
  })

  it('NAO renderiza o conteudo do tooltip in-flow quando fechado (regressao: tooltip clipado por overflow)', () => {
    // O tooltip hand-rolled antigo ficava SEMPRE no DOM (apenas escondido via group-hover),
    // e era cortado pelo overflow do container da tabela. O primitivo Radix monta o
    // conteudo sob demanda (fixed/portal), entao o texto NAO esta no DOM enquanto fechado.
    const { container } = render(<>{renderSourceCell(localCand)}</>)
    expect(container.textContent).not.toContain('Base Local')
  })
})
