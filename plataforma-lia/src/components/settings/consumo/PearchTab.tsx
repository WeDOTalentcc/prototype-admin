'use client'

import useSWR from 'swr'

const jsonFetcher = (url: string) => fetch(url).then(r => r.json())

interface PearchConsumption {
  company_id: string
  period_start: string
  period_end: string
  period_days: number
  total_searches: number
  successful_searches: number
  total_credits_consumed: number
  estimated_cost_brl: number
}

export function PearchTab() {
  const { data, isLoading, error } =
    useSWR<PearchConsumption>('/api/backend-proxy/consumo/pearch?days=30', jsonFetcher)

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-lia-text-tertiary">
        Carregando dados do Pearch...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-status-error">
        Erro ao carregar dados. Tente novamente.
      </div>
    )
  }

  const totalSearches = data?.total_searches ?? 0
  const creditsUsed = data?.total_credits_consumed ?? 0
  const successfulSearches = data?.successful_searches ?? 0
  const costBrl = data?.estimated_cost_brl ?? 0

  return (
    <div className="space-y-6">
      <p className="text-sm text-lia-text-tertiary">
        Créditos consumidos nas buscas globais de candidatos via Pearch.
      </p>
      <div className="grid grid-cols-2 gap-4 max-w-md">
        <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-primary p-4">
          <p className="text-xs text-lia-text-tertiary mb-1">Buscas realizadas</p>
          <p className="text-2xl font-semibold text-lia-text-primary">
            {totalSearches.toLocaleString('pt-BR')}
          </p>
          <p className="text-xs text-lia-text-disabled mt-1">Últimos 30 dias</p>
        </div>
        <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-primary p-4">
          <p className="text-xs text-lia-text-tertiary mb-1">Créditos utilizados</p>
          <p className="text-2xl font-semibold text-lia-text-primary">
            {creditsUsed.toLocaleString('pt-BR')}
          </p>
          <p className="text-xs text-lia-text-disabled mt-1">créditos</p>
        </div>
        {successfulSearches > 0 && (
          <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-primary p-4">
            <p className="text-xs text-lia-text-tertiary mb-1">Buscas bem-sucedidas</p>
            <p className="text-2xl font-semibold text-lia-text-primary">
              {successfulSearches.toLocaleString('pt-BR')}
            </p>
            <p className="text-xs text-lia-text-disabled mt-1">
              {totalSearches > 0
                ? `${Math.round((successfulSearches / totalSearches) * 100)}% de sucesso`
                : '—'}
            </p>
          </div>
        )}
        {costBrl > 0 && (
          <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-primary p-4">
            <p className="text-xs text-lia-text-tertiary mb-1">Custo estimado</p>
            <p className="text-2xl font-semibold text-lia-text-primary">
              {costBrl.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
            </p>
            <p className="text-xs text-lia-text-disabled mt-1">no período</p>
          </div>
        )}
      </div>
      {totalSearches === 0 && (
        <p className="text-sm text-lia-text-disabled">
          Nenhuma busca Pearch registrada nos últimos 30 dias.
        </p>
      )}
    </div>
  )
}
