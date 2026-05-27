'use client'

import useSWR from 'swr'

const jsonFetcher = (url: string) => fetch(url).then(r => r.json())

interface AgentUsage {
  agent_type: string
  total_tokens: number
  total_cost_cents: number
  total_operations?: number
  operation_count?: number
  requests_count?: number
  total_requests?: number
  tokens_used?: number
}

function parseAgentData(raw: unknown): AgentUsage[] {
  if (!raw) return []
  if (Array.isArray(raw)) return raw as AgentUsage[]
  const r = raw as Record<string, unknown>
  return (r.data ?? r.usage_by_agent ?? []) as AgentUsage[]
}

export function PearchTab() {
  const { data: agentRaw, isLoading, error } =
    useSWR('/api/backend-proxy/ai-credits?endpoint=by-agent&days=30', jsonFetcher)

  const agents: AgentUsage[] = parseAgentData(agentRaw)
  const pearchData = agents.find((a) => a.agent_type === 'search') ?? null

  const totalSearches =
    pearchData?.requests_count ??
    pearchData?.total_requests ??
    pearchData?.total_operations ??
    pearchData?.operation_count ??
    0
  const tokensUsed =
    pearchData?.tokens_used ?? pearchData?.total_tokens ?? 0

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
          <p className="text-xs text-lia-text-disabled mt-1">Este mês</p>
        </div>
        <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-primary p-4">
          <p className="text-xs text-lia-text-tertiary mb-1">Créditos utilizados</p>
          <p className="text-2xl font-semibold text-lia-text-primary">
            {tokensUsed.toLocaleString('pt-BR')}
          </p>
          <p className="text-xs text-lia-text-disabled mt-1">tokens</p>
        </div>
      </div>
      {!pearchData && (
        <p className="text-sm text-lia-text-disabled">
          Nenhuma busca Pearch registrada este mês.
        </p>
      )}
    </div>
  )
}
