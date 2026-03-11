"use client"

import React from "react"
import { useParams } from "next/navigation"
import { useAIConsumption } from "@/hooks/use-ai-consumption"
import { 
  ConsumptionGrid, 
  ConsumptionChart, 
  AgentBreakdown 
} from "@/components/admin/ai-consumption"
import { AlertCircle } from "lucide-react"

export default function ConsumoIAPage() {
  const params = useParams()
  const clientId = params.clientId as string
  const { summary, dailyUsage, agentUsage, isLoading, error, refetch } = useAIConsumption({
    clientId,
    autoFetch: true
  })

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-gray-100 rounded-md animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-64 bg-gray-100 rounded-md animate-pulse" />
          <div className="h-64 bg-gray-100 rounded-md animate-pulse" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-md">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <div>
            <p className="font-medium text-red-800">Erro ao carregar dados</p>
            <p className="text-sm text-red-600">{error}</p>
          </div>
          <button
            onClick={() => refetch()}
            className="ml-auto px-3 py-1 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="p-6">
        <p style={{ color: 'var(--eleven-text-tertiary)' }}>Nenhum dado disponível</p>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-lg font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
          Consumo de IA
        </h2>
        <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
          Acompanhe o uso de tokens e créditos de IA deste cliente
        </p>
      </div>

      <ConsumptionGrid summary={summary} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ConsumptionChart data={dailyUsage} />
        <AgentBreakdown agents={agentUsage} />
      </div>
    </div>
  )
}
