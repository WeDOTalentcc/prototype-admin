"use client"

import { useState, useEffect, useCallback } from 'react'
import { AlertTriangle, TrendingUp, Lightbulb, Clock, Users, Globe, Search, Settings } from 'lucide-react'
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover'
import { toast } from 'sonner'
import { useRouter } from 'next/navigation'

interface ChannelCounts {
  web: number
  whatsapp: number
  sourcing: number
  ats: number
}

interface ChannelSaturation {
  count: number
  threshold: number
  is_saturated: boolean
  slots_remaining: number
  percentage: number
}

interface SaturationStatus {
  job_id: string
  approved_count: number
  saturation_threshold: number
  is_saturated: boolean
  slots_remaining: number
  recommendation: "continue_screening" | "pause_screening"
  saturation_percentage: number
  queued_count: number
  last_screened_at: string | null
  saturation_disabled_until: string | null
  counts_by_channel: ChannelCounts
  organic: ChannelSaturation
  sourcing: ChannelSaturation
  threshold_web: number
  threshold_sourcing: number
  unlock_increment: number
  unlock_hours: number
}

interface SaturationBadgeProps {
  jobId: string
}

type SaturationState = "saturated" | "almost" | "normal"

function getSaturationState(data: SaturationStatus): SaturationState {
  if (data.saturation_disabled_until) {
    const disabledUntil = new Date(data.saturation_disabled_until)
    if (disabledUntil > new Date()) {
      return "normal"
    }
  }

  if (data.organic.is_saturated || data.sourcing.is_saturated) {
    return "saturated"
  }

  if (data.organic.percentage >= 90 || data.sourcing.percentage >= 90) {
    return "almost"
  }

  return "normal"
}

function formatLastScreened(dateStr: string | null): string {
  if (!dateStr) return "Sem triagens recentes"
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return "Último triado hoje"
  if (diffDays === 1) return "Último triado há 1 dia"
  return `Último triado há ${diffDays} dias`
}

function getRecommendationText(recommendation: string): string {
  if (recommendation === "pause_screening") {
    return "Recomendamos agendar entrevistas antes de desbloquear"
  }
  return "Pipeline com capacidade — triagem pode continuar"
}

