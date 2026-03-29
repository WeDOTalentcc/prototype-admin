"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DollarSign,
  Gift,
  TrendingUp,
  CheckCircle2,
  Edit,
  Wallet,
  Percent
} from "lucide-react"

interface CompensationSummaryData {
  salary_min: number
  salary_max: number
  bonus_min?: number
  bonus_max?: number
  bonus_criteria?: string
  benefits: string[]
  total_benefits_value?: number
  currency?: string
}

interface CompensationSummaryCardProps {
  data: CompensationSummaryData
  onEdit?: () => void
  compact?: boolean
}

export function CompensationSummaryCard({
  data,
  onEdit,
  compact = false
}: CompensationSummaryCardProps) {
  const formatCurrency = (value: number, currency = "BRL") => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency,
      maximumFractionDigits: 0
    }).format(value)
  }

  const hasBonus = data.bonus_min !== undefined || data.bonus_max !== undefined

  return (
    <Card
      className="w-full max-w-md border-l-4 overflow-hidden bg-lia-bg-secondary"
      style={{borderLeftColor: 'var(--lia-border-default)'}}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div
              className="h-10 w-10 rounded-full flex items-center justify-center bg-lia-bg-tertiary"
            >
              <Wallet className="h-5 w-5 text-gray-700 dark:text-gray-300" />
            </div>
            <div>
              <div className="text-sm font-medium text-lia-text-primary">
                Pacote de Remuneração
              </div>
              <div className="text-xs text-lia-text-tertiary">
                Resumo configurado
              </div>
            </div>
          </div>
          {onEdit && (
            <Button
              size="sm"
              variant="ghost"
              className="text-lia-text-secondary"
              onClick={onEdit}
            >
              <Edit className="h-4 w-4" />
            </Button>
          )}
        </div>

        <div className="space-y-4">
          <div
            className="p-3 rounded-md border bg-lia-bg-primary border-lia-border-subtle"
          >
            <div className="flex items-center gap-2 text-sm mb-1 text-lia-text-tertiary">
              <DollarSign className="h-4 w-4 text-gray-700 dark:text-gray-300" />
              Salário Base (CLT)
            </div>
            <div className="text-lg font-semibold text-lia-text-primary">
              {formatCurrency(data.salary_min)} - {formatCurrency(data.salary_max)}
            </div>
          </div>

          {hasBonus && (
            <div
              className="p-3 rounded-md border bg-lia-bg-primary border-lia-border-subtle"
            >
              <div className="flex items-center gap-2 text-sm mb-1 text-lia-text-tertiary">
                <TrendingUp className="h-4 w-4 text-wedo-green" />
                Bônus / Variável
              </div>
              <div className="text-lg font-semibold text-lia-text-primary">
                {data.bonus_min !== undefined && data.bonus_max !== undefined
                  ? `${formatCurrency(data.bonus_min)} - ${formatCurrency(data.bonus_max)}`
                  : data.bonus_min !== undefined
                  ? formatCurrency(data.bonus_min)
                  : formatCurrency(data.bonus_max!)}
              </div>
              {data.bonus_criteria && (
                <div className="text-xs mt-1 text-lia-text-tertiary">
                  {data.bonus_criteria}
                </div>
              )}
            </div>
          )}

          {data.benefits && data.benefits.length > 0 && (
            <div
              className="p-3 rounded-md border bg-lia-bg-primary border-lia-border-subtle"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-sm text-lia-text-tertiary">
                  <Gift className="h-4 w-4" />
                  Benefícios
                </div>
                <Badge
                  variant="secondary"
                  className="text-xs bg-lia-bg-tertiary text-lia-text-secondary"
                >
                  {data.benefits.length} itens
                </Badge>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {data.benefits.slice(0, compact ? 4 : 8).map((benefit, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-1 text-xs px-2 py-1 rounded-md bg-lia-bg-tertiary text-lia-text-secondary"
                  >
                    <CheckCircle2 className="h-3 w-3 text-wedo-green" />
                    {benefit}
                  </div>
                ))}
                {data.benefits.length > (compact ? 4 : 8) && (
                  <Badge
                    variant="outline"
                    className="text-xs border-lia-border-subtle text-lia-text-tertiary"
                  >
                    +{data.benefits.length - (compact ? 4 : 8)}
                  </Badge>
                )}
              </div>
            </div>
          )}

          {data.total_benefits_value !== undefined && !compact && (
            <div
              className="flex items-center justify-between p-3 rounded-md bg-lia-bg-tertiary"
            >
              <span className="text-sm text-lia-text-secondary">
                Valor Estimado Total (Benefícios)
              </span>
              <span className="font-semibold text-lia-text-primary">
                {formatCurrency(data.total_benefits_value)}/mês
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
