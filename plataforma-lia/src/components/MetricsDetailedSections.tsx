"use client"

import React from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  TrendingUp, Clock, Users, Target, CheckCircle,
  Phone, Award, Zap, AlertCircle, Activity, Timer
} from"lucide-react"
import { LiaMetricsChart } from"./lia-metrics-chart"
import { textStyles } from"@/lib/design-tokens"
import {
  SourceMetricItem, StatusBreakdownItem,
  generateTimeSeriesData,
} from"@/hooks/ui/use-metrics-calculations"

interface MetricsDetailedSectionsProps {
  contactRate: number
  triageConversionRate: number
  triageApprovalRate: number
  interviewConversionRate: number
  avgLiaScore: number
  avgSkillsMatch: number
  avgTimeContact: number
  avgTimeTriage: number
  avgTimeInterview: number
  avgTimeTotal: number
  pendingApproval: number
  sourceMetrics: SourceMetricItem[]
  candidateStatusBreakdown: StatusBreakdownItem[]
}

export function MetricsDetailedSections({
  contactRate, triageConversionRate, triageApprovalRate, interviewConversionRate,
  avgLiaScore, avgSkillsMatch,
  avgTimeContact, avgTimeTriage, avgTimeInterview, avgTimeTotal,
  pendingApproval,
  sourceMetrics, candidateStatusBreakdown,
}: MetricsDetailedSectionsProps) {
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
                  <div className="text-sm font-semibold text-wedo-orange-text">{pendingApproval} Ações Pendentes</div>
                  <div className="text-xs text-wedo-orange/80">Aguardando aprovação para contato ou próximo passo</div>
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
                      <Chip density="relaxed" variant="neutral" className="px-1 py-0">{source.count} cand.</Chip>
                      <Chip variant="neutral" muted className={`text-xs px-1 py-0 ${source.conversionRate >= 70 ? 'bg-status-success' : source.conversionRate >= 50 ? 'bg-status-warning' : 'bg-status-error'} text-white`}>
                        {source.conversionRate.toFixed(0)}%
                      </Chip>
                    </div>
                  </div>
                  <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-1">
                    <div
                      className={`h-1 rounded-full ${source.conversionRate >= 70 ? 'bg-status-success' : source.conversionRate >= 50 ? 'bg-status-warning' : 'bg-status-error'}`}
                      style={{width: `${source.conversionRate}%`}}
                    />
                  </div>
                </div>
                <div className={textStyles.bodySmall}>Score: {source.avgScore.toFixed(1)}</div>
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
                {status.icon}
                <span className="text-xs font-bold text-lia-text-primary">{status.count}</span>
              </div>
              <div className={`${textStyles.bodySmall} truncate`}>{status.status}</div>
              <div className={textStyles.bodySmall}>{status.percentage.toFixed(0)}% do total</div>
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
            <div className={`p-3 rounded-md ${contactRate >= 80 ? 'bg-status-success/10' : contactRate >= 60 ? 'bg-status-warning/10' : 'bg-status-error/10'}`}>
              <div className="flex items-center gap-2 mb-1">
                <Phone className="w-3 h-3 text-lia-text-secondary" />
                <span className="text-xs font-semibold text-lia-text-primary">Taxa de Contato</span>
              </div>
              <p className="text-xs text-lia-text-primary">
                {contactRate >= 80 ? '✅ Excelente! Continue assim.' : contactRate >= 60 ? '⚠️ Pode melhorar. Tente contatos em horários alternativos.' : '❌ Baixa. Considere múltiplos canais de contato.'}
              </p>
            </div>
            <div className={`p-3 rounded-md ${triageConversionRate >= 70 ? 'bg-status-success/10' : triageConversionRate >= 50 ? 'bg-status-warning/10' : 'bg-status-error/10'}`}>
              <div className="flex items-center gap-2 mb-1">
                <Target className="w-3 h-3 text-status-success" />
                <span className="text-xs font-semibold text-lia-text-primary">Taxa de Conversão</span>
              </div>
              <p className="text-xs text-lia-text-primary">
                {triageConversionRate >= 70 ? '✅ Ótima conversão na triagem!' : triageConversionRate >= 50 ? '⚠️ Conversão moderada. Revise critérios.' : '❌ Conversão baixa. Ajuste requisitos.'}
              </p>
            </div>
            <div className={`p-3 rounded-md ${avgTimeContact <= 2 ? 'bg-status-success/10' : avgTimeContact <= 4 ? 'bg-status-warning/10' : 'bg-status-error/10'}`}>
              <div className="flex items-center gap-2 mb-1">
                <Clock className="w-3 h-3 text-wedo-orange" />
                <span className="text-xs font-semibold text-lia-text-primary">Velocidade</span>
              </div>
              <p className="text-xs text-lia-text-primary">
                {avgTimeContact <= 2 ? '✅ Resposta rápida! Mantém candidatos engajados.' : avgTimeContact <= 4 ? '⚠️ Tempo razoável. Pode ser mais ágil.' : '❌ Muito lento. Risco de perder candidatos.'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-lia-text-secondary mb-1">Score Médio IA</div>
                <div className="text-3xl font-semibold text-lia-text-primary">{avgLiaScore.toFixed(1)}</div>
              </div>
              <div className="w-16 h-16 rounded-full bg-wedo-cyan flex items-center justify-center text-white text-xl font-semibold">
                {(avgLiaScore * 10).toFixed(0)}
              </div>
            </div>
            <div className="mt-3 w-full h-2 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full overflow-hidden">
              <div className="h-full bg-wedo-cyan transition-[width,height] duration-500" style={{width: `${avgLiaScore * 10}%`}} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-lia-text-secondary mb-1">Match Médio de Skills</div>
                <div className="text-3xl font-semibold text-lia-text-primary">{avgSkillsMatch.toFixed(0)}%</div>
              </div>
              <div className="w-16 h-16 rounded-full bg-wedo-green flex items-center justify-center text-white text-xl font-semibold">
                {avgSkillsMatch.toFixed(0)}
              </div>
            </div>
            <div className="mt-3 w-full h-2 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full overflow-hidden">
              <div className="h-full bg-wedo-green transition-[width,height] duration-500" style={{width: `${avgSkillsMatch}%`}} />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Evolução das Métricas (Últimos 7 Dias)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-6">
            <LiaMetricsChart data={generateTimeSeriesData(contactRate)} title="Taxa de Contato" color="var(--lia-text-secondary)" targetValue={80} />
            <LiaMetricsChart data={generateTimeSeriesData(triageConversionRate)} title="Taxa de Conversão (Triagem)" color="var(--status-success)" targetValue={70} />
            <LiaMetricsChart data={generateTimeSeriesData(triageApprovalRate)} title="Taxa de Aprovação" color="var(--wedo-purple)" targetValue={60} />
            <LiaMetricsChart data={generateTimeSeriesData(interviewConversionRate)} title="Taxa de Entrevista" color="var(--status-warning)" targetValue={50} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Timer className="w-4 h-4" />
            SLA e Tempo Médio por Etapa
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div className="p-3 bg-lia-bg-tertiary rounded-xl">
                <div className="flex items-center justify-between mb-2"><Timer className="w-5 h-5 text-lia-text-secondary" /><Chip density="relaxed" variant="neutral" muted className="bg-status-success text-white">✓ No Prazo</Chip></div>
                <div className="text-2xl font-semibold text-lia-text-primary">{avgTimeContact.toFixed(1)}d</div>
                <div className="text-xs text-lia-text-secondary mt-1">Contato Inicial</div>
                <div className="text-xs text-lia-text-secondary mt-1">SLA: 2 dias</div>
              </div>
              <div className="p-3 bg-status-success/10 dark:bg-lia-bg-secondary rounded-xl">
                <div className="flex items-center justify-between mb-2"><Timer className="w-5 h-5 text-status-success" /><Chip density="relaxed" variant="neutral" muted className="bg-status-success text-white">✓ No Prazo</Chip></div>
                <div className="text-2xl font-semibold text-lia-text-primary">{avgTimeTriage.toFixed(1)}d</div>
                <div className="text-xs text-lia-text-secondary mt-1">Triagem Completa</div>
                <div className="text-xs text-lia-text-secondary mt-1">SLA: 3 dias</div>
              </div>
              <div className="p-3 bg-status-warning/10 dark:bg-lia-bg-secondary rounded-xl">
                <div className="flex items-center justify-between mb-2"><Timer className="w-5 h-5 text-status-warning" /><Chip density="relaxed" variant="neutral" muted className="bg-status-warning text-white">⚠ Atenção</Chip></div>
                <div className="text-2xl font-semibold text-lia-text-primary">{avgTimeInterview.toFixed(1)}d</div>
                <div className="text-xs text-lia-text-secondary mt-1">Agendamento</div>
                <div className="text-xs text-lia-text-secondary mt-1">SLA: 5 dias</div>
              </div>
              <div className="p-3 bg-wedo-purple/10 dark:bg-lia-bg-secondary rounded-xl">
                <div className="flex items-center justify-between mb-2"><Clock className="w-5 h-5 text-wedo-purple-text" /><Chip density="relaxed" variant="neutral" muted >Total</Chip></div>
                <div className="text-2xl font-semibold text-lia-text-primary">{avgTimeTotal.toFixed(1)}d</div>
                <div className="text-xs text-lia-text-secondary mt-1">Tempo Total</div>
                <div className="text-xs text-lia-text-secondary mt-1">Contato → Entrevista</div>
              </div>
            </div>

            <div className="p-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-lia-border-medium rounded-md flex items-center justify-center"><Award className="w-6 h-6 text-white" /></div>
                  <div>
                    <div className="text-xs text-lia-text-secondary mb-1">Tempo Médio até Contratação</div>
                    <div className="text-3xl font-semibold text-lia-text-primary">{(avgTimeTotal + 7).toFixed(0)} dias</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-lia-text-secondary mb-1">Meta do Mercado</div>
                  <div className="text-2xl font-semibold text-lia-text-primary">15 dias</div>
                  <Chip variant="neutral" muted className="mt-2 bg-status-success text-white"><TrendingUp className="w-3 h-3 mr-1" />Dentro da Meta</Chip>
                </div>
              </div>
              <div className="mt-4">
                <div className="flex items-center justify-between text-xs text-lia-text-secondary mb-2">
                  <span>Seu desempenho</span><span>Benchmark mercado</span>
                </div>
                <div className="relative h-3 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full overflow-hidden">
                  <div className="absolute h-full bg-lia-border-medium rounded-full transition-[width,height] duration-500" style={{width: `${((avgTimeTotal + 7) / 15) * 100}%`}} />
                  <div className="absolute left-full h-full border-r-2 border-status-error/30" />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl">
                <div className="text-xs text-lia-text-secondary mb-2">Mais Rápido</div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-status-success" />
                  <div><div className="text-lg font-semibold text-lia-text-primary">{(avgTimeTotal * 0.6).toFixed(1)}d</div><div className="text-xs text-lia-text-secondary">Melhor caso</div></div>
                </div>
              </div>
              <div className="p-3 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl">
                <div className="text-xs text-lia-text-secondary mb-2">Médio</div>
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-lia-text-secondary" />
                  <div><div className="text-lg font-semibold text-lia-text-primary">{avgTimeTotal.toFixed(1)}d</div><div className="text-xs text-lia-text-secondary">Caso típico</div></div>
                </div>
              </div>
              <div className="p-3 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl">
                <div className="text-xs text-lia-text-secondary mb-2">Mais Lento</div>
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-wedo-orange" />
                  <div><div className="text-lg font-semibold text-lia-text-primary">{(avgTimeTotal * 1.8).toFixed(1)}d</div><div className="text-xs text-lia-text-secondary">Pior caso</div></div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  )
}
