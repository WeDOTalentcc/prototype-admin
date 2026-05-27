"use client"

import React from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  TrendingUp, Clock, Target, CheckCircle, Award, AlertCircle, Activity, Timer
} from"lucide-react"
import { LiaMetricsChart } from"./lia-metrics-chart"
import { generateTimeSeriesData } from"@/hooks/ai/use-lia-metrics-data"
import type { LiaMetricsData } from"@/hooks/ai/use-lia-metrics-data"

interface LiaMetricsPerformanceSectionProps {
  data: LiaMetricsData
}

export function LiaMetricsPerformanceSection({ data }: LiaMetricsPerformanceSectionProps) {
  const {
    avgLiaScore, avgSkillsMatch,
    contactRate, triageConversionRate, triageApprovalRate, interviewConversionRate,
    avgTimeContact, avgTimeTriage, avgTimeInterview, avgTimeTotal,
  } = data

  return (
    <>
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-lia-text-secondary mb-1">
                  Score Médio IA
                </div>
                <div className="text-3xl font-semibold text-lia-text-primary">
                  {avgLiaScore.toFixed(1)}
                </div>
              </div>
              <div className="w-16 h-16 rounded-full bg-wedo-cyan flex items-center justify-center text-white text-xl font-semibold">
                {(avgLiaScore * 10).toFixed(0)}
              </div>
            </div>
            <div className="mt-3 w-full h-2 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full overflow-hidden">
              <div
                className="h-full bg-wedo-cyan transition-[width,height] duration-500"
                style={{width: `${avgLiaScore * 10}%`}}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-lia-text-secondary mb-1">
                  Match Médio de Skills
                </div>
                <div className="text-3xl font-semibold text-lia-text-primary">
                  {avgSkillsMatch.toFixed(0)}%
                </div>
              </div>
              <div className="w-16 h-16 rounded-full bg-wedo-green flex items-center justify-center text-white text-xl font-semibold">
                {avgSkillsMatch.toFixed(0)}
              </div>
            </div>
            <div className="mt-3 w-full h-2 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full overflow-hidden">
              <div
                className="h-full bg-wedo-green transition-[width,height] duration-500"
                style={{width: `${avgSkillsMatch}%`}}
              />
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
            <LiaMetricsChart
              data={generateTimeSeriesData(contactRate)}
              title="Taxa de Contato"
              color="var(--lia-text-secondary)"
              targetValue={80}
            />
            <LiaMetricsChart
              data={generateTimeSeriesData(triageConversionRate)}
              title="Taxa de Conversão (Triagem)"
              color="var(--status-success)"
              targetValue={70}
            />
            <LiaMetricsChart
              data={generateTimeSeriesData(triageApprovalRate)}
              title="Taxa de Aprovação"
              color="var(--wedo-purple)"
              targetValue={60}
            />
            <LiaMetricsChart
              data={generateTimeSeriesData(interviewConversionRate)}
              title="Taxa de Entrevista"
              color="var(--status-warning)"
              targetValue={50}
            />
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
                <div className="flex items-center justify-between mb-2">
                  <Timer className="w-5 h-5 text-lia-text-secondary" />
                  <Chip density="relaxed" variant="neutral" muted className="bg-status-success text-white">
                    ✓ No Prazo
                  </Chip>
                </div>
                <div className="text-2xl font-semibold text-lia-text-primary">
                  {avgTimeContact.toFixed(1)}d
                </div>
                <div className="text-xs text-lia-text-secondary mt-1">
                  Contato Inicial
                </div>
                <div className="text-xs text-lia-text-secondary mt-1">
                  SLA: 2 dias
                </div>
              </div>

              <div className="p-3 bg-status-success/10 dark:bg-lia-bg-secondary rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <Timer className="w-5 h-5 text-status-success" />
                  <Chip density="relaxed" variant="neutral" muted className="bg-status-success text-white">
                    ✓ No Prazo
                  </Chip>
                </div>
                <div className="text-2xl font-semibold text-lia-text-primary">
                  {avgTimeTriage.toFixed(1)}d
                </div>
                <div className="text-xs text-lia-text-secondary mt-1">
                  Triagem Completa
                </div>
                <div className="text-xs text-lia-text-secondary mt-1">
                  SLA: 3 dias
                </div>
              </div>

              <div className="p-3 bg-status-warning/10 dark:bg-lia-bg-secondary rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <Timer className="w-5 h-5 text-status-warning" />
                  <Chip density="relaxed" variant="neutral" muted className="bg-status-warning text-white">
                    ⚠ Atenção
                  </Chip>
                </div>
                <div className="text-2xl font-semibold text-lia-text-primary">
                  {avgTimeInterview.toFixed(1)}d
                </div>
                <div className="text-xs text-lia-text-secondary mt-1">
                  Agendamento
                </div>
                <div className="text-xs text-lia-text-secondary mt-1">
                  SLA: 5 dias
                </div>
              </div>

              <div className="p-3 bg-wedo-purple/10 dark:bg-lia-bg-secondary rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <Clock className="w-5 h-5 text-wedo-purple" />
                  <Chip density="relaxed" variant="neutral" muted >
                    Total
                  </Chip>
                </div>
                <div className="text-2xl font-semibold text-lia-text-primary">
                  {avgTimeTotal.toFixed(1)}d
                </div>
                <div className="text-xs text-lia-text-secondary mt-1">
                  Tempo Total
                </div>
                <div className="text-xs text-lia-text-secondary mt-1">
                  Contato → Entrevista
                </div>
              </div>
            </div>

            <div className="p-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-lia-border-medium rounded-md flex items-center justify-center">
                    <Award className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <div className="text-xs text-lia-text-secondary mb-1">
                      Tempo Médio até Contratação
                    </div>
                    <div className="text-3xl font-semibold text-lia-text-primary">
                      {(avgTimeTotal + 7).toFixed(0)} dias
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-lia-text-secondary mb-1">
                    Meta do Mercado
                  </div>
                  <div className="text-2xl font-semibold text-lia-text-primary">
                    15 dias
                  </div>
                  <Chip variant="neutral" muted className="mt-2 bg-status-success text-white">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    Dentro da Meta
                  </Chip>
                </div>
              </div>

              <div className="mt-4">
                <div className="flex items-center justify-between text-xs text-lia-text-secondary mb-2">
                  <span>Seu desempenho</span>
                  <span>Benchmark mercado</span>
                </div>
                <div className="relative h-3 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full overflow-hidden">
                  <div
                    className="absolute h-full bg-lia-border-medium rounded-full transition-[width,height] duration-500"
                    style={{width: `${((avgTimeTotal + 7) / 15) * 100}%`}}
                  />
                  <div
                    className="absolute left-full h-full border-r-2 border-status-error/30"
                   
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl">
                <div className="text-xs text-lia-text-secondary mb-2">
                  Mais Rápido
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-status-success" />
                  <div>
                    <div className="text-lg font-semibold text-lia-text-primary">
                      {(avgTimeTotal * 0.6).toFixed(1)}d
                    </div>
                    <div className="text-xs text-lia-text-secondary">
                      Melhor caso
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl">
                <div className="text-xs text-lia-text-secondary mb-2">
                  Médio
                </div>
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-lia-text-secondary" />
                  <div>
                    <div className="text-lg font-semibold text-lia-text-primary">
                      {avgTimeTotal.toFixed(1)}d
                    </div>
                    <div className="text-xs text-lia-text-secondary">
                      Caso típico
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl">
                <div className="text-xs text-lia-text-secondary mb-2">
                  Mais Lento
                </div>
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-wedo-orange" />
                  <div>
                    <div className="text-lg font-semibold text-lia-text-primary">
                      {(avgTimeTotal * 1.8).toFixed(1)}d
                    </div>
                    <div className="text-xs text-lia-text-secondary">
                      Pior caso
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  )
}
