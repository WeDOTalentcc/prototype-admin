import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { NextIntlClientProvider } from 'next-intl'
import { BulkResultReport } from '../BulkResultReport'
import type { BulkItemResult } from '@/lib/bulk'

const MESSAGES = {
  bulkReport: {
    title: "{succeeded} de {total} enviados",
    closeButton: "Fechar",
    copyFailed: "Copiar lista de falhas",
    deliveryFailed: "Último envio falhou: {reason}",
  },
}

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <NextIntlClientProvider locale="pt" messages={MESSAGES}>
      {children}
    </NextIntlClientProvider>
  )
}

const results: BulkItemResult[] = [
  { id: '1', name: 'Ana Souza', ok: true },
  { id: '2', name: 'Bruno Lima', ok: true },
  { id: '3', name: 'Carla Dias', ok: false, reason: 'e-mail ausente' },
]

describe('BulkResultReport', () => {
  it('exibe contagem de sucessos no título', () => {
    render(
      <BulkResultReport isOpen onClose={vi.fn()} results={results} actionLabel="Email" />,
      { wrapper: Wrapper }
    )
    expect(screen.getByText(/2 de 3/)).toBeInTheDocument()
  })

  it('exibe o nome de cada candidato', () => {
    render(
      <BulkResultReport isOpen onClose={vi.fn()} results={results} actionLabel="Email" />,
      { wrapper: Wrapper }
    )
    expect(screen.getByText('Ana Souza')).toBeInTheDocument()
    expect(screen.getByText('Carla Dias')).toBeInTheDocument()
  })

  it('exibe motivo da falha para item ok=false', () => {
    render(
      <BulkResultReport isOpen onClose={vi.fn()} results={results} actionLabel="Email" />,
      { wrapper: Wrapper }
    )
    expect(screen.getByText('e-mail ausente')).toBeInTheDocument()
  })

  it('chama onClose ao clicar em Fechar', () => {
    const onClose = vi.fn()
    render(
      <BulkResultReport isOpen onClose={onClose} results={results} actionLabel="Email" />,
      { wrapper: Wrapper }
    )
    fireEvent.click(screen.getByRole('button', { name: /fechar/i }))
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('não renderiza quando isOpen=false', () => {
    const { container } = render(
      <BulkResultReport isOpen={false} onClose={vi.fn()} results={results} actionLabel="Email" />,
      { wrapper: Wrapper }
    )
    expect(container).toBeEmptyDOMElement()
  })
})
