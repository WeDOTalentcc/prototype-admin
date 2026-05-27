import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { NextIntlClientProvider } from 'next-intl'
import ptBRMessages from '../../../../../messages/pt-BR.json'
import { PearchTab } from '../PearchTab'

// Mock SWR to avoid real fetch calls in tests
vi.mock('swr', () => ({
  default: vi.fn(() => ({ data: undefined, isLoading: true, error: undefined })),
}))

// Mock recharts to avoid canvas errors in jsdom
vi.mock('recharts', () => ({
  BarChart: () => null,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Cell: () => null,
  LineChart: () => null,
  Line: () => null,
  Legend: () => null,
}))

import { ConsumoHub } from '../ConsumoHub'

function renderWithIntl(ui: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="pt" messages={ptBRMessages}>
      {ui}
    </NextIntlClientProvider>
  )
}

describe('ConsumoHub', () => {
  it('renders all 4 tab triggers', () => {
    renderWithIntl(<ConsumoHub />)
    expect(screen.getByRole('tab', { name: 'Créditos IA' })).toBeTruthy()
    expect(screen.getByRole('tab', { name: 'Pearch' })).toBeTruthy()
    expect(screen.getByRole('tab', { name: 'Agentes' })).toBeTruthy()
    expect(screen.getByRole('tab', { name: 'Billing' })).toBeTruthy()
  })

  it('shows loading state for IA tab (default)', () => {
    renderWithIntl(<ConsumoHub />)
    expect(screen.getByText('Carregando dados de consumo de IA...')).toBeTruthy()
  })
})

describe('ConsumoHub — i18n canonical contract', () => {
  it('has settings.consumo.tabs.ia key in pt-BR.json', () => {
    const settings = ptBRMessages.settings as Record<string, unknown>
    const consumo = settings.consumo as Record<string, unknown>
    const tabs = consumo?.tabs as Record<string, string> | undefined
    expect(typeof tabs?.ia).toBe('string')
    expect(typeof tabs?.pearch).toBe('string')
    expect(typeof tabs?.agentes).toBe('string')
    expect(typeof tabs?.billing).toBe('string')
  })

  it('has settings.consumo.pearch keys in pt-BR.json', () => {
    const settings = ptBRMessages.settings as Record<string, unknown>
    const consumo = settings.consumo as Record<string, unknown>
    const pearch = consumo?.pearch as Record<string, string> | undefined
    for (const key of ['description', 'totalSearches', 'creditsUsed', 'thisMonth', 'tokens', 'noData']) {
      expect(typeof pearch?.[key], `pearch.${key} missing`).toBe('string')
    }
  })

  it('has settings.consumo.billing keys in pt-BR.json', () => {
    const settings = ptBRMessages.settings as Record<string, unknown>
    const consumo = settings.consumo as Record<string, unknown>
    const billing = consumo?.billing as Record<string, string> | undefined
    expect(typeof billing?.title).toBe('string')
    expect(typeof billing?.description).toBe('string')
  })
})

describe('PearchTab unit', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state when SWR is loading', () => {
    renderWithIntl(
      <NextIntlClientProvider locale="pt" messages={ptBRMessages}>
        <PearchTab />
      </NextIntlClientProvider>
    )
    expect(screen.getByText('Carregando dados do Pearch...')).toBeTruthy()
  })
})
