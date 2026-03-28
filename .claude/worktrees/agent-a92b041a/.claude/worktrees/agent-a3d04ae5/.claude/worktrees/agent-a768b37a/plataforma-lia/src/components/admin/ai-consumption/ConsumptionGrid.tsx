"use client"

import React from "react"
import { Cpu, DollarSign, Activity, Zap } from "lucide-react"
import { ConsumptionSummaryCard } from "./ConsumptionSummaryCard"
import type { UsageSummary } from "@/hooks/use-ai-consumption"

export interface ConsumptionGridProps {
  summary: UsageSummary
}

export function ConsumptionGrid({ summary }: ConsumptionGridProps) {
  const formatCurrency = (value: number) => 
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <ConsumptionSummaryCard
        title="Tokens Usados"
        value={`${(summary.totalTokens / 1000).toFixed(0)}K`}
        icon={Cpu}
        progress={summary.usagePercentage}
        progressLabel={`${summary.usagePercentage.toFixed(1)}% do limite mensal`}
      />
      <ConsumptionSummaryCard
        title="Custo Estimado"
        value={formatCurrency(summary.estimatedCostBRL)}
        icon={DollarSign}
        subtitle="Baseado no consumo atual"
      />
      <ConsumptionSummaryCard
        title="Chamadas de API"
        value={summary.apiCalls.toLocaleString('pt-BR')}
        icon={Activity}
        subtitle="Este mês"
      />
      <ConsumptionSummaryCard
        title="Créditos Restantes"
        value={`${(summary.creditsRemaining / 1000).toFixed(0)}K`}
        icon={Zap}
        subtitle={`De ${(summary.monthlyLimit / 1000).toFixed(0)}K mensais`}
        valueColor={summary.creditsRemaining < 50000 ? '#ef4444' : undefined}
      />
    </div>
  )
}

export default ConsumptionGrid
