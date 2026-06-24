import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { NextIntlClientProvider } from 'next-intl'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ptBRMessages from '../../../../../messages/pt-BR.json'

// Mock next/navigation hooks used by ConsumoHub
vi.mock('next/navigation', () => ({
  useSearchParams: () => ({ get: () => null, toString: () => '' }),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => '/configuracoes/plano-e-cobranca',
}))

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

// Mock @tanstack/react-query fetch calls (billing queries return loading)
global.fetch = vi.fn(() => new Promise(() => {})) as unknown as typeof fetch

import { ConsumoHub } from '../../ConsumoHub'

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0 } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <NextIntlClientProvider locale="pt" messages={ptBRMessages}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// TDD Red: estrutura esperada após reestruturação B1
// ─────────────────────────────────────────────────────────────────────────────
describe('ConsumoHub — estrutura nova (B1)', () => {
  it('renders hub header "Plano e Cobrança"', () => {
    renderWithProviders(<ConsumoHub />)
    expect(screen.getByText('Plano e Cobrança')).toBeTruthy()
  })

  it('renders 4 new sub-tabs: plano, consumo, faturas, cobranca', () => {
    renderWithProviders(<ConsumoHub />)
    expect(screen.getByRole('tab', { name: 'Plano' })).toBeTruthy()
    expect(screen.getByRole('tab', { name: 'Consumo' })).toBeTruthy()
    expect(screen.getByRole('tab', { name: 'Faturas' })).toBeTruthy()
    expect(screen.getByRole('tab', { name: 'Cobrança' })).toBeTruthy()
  })

  it('does NOT render old tabs (Créditos IA / Pearch / Agentes / Billing)', () => {
    renderWithProviders(<ConsumoHub />)
    expect(screen.queryByRole('tab', { name: 'Créditos IA' })).toBeNull()
    expect(screen.queryByRole('tab', { name: 'Pearch' })).toBeNull()
    expect(screen.queryByRole('tab', { name: 'Agentes' })).toBeNull()
    expect(screen.queryByRole('tab', { name: 'Billing' })).toBeNull()
  })

  it('default active tab is "plano"', () => {
    renderWithProviders(<ConsumoHub />)
    const planoTab = screen.getByRole('tab', { name: 'Plano' })
    expect(planoTab.getAttribute('data-state')).toBe('active')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// i18n canonical contract
// ─────────────────────────────────────────────────────────────────────────────
describe('ConsumoHub — i18n canonical contract', () => {
  it('has settings.consumo.tabs.plano key in pt-BR.json', () => {
    const settings = ptBRMessages.settings as Record<string, unknown>
    const consumo = settings.consumo as Record<string, unknown>
    const tabs = consumo?.tabs as Record<string, string> | undefined
    expect(typeof tabs?.plano).toBe('string')
    expect(typeof tabs?.consumo).toBe('string')
    expect(typeof tabs?.faturas).toBe('string')
    expect(typeof tabs?.cobranca).toBe('string')
  })

  it('settings.consumo.sidebarLabel is "Plano e Cobrança"', () => {
    const settings = ptBRMessages.settings as Record<string, unknown>
    const consumo = settings.consumo as Record<string, unknown>
    expect(consumo?.sidebarLabel).toBe('Plano e Cobrança')
  })

  it('settings.billing has plan summary keys', () => {
    const settings = ptBRMessages.settings as Record<string, unknown>
    const billing = settings.billing as Record<string, unknown>
    for (const key of ['currentPlan', 'seats', 'usage', 'invoices', 'paymentMethod']) {
      expect(typeof billing?.[key], `billing.${key} missing`).toBe('string')
    }
  })
})
