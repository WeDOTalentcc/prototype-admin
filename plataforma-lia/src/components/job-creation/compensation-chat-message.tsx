"use client"


import { CURRENCY_SYMBOL } from"@/lib/pricing"
import React, { useState } from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { cn } from"@/lib/utils"
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
} from"lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import type { 
  CompensationAnalysisResult, 
  SalaryRange, 
  CompetitivenessStatus,
  DataSource
} from"./compensation-analysis-panel"

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
    className: 'text-status-success',
    bgClassName: 'bg-status-success/10 dark:bg-status-success/30',
    borderClassName: 'border-status-success/30 dark:border-status-success/30'
  },
  below_market: {
    icon: AlertTriangle,
    label: 'Abaixo do Mercado',
    description: 'Pode dificultar atração de talentos',
    className: 'text-status-warning',
    bgClassName: 'bg-status-warning/10 dark:bg-status-warning/30',
    borderClassName: 'border-status-warning/30 dark:border-status-warning/30'
  },
  above_market: {
    icon: TrendingUp,
    label: 'Acima do Mercado',
    description: 'Remuneração acima da média',
    className: 'text-wedo-cyan-text',
    bgClassName: 'bg-wedo-cyan/10',
    borderClassName: 'border-wedo-cyan/30 dark:border-wedo-cyan/30'
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
        <div className="absolute inset-x-0 top-2.5 h-1 bg-lia-interactive-active rounded-full" />
        
        <div 
          className="absolute top-2.5 h-1 bg-lia-border-medium rounded-full"
          style={{left: `${getPosition(market.min)}%`,
            width: `${getPosition(market.max) - getPosition(market.min)}%`}}
        />
        
        <div 
          className="absolute top-2 h-2 bg-status-success dark:bg-status-success rounded-full"
          style={{left: `${getPosition(proposed.min)}%`,
            width: `${getPosition(proposed.max) - getPosition(proposed.min)}%`}}
        />

        <div 
          className="absolute top-0 w-0.5 h-6 bg-lia-btn-primary-bg"
          style={{left: `${percentile}%`}}
        >
          <div className="absolute -top-5 left-1/2 -translate-x-1/2 text-micro font-medium text-lia-text-secondary whitespace-nowrap">
            P{percentile}
          </div>
        </div>
      </div>
      
      <div className="flex justify-between text-micro text-lia-text-tertiary">
        <div className="flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-status-success" />
          <span>Proposto</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-lia-border-medium" />
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
        <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-lia-border-default">
          <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
          <AvatarFallback className="bg-gradient-to-br from-lia-bg-tertiary dark:from-lia-bg-tertiary to-wedo-cyan-dark text-white text-xs font-medium">
            LIA
          </AvatarFallback>
        </Avatar>
        <div className="rounded-xl rounded-tl-sm bg-lia-bg-primary border border-lia-border-subtle p-4" role="status" aria-live="polite" aria-label="Carregando...">
          <div className="flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            <span className="text-sm text-lia-text-tertiary">Analisando remuneração...</span>
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
      <Avatar className="h-8 w-8 flex-shrink-0 border-2 border-lia-border-default">
        <AvatarImage src="/images/lia-avatar.png" alt="LIA" />
        <AvatarFallback className="bg-gradient-to-br from-lia-bg-tertiary dark:from-lia-bg-tertiary to-wedo-cyan-dark text-white text-xs font-medium">
          LIA
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 space-y-3">
        <div className="rounded-xl rounded-tl-sm bg-lia-bg-primary border border-lia-border-subtle p-4 space-y-4">
          <div className={cn("flex items-center gap-2 p-2 rounded-md border",
            statusConfig.bgClassName,
            statusConfig.borderClassName
          )}>
            <StatusIcon className={cn("h-4 w-4", statusConfig.className)} />
            <div className="flex-1 min-w-0">
              <p className={cn("text-xs font-medium", statusConfig.className)}>
                {statusConfig.label}
              </p>
              <p className="text-micro text-lia-text-tertiary truncate">
                {statusConfig.description}
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-1.5 text-xs font-medium text-lia-text-tertiary">
              <DollarSign className="h-3.5 w-3.5" />
              <span>Comparação Salarial</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-xl bg-status-success/10 dark:bg-status-success/30 border border-status-success/30 dark:border-status-success/30">
                <p className="text-micro text-lia-text-tertiary mb-0.5">Proposto</p>
                <p className="text-xs font-semibold text-status-success">
                  {formatCurrency(analysis.salary.proposed.min)} - {formatCurrency(analysis.salary.proposed.max)}
                </p>
              </div>
              <div className="p-2.5 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
                <p className="text-micro text-lia-text-tertiary mb-0.5">Mercado</p>
                <p className="text-xs font-semibold text-lia-text-secondary">
                  {formatCurrency(analysis.salary.market.min)} - {formatCurrency(analysis.salary.market.max)}
                </p>
              </div>
            </div>

            <MiniSalaryBar 
              proposed={analysis.salary.proposed}
              market={analysis.salary.market}
              percentile={analysis.salary.percentileVsMarket}
            />

            <div className="flex items-center justify-between text-xs px-1">
              <span className="text-lia-text-tertiary">Posição no mercado:</span>
              <Chip 
                variant="neutral" 
                className={cn("text-micro h-5",
                  analysis.salary.percentileVsMarket >= 50 
                    ?"border-status-success/30  dark:border-status-success/30 dark:bg-status-success/30"
                    :"border-status-warning/30  dark:border-status-warning/30 dark:bg-status-warning/30"
                )}
              >
                Percentil {analysis.salary.percentileVsMarket}
              </Chip>
            </div>

            {analysis.salary.suggestion && (
              <div className="p-2 rounded-xl bg-status-warning/10 dark:bg-status-warning/30 border border-status-warning/30 dark:border-status-warning/30 flex items-start gap-2">
                <AlertTriangle className="h-3.5 w-3.5 text-status-warning flex-shrink-0 mt-0.5" />
                <p className="text-micro text-status-warning">
                  <span className="font-medium">Sugestão:</span> Considere ajustar para {formatCurrency(analysis.salary.suggestion.min)} - {formatCurrency(analysis.salary.suggestion.max)} para melhor competitividade.
                </p>
              </div>
            )}
          </div>

          <p className="text-xs text-lia-text-tertiary border-t pt-3">
            {analysis.executiveSummary}
          </p>

          <div className="flex flex-wrap gap-2 pt-1">
            {(analysis.salary.suggestion || analysis.bonus.suggestion || (analysis.benefits.missingFromStandard && analysis.benefits.missingFromStandard.length > 0)) ? (
              <Button 
                size="sm" 
                className="h-8 text-xs bg-gradient-to-r from-lia-bg-tertiary dark:from-lia-bg-tertiary to-wedo-cyan-dark hover:from-wedo-cyan-dark hover:to-wedo-cyan text-white"
                onClick={onConfirm}
              >
                <Brain className="h-3.5 w-3.5 mr-1.5 text-wedo-cyan" />
                Aplicar Sugestões LIA
              </Button>
            ) : (
              <Button 
                size="sm" 
                className="h-8 text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
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
                placeholder={`Ex: ${CURRENCY_SYMBOL} 15.000 a ${CURRENCY_SYMBOL} 18.000`}
                value={salaryInput}
                onChange={(e) => setSalaryInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="h-9 text-sm"
                autoFocus
              />
              <Button 
                size="sm" 
                className="h-9 px-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
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
