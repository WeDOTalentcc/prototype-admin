"use client"

import React, { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { 
  DollarSign, 
  TrendingUp, 
  Check,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Send,
  PenLine,
  Brain
} from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import type { 
  CompensationAnalysisResult, 
  SalaryRange, 
  CompetitivenessStatus,
  DataSource
} from "./compensation-analysis-panel"

export interface CompensationChatMessageProps {
  analysis: CompensationAnalysisResult | null
  isLoading?: boolean
  onConfirm: () => void
  onAdjust: () => void
  onSuggestNewValue: (value: string) => void
}

const STATUS_CONFIG: Record<CompetitivenessStatus, {
  icon: React.ElementType
  label: string
  description: string
  className: string
  bgClassName: string
  borderClassName: string
}> = {
  competitive: {
    icon: CheckCircle2,
    label: 'Competitivo',
    description: 'Remuneração alinhada com o mercado',
    className: 'text-green-600 dark:text-green-400',
    bgClassName: 'bg-green-50 dark:bg-green-950/30',
    borderClassName: 'border-green-200 dark:border-green-800'
  },
  below_market: {
    icon: AlertTriangle,
    label: 'Abaixo do Mercado',
    description: 'Pode dificultar atração de talentos',
    className: 'text-amber-600 dark:text-amber-400',
    bgClassName: 'bg-amber-50 dark:bg-amber-950/30',
    borderClassName: 'border-amber-200 dark:border-amber-800'
  },
  above_market: {
    icon: TrendingUp,
    label: 'Acima do Mercado',
    description: 'Remuneração acima da média',
    className: 'text-blue-600 dark:text-blue-400',
    bgClassName: 'bg-blue-50 dark:bg-blue-950/30',
    borderClassName: 'border-blue-200 dark:border-blue-800'
  }
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

function MiniSalaryBar({ 
  proposed, 
  market,
  percentile
}: { 
  proposed: SalaryRange
  market: SalaryRange
  percentile: number
}) {
  const allValues = [proposed.min, proposed.max, market.min, market.max]
  const minValue = Math.min(...allValues) * 0.85
  const maxValue = Math.max(...allValues) * 1.15
  const range = maxValue - minValue

  const getPosition = (value: number) => ((value - minValue) / range) * 100
  
  const proposedMid = (proposed.min + proposed.max) / 2
  const marketMid = (market.min + market.max) / 2

  return (
    <div className="space-y-2">
      <div className="relative h-6">
        <div className="absolute inset-x-0 top-2.5 h-1 bg-gray-200 dark:bg-gray-700 rounded-full" />
        
        <div 
          className="absolute top-2.5 h-1 bg-gray-400 dark:bg-gray-500 rounded-full"
          style={{
            left: `${getPosition(market.min)}%`,
            width: `${getPosition(market.max) - getPosition(market.min)}%`
          }}
        />
        
        <div 
          className="absolute top-2 h-2 bg-green-500 dark:bg-green-600 rounded-full"
          style={{
            left: `${getPosition(proposed.min)}%`,
            width: `${getPosition(proposed.max) - getPosition(proposed.min)}%`
          }}
        />

        <div 
          className="absolute top-0 w-0.5 h-6 bg-gray-900 dark:bg-gray-50"
          style={{ left: `${percentile}%` }}
        >
          <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-[9px] font-medium text-gray-600 dark:text-gray-400 whitespace-nowrap">
            P{percentile}
          </div>
        </div>
      </div>
      
      <div className="flex justify-between text-[9px] text-muted-foreground">
        <div className="flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
          <span>Proposto</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-gray-400" />
          <span>Mercado</span>
        </div>
      </div>
    </div>
  )
}

export function CompensationChatMessage({
  analysis,
  isLoading = false,
  onConfirm,
  onAdjust,
  onSuggestNewValue
}: CompensationChatMessageProps) {
  const [salaryInput, setSalaryInput] = useState("")
  const [showInput, setShowInput] = useState(false)

  const handleSubmitSuggestion = () => {
    if (salaryInput.trim()) {
      onSuggestNewValue(salaryInput.trim())
      setSalaryInput("")
      setShowInput(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmitSuggestion()
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-start gap-3 max-w-[85%]">
        <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-gray-300 dark:border-gray-600">
          <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
          <AvatarFallback className="bg-gradient-to-br from-gray-100 dark:from-gray-800 to-[#4FA3B4] text-white text-xs font-medium">
            LIA
          </AvatarFallback>
        </Avatar>
        <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-gray-600 dark:text-gray-400" />
            <span className="text-sm text-muted-foreground">Analisando remuneração...</span>
          </div>
        </div>
      </div>
    )
  }

  if (!analysis) return null

  const statusConfig = STATUS_CONFIG[analysis.overallStatus]
  const StatusIcon = statusConfig.icon

  return (
    <div className="flex items-start gap-3 max-w-[90%]">
      <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-gray-300 dark:border-gray-600">
        <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
        <AvatarFallback className="bg-gradient-to-br from-gray-100 dark:from-gray-800 to-[#4FA3B4] text-white text-xs font-medium">
          LIA
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 space-y-3">
        <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4 space-y-4">
          <div className={cn(
            "flex items-center gap-2 p-2 rounded-md border",
            statusConfig.bgClassName,
            statusConfig.borderClassName
          )}>
            <StatusIcon className={cn("h-4 w-4", statusConfig.className)} />
            <div className="flex-1 min-w-0">
              <p className={cn("text-xs font-medium", statusConfig.className)}>
                {statusConfig.label}
              </p>
              <p className="text-[10px] text-muted-foreground truncate">
                {statusConfig.description}
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
              <DollarSign className="h-3.5 w-3.5" />
              <span>Comparação Salarial</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-md bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800">
                <p className="text-[10px] text-muted-foreground mb-0.5">Proposto</p>
                <p className="text-xs font-semibold text-green-700 dark:text-green-400">
                  {formatCurrency(analysis.salary.proposed.min)} - {formatCurrency(analysis.salary.proposed.max)}
                </p>
              </div>
              <div className="p-2.5 rounded-md bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
                <p className="text-[10px] text-muted-foreground mb-0.5">Mercado</p>
                <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                  {formatCurrency(analysis.salary.market.min)} - {formatCurrency(analysis.salary.market.max)}
                </p>
              </div>
            </div>

            <MiniSalaryBar 
              proposed={analysis.salary.proposed}
              market={analysis.salary.market}
              percentile={analysis.salary.percentileVsMarket}
            />

            <div className="flex items-center justify-between text-[11px] px-1">
              <span className="text-muted-foreground">Posição no mercado:</span>
              <Badge 
                variant="outline" 
                className={cn(
                  "text-[10px] h-5",
                  analysis.salary.percentileVsMarket >= 50 
                    ? "border-green-300 bg-green-50 text-green-700 dark:border-green-700 dark:bg-green-950/30 dark:text-green-400"
                    : "border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-700 dark:bg-amber-950/30 dark:text-amber-400"
                )}
              >
                Percentil {analysis.salary.percentileVsMarket}
              </Badge>
            </div>

            {analysis.salary.suggestion && (
              <div className="p-2 rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 flex items-start gap-2">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
                <p className="text-[10px] text-amber-700 dark:text-amber-400">
                  <span className="font-medium">Sugestão:</span> Considere ajustar para {formatCurrency(analysis.salary.suggestion.min)} - {formatCurrency(analysis.salary.suggestion.max)} para melhor competitividade.
                </p>
              </div>
            )}
          </div>

          <p className="text-xs text-muted-foreground border-t pt-3">
            {analysis.executiveSummary}
          </p>

          <div className="flex flex-wrap gap-2 pt-1">
            {(analysis.salary.suggestion || analysis.bonus.suggestion || (analysis.benefits.missingFromStandard && analysis.benefits.missingFromStandard.length > 0)) ? (
              <Button 
                size="sm" 
                className="h-8 text-xs bg-gradient-to-r from-gray-100 dark:from-gray-800 to-[#4FA3B4] hover:from-[#4FA3B4] hover:to-[#3E8F9F] text-white"
                onClick={onConfirm}
              >
                <Brain className="h-3.5 w-3.5 mr-1.5 text-wedo-cyan" />
                Aplicar Sugestões LIA
              </Button>
            ) : (
              <Button 
                size="sm" 
                className="h-8 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                onClick={onConfirm}
              >
                <Check className="h-3.5 w-3.5 mr-1.5" />
                Confirmar valores
              </Button>
            )}
            <Button 
              variant="outline" 
              size="sm" 
              className="h-8 text-xs"
              onClick={() => setShowInput(!showInput)}
            >
              <PenLine className="h-3.5 w-3.5 mr-1.5" />
              Ajustar salário
            </Button>
          </div>

          {showInput && (
            <div className="flex gap-2 pt-2 border-t">
              <Input
                placeholder="Ex: R$ 15.000 a R$ 18.000"
                value={salaryInput}
                onChange={(e) => setSalaryInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="h-9 text-sm"
                autoFocus
              />
              <Button 
                size="sm" 
                className="h-9 px-3 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                onClick={handleSubmitSuggestion}
                disabled={!salaryInput.trim()}
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default CompensationChatMessage
