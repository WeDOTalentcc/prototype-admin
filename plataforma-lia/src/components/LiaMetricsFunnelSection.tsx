"use client"

import React from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  TrendingUp, Phone, Target, Activity, Timer, ArrowRight,
  CheckCircle, Award, Calendar
} from"lucide-react"
import { LiaMetricsChart } from"./lia-metrics-chart"
import { textStyles } from"@/lib/design-tokens"
import { generateTimeSeriesData } from"@/hooks/ai/use-lia-metrics-data"
import type { LiaMetricsData } from"@/hooks/ai/use-lia-metrics-data"

const stageIcons: Record<string, React.ReactNode> = {
  'Contato Inicial': <Phone className="w-4 h-4" />,
  'Triagem Iniciada Iniciada': <Target className="w-4 h-4" />,
  'Triagem Iniciada Completa': <CheckCircle className="w-4 h-4" />,
  'Triagem Iniciada Aprovada': <Award className="w-4 h-4" />,
  'Entrevista Agendada': <Calendar className="w-4 h-4" />,
}

interface LiaMetricsFunnelSectionProps {
  data: LiaMetricsData
}

export function LiaMetricsFunnelSection({ data }: LiaMetricsFunnelSectionProps) {
  const {
    funnelStages, scoreDistribution,
    contactRate, triageConversionRate, avgSkillsMatch,
  } = data

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
              <Activity className="w-4 h-4 text-wedo-purple" />
              Funil de Conversão IA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {funnelStages.map((stage, index) => (
                <div key={stage.stage} className="relative">
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-md ${stage.bgColor} flex items-center justify-center`}>
                      {stageIcons[stage.stage] ?? <Target className="w-4 h-4" />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className={`${textStyles.label}`}>
                          {stage.stage}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-lia-text-secondary">
                            {stage.count}/{stage.total}
                          </span>
                          <Chip density="relaxed" className="px-1.5 py-0.5" variant="neutral">
                            {stage.rate.toFixed(0)}%
                          </Chip>
                        </div>
                      </div>
                      <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${
                            stage.rate >= 70 ? 'bg-wedo-green' :
                            stage.rate >= 50 ? 'bg-wedo-orange' :
                            'bg-status-error'
                          }`}
                          style={{width: `${stage.rate}%`}}
                        />
                      </div>
                    </div>
                    {stage.avgTime > 0 && (
                      <div className={`flex items-center gap-1 ${textStyles.bodySmall}`}>
                        <Timer className="w-3 h-3" />
                        {stage.avgTime}h
                      </div>
                    )}
                  </div>
                  {index < funnelStages.length - 1 && (
                    <ArrowRight className="w-3 h-3 text-lia-text-secondary ml-4 my-1" />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
              <TrendingUp className="w-4 h-4 text-status-success" />
              Distribuição de Scores IA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48">
              <LiaMetricsChart
                data={scoreDistribution}
                title="Distribuição de Notas"
                color="var(--status-success)"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
              <Phone className="w-4 h-4 text-lia-text-secondary" />
              Taxa de Contato (7 dias)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-32">
              <LiaMetricsChart
                data={generateTimeSeriesData(contactRate)}
                title=""
                color="var(--lia-text-secondary)"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
              <TrendingUp className="w-4 h-4 text-status-success" />
              Taxa de Conversão (7 dias)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-32">
              <LiaMetricsChart
                data={generateTimeSeriesData(triageConversionRate)}
                title=""
                color="var(--status-success)"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
              <Target className="w-4 h-4 text-wedo-purple" />
              Match de Skills (7 dias)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-32">
              <LiaMetricsChart
                data={generateTimeSeriesData(avgSkillsMatch)}
                title=""
                color="var(--wedo-purple)"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  )
}
