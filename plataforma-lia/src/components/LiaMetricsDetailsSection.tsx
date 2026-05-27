"use client"

import React from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  TrendingUp, Clock, Users, Target, CheckCircle,
  Phone, Calendar, Award, Zap, AlertCircle
} from"lucide-react"
import { textStyles } from"@/lib/design-tokens"
import type { LiaMetricsData } from"@/hooks/ai/use-lia-metrics-data"

const statusIcons: Record<string, React.ReactNode> = {
  'Contato Inicial': <Phone className="w-4 h-4" />,
  'Triagem Iniciada': <Target className="w-4 h-4" />,
  'Triagem Completa': <CheckCircle className="w-4 h-4" />,
  'Triagem Aprovada': <Award className="w-4 h-4" />,
  'Entrevista Agendada': <Calendar className="w-4 h-4" />,
  'Reprovado': <AlertCircle className="w-4 h-4" />,
}

interface LiaMetricsDetailsSectionProps {
  data: LiaMetricsData
}

export function LiaMetricsDetailsSection({ data }: LiaMetricsDetailsSectionProps) {
  const {
    pendingApproval, sourceMetrics, candidateStatusBreakdown,
    contactRate, triageConversionRate, avgTimeContact,
  } = data

  return (
    <>
      {pendingApproval > 0 && (
        <Card className="bg-wedo-orange/10">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-wedo-orange/20 rounded-md flex items-center justify-center">
                  <AlertCircle className="w-4 h-4 text-wedo-orange" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-wedo-orange">
                    {pendingApproval} Ações Pendentes
                  </div>
                  <div className="text-xs text-wedo-orange/80">
                    Aguardando aprovação para contato ou próximo passo
                  </div>
                </div>
              </div>
              <Button size="sm" className="bg-wedo-orange hover:bg-wedo-orange/90 text-white">
                <Zap className="w-3 h-3 mr-1" />
                Revisar Agora
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
            <Users className="w-4 h-4 text-lia-text-primary" />
            Performance por Fonte
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {sourceMetrics.map((source) => (
              <div key={source.source} className="flex items-center gap-2">
                <div className="w-6 h-6 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl flex items-center justify-center">
                  <Users className="w-3 h-3 text-lia-text-secondary" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-medium text-lia-text-primary">{source.source}</span>
                    <div className="flex items-center gap-2">
                      <Chip density="relaxed" variant="neutral" className="px-1 py-0">
                        {source.count} cand.
                      </Chip>
                      <Chip variant="neutral" muted className={`text-xs px-1 py-0 ${
                        source.conversionRate >= 70 ? 'bg-status-success' :
                        source.conversionRate >= 50 ? 'bg-status-warning' :
                        'bg-status-error'
                      } text-white`}>
                        {source.conversionRate.toFixed(0)}%
                      </Chip>
                    </div>
                  </div>
                  <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-1">
                    <div
                      className={`h-1 rounded-full ${
                        source.conversionRate >= 70 ? 'bg-status-success' :
                        source.conversionRate >= 50 ? 'bg-status-warning' :
                        'bg-status-error'
                      }`}
                      style={{width: `${source.conversionRate}%`}}
                    />
                  </div>
                </div>
                <div className={textStyles.bodySmall}>
                  Score: {source.avgScore.toFixed(1)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
        {candidateStatusBreakdown.map((status) => (
          <Card key={status.status}>
            <CardContent className="p-2">
              <div className="flex items-center justify-between mb-1">
                {statusIcons[status.status] ?? <AlertCircle className="w-4 h-4" />}
                <span className="text-xs font-bold text-lia-text-primary">
                  {status.count}
                </span>
              </div>
              <div className={`${textStyles.bodySmall} truncate`}>
                {status.status}
              </div>
              <div className={textStyles.bodySmall}>
                {status.percentage.toFixed(0)}% do total
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
            <TrendingUp className="w-4 h-4 text-wedo-purple" />
            Insights IA
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <div className={`p-3 rounded-md ${
              contactRate >= 80 ? 'bg-status-success/10' :
              contactRate >= 60 ? 'bg-status-warning/10' :
              'bg-status-error/10'
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <Phone className="w-3 h-3 text-lia-text-secondary" />
                <span className="text-xs font-semibold text-lia-text-primary">
                  Taxa de Contato
                </span>
              </div>
              <p className="text-xs text-lia-text-primary">
                {contactRate >= 80 ?
                  '✅ Excelente! Continue assim.' :
                  contactRate >= 60 ?
                  '⚠️ Pode melhorar. Tente contatos em horários alternativos.' :
                  '❌ Baixa. Considere múltiplos canais de contato.'
                }
              </p>
            </div>

            <div className={`p-3 rounded-md ${
              triageConversionRate >= 70 ? 'bg-status-success/10' :
              triageConversionRate >= 50 ? 'bg-status-warning/10' :
              'bg-status-error/10'
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <Target className="w-3 h-3 text-status-success" />
                <span className="text-xs font-semibold text-lia-text-primary">
                  Taxa de Conversão
                </span>
              </div>
              <p className="text-xs text-lia-text-primary">
                {triageConversionRate >= 70 ?
                  '✅ Ótima conversão na triagem!' :
                  triageConversionRate >= 50 ?
                  '⚠️ Conversão moderada. Revise critérios.' :
                  '❌ Conversão baixa. Ajuste requisitos.'
                }
              </p>
            </div>

            <div className={`p-3 rounded-md ${
              avgTimeContact <= 2 ? 'bg-status-success/10' :
              avgTimeContact <= 4 ? 'bg-status-warning/10' :
              'bg-status-error/10'
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <Clock className="w-3 h-3 text-wedo-orange" />
                <span className="text-xs font-semibold text-lia-text-primary">
                  Velocidade
                </span>
              </div>
              <p className="text-xs text-lia-text-primary">
                {avgTimeContact <= 2 ?
                  '✅ Resposta rápida! Mantém candidatos engajados.' :
                  avgTimeContact <= 4 ?
                  '⚠️ Tempo razoável. Pode ser mais ágil.' :
                  '❌ Muito lento. Risco de perder candidatos.'
                }
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  )
}