export function SaturationBadge({ jobId }: SaturationBadgeProps) {
  const [data, setData] = useState<SaturationStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const router = useRouter()

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`/api/backend-proxy/job-vacancies/${jobId}/saturation-status/`)
      if (!response.ok) return
      const result = await response.json()
      setData(result)
    } catch {
    } finally {
      setLoading(false)
    }
  }, [jobId])

  useEffect(() => {
    if (!jobId) return
    fetchStatus()
  }, [jobId, fetchStatus])

  const handleUnlock = async (action: "increase_threshold" | "disable_temporarily") => {
    if (!data) return
    setActionLoading(true)
    try {
      const body = action === "increase_threshold"
        ? { action, new_threshold: data.saturation_threshold + data.unlock_increment }
        : { action, disable_hours: data.unlock_hours }

      const response = await fetch(`/api/backend-proxy/job-vacancies/${jobId}/unlock-pipeline/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        toast.error("Erro ao desbloquear pipeline")
        return
      }

      const message = action === "increase_threshold"
        ? `Limite aumentado em +${data.unlock_increment}`
        : `Pipeline desbloqueado por ${data.unlock_hours}h`
      toast.success(message)

      await fetchStatus()
    } catch {
      toast.error("Erro ao conectar com o servidor")
    } finally {
      setActionLoading(false)
    }
  }

  if (loading || !data) return null

  const state = getSaturationState(data)

  if (state === "normal") return null

  const isSaturated = state === "saturated"

  const organicPercent = Math.min(data.organic.percentage, 100)
  const sourcingPercent = Math.min(data.sourcing.percentage, 100)

  const badgeElement = isSaturated ? (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-micro font-semibold font-['Open_Sans'] text-status-error bg-status-error/10 border border-status-error/30 cursor-pointer" title="Pipeline Saturado">
      <AlertTriangle className="w-3 h-3 shrink-0" />
      <span>{data.organic.count}/{data.organic.threshold} org</span>
      <span className="text-status-error">|</span>
      <span>{data.sourcing.count}/{data.sourcing.threshold} src</span>
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-micro font-semibold font-['Open_Sans'] text-status-warning bg-status-warning/10 border border-status-warning/30 cursor-pointer" title="Quase Saturado">
      <TrendingUp className="w-3 h-3 shrink-0" />
      <span>{data.organic.count}/{data.organic.threshold} org</span>
      <span className="text-status-warning">|</span>
      <span>{data.sourcing.count}/{data.sourcing.threshold} src</span>
    </span>
  )

  return (
    <Popover>
      <PopoverTrigger asChild>
        {badgeElement}
      </PopoverTrigger>
      <PopoverContent
        className="w-[300px] rounded-md p-0 shadow-none border border-gray-200"
        align="start"
        sideOffset={8}
      >
        <div className="p-3 space-y-3 text-xs font-['Open_Sans']">
          <div className="font-medium text-gray-900">
            {isSaturated ? "Pipeline Saturado" : "Quase Saturado"}
          </div>

          <div className="space-y-2">
            <div className="space-y-1">
              <div className="flex items-center justify-between text-gray-700">
                <span className="flex items-center gap-1">
                  <Globe className="w-3 h-3 text-wedo-cyan-dark" />
                  Orgânico (Web + WhatsApp)
                </span>
                <span className={data.organic.is_saturated ? 'text-status-error font-semibold' : ''}>
                  {data.organic.count}/{data.organic.threshold}
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full transition-all ${data.organic.is_saturated ? 'bg-status-error' : organicPercent >= 90 ? 'bg-status-warning' : 'bg-wedo-cyan'}`}
                  style={{ width: `${organicPercent}%` }}
                />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between text-gray-700">
                <span className="flex items-center gap-1">
                  <Search className="w-3 h-3 text-gray-500" />
                  Busca Ativa (Sourcing + ATS)
                </span>
                <span className={data.sourcing.is_saturated ? 'text-status-error font-semibold' : ''}>
                  {data.sourcing.count}/{data.sourcing.threshold}
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full transition-all ${data.sourcing.is_saturated ? 'bg-status-error' : sourcingPercent >= 90 ? 'bg-status-warning' : 'bg-gray-500'}`}
                  style={{ width: `${sourcingPercent}%` }}
                />
              </div>
            </div>
          </div>

          <div className="space-y-1 text-gray-600">
            <div className="flex items-center gap-1.5">
              <Users className="w-3 h-3 text-gray-400" />
              <span>{data.queued_count} candidatos aguardando triagem</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Clock className="w-3 h-3 text-gray-400" />
              <span>{formatLastScreened(data.last_screened_at)}</span>
            </div>
          </div>

          <div className="flex items-start gap-1.5 text-gray-500">
            <Lightbulb className="w-3 h-3 mt-0.5 text-status-warning shrink-0" />
            <span>{getRecommendationText(data.recommendation)}</span>
          </div>
        </div>

        <div className="border-t border-gray-200 p-3 space-y-2">
          <button
            onClick={() => handleUnlock("increase_threshold")}
            disabled={actionLoading}
            className="w-full px-3 py-1.5 rounded-md text-xs font-medium font-['Open_Sans'] text-gray-700 bg-gray-50 border border-gray-200 hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Aumentar limite (+{data.unlock_increment})
          </button>
          <button
            onClick={() => handleUnlock("disable_temporarily")}
            disabled={actionLoading}
            className="w-full px-3 py-1.5 rounded-md text-xs font-medium font-['Open_Sans'] text-gray-700 bg-gray-50 border border-gray-200 hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Desbloquear por {data.unlock_hours}h
          </button>
          <button
            onClick={() => router.push('/configuracoes')}
            className="w-full px-3 py-1.5 rounded-md text-xs font-medium font-['Open_Sans'] text-wedo-cyan-dark bg-wedo-cyan/10 border border-wedo-cyan/30 hover:bg-wedo-cyan/15 transition-colors flex items-center justify-center gap-1"
          >
            <Settings className="w-3 h-3" />
            Ver configurações
          </button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
