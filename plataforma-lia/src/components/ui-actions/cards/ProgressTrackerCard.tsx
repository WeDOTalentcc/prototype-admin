"use client"

import React from"react"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Progress } from"@/components/ui/progress"
import {
  Target,
  Users,
  CheckCircle2,
  Clock,
  TrendingUp,
  AlertTriangle
} from"lucide-react"

interface PipelineStage {
  name: string
  count: number
  color: string
}

interface ProgressTrackerData {
  job_title: string
  total_candidates: number
  target_candidates: number
  stages: PipelineStage[]
  days_open: number
  avg_time_to_hire?: number
  conversion_rate?: number
  alerts?: string[]
}

interface ProgressTrackerCardProps {
  data: ProgressTrackerData
  compact?: boolean
}

export function ProgressTrackerCard({
  data,
  compact = false
}: ProgressTrackerCardProps) {
  const progressPercent = Math.min(
    Math.round((data.total_candidates / data.target_candidates) * 100),
    100
  )

  const isOnTrack = data.total_candidates >= data.target_candidates * 0.5

  return (
    <Card
      className="w-full max-w-md border-l-4 overflow-hidden bg-lia-bg-secondary"
     
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div
              className="h-10 w-10 rounded-full flex items-center justify-center bg-lia-bg-tertiary"
            >
              <Target className="h-5 w-5 text-wedo-purple" />
            </div>
            <div>
              <div className="font-semibold text-lia-text-primary">
                {data.job_title}
              </div>
              <div className="text-xs text-lia-text-tertiary">
                Progresso do Pipeline
              </div>
            </div>
          </div>
          <Chip
            variant="neutral"
            className="border border-lia-border-default bg-lia-bg-primary text-lia-text-primary"
          >
            {isOnTrack ? (
              <>
                <CheckCircle2 className="h-3 w-3 mr-1 text-wedo-green" />
                No Ritmo
              </>
            ) : (
              <>
                <AlertTriangle className="h-3 w-3 mr-1 text-lia-text-secondary" />
                Atenção
              </>
            )}
          </Chip>
        </div>

        <div className="mb-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-lia-text-secondary">Meta de Candidatos</span>
            <span className="font-semibold text-lia-text-primary">
              {data.total_candidates} / {data.target_candidates}
            </span>
          </div>
          <div
            className="relative h-2 rounded-full overflow-hidden bg-lia-bg-tertiary"
          >
            <div
              className="absolute inset-y-0 left-0 rounded-full transition-[width,height] duration-500 bg-lia-text-primary"
              style={{width: `${progressPercent}%`}}
            />
          </div>
          <div
            className="text-xs mt-1 text-right text-lia-text-tertiary"
          >
            {progressPercent}% concluído
          </div>
        </div>

        {!compact && data.stages && data.stages.length > 0 && (
          <div className="mb-4">
            <div className="text-sm mb-2 text-lia-text-secondary">Pipeline</div>
            <div
              className="flex h-4 rounded-full overflow-hidden bg-lia-bg-tertiary"
            >
              {data.stages.map((stage, index) => (
                <div
                  key={stage.name}
                  className={`${stage.color} relative`}
                  style={{width: `${(stage.count / data.total_candidates) * 100}%`,
                    minWidth: stage.count > 0 ?"16px" :"0"}}
                  title={`${stage.name}: ${stage.count}`}
                />
              ))}
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {data.stages.map((stage, index) => (
                <div key={stage.name} className="flex items-center gap-1.5 text-xs">
                  <div className={`h-2 w-2 rounded-full ${stage.color}`} />
                  <span className="text-lia-text-secondary">{stage.name}</span>
                  <span className="font-medium text-lia-text-primary">
                    {stage.count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-3 gap-2">
          <div
            className="text-center p-2 rounded-xl border bg-lia-bg-primary border-lia-border-subtle"
          >
            <div className="text-lg font-semibold text-lia-text-secondary">{data.days_open}</div>
            <div className="text-xs text-lia-text-tertiary">Dias Aberta</div>
          </div>
          {data.avg_time_to_hire !== undefined && (
            <div
              className="text-center p-2 rounded-xl border bg-lia-bg-primary border-lia-border-subtle"
            >
              <div className="text-lg font-semibold text-lia-text-primary">
                {data.avg_time_to_hire}d
              </div>
              <div className="text-xs text-lia-text-tertiary">Tempo Médio</div>
            </div>
          )}
          {data.conversion_rate !== undefined && (
            <div
              className="text-center p-2 rounded-xl border bg-lia-bg-primary border-lia-border-subtle"
            >
              <div className="text-lg font-semibold text-lia-text-secondary">{data.conversion_rate}%</div>
              <div className="text-xs text-lia-text-tertiary">Conversão</div>
            </div>
          )}
        </div>

        {!compact && data.alerts && data.alerts.length > 0 && (
          <div className="mt-4 space-y-1">
            {data.alerts.slice(0, 2).map((alert, index) => (
              <div
                key={`alert-${index}`}
                className="flex items-start gap-2 text-xs px-2 py-1.5 rounded-xl bg-lia-bg-tertiary text-lia-text-secondary"
              >
                <AlertTriangle className="h-3 w-3 mt-0.5 shrink-0 text-lia-text-secondary" />
                <span>{alert}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
