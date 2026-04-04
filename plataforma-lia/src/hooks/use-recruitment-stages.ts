"use client"

import { useState, useEffect, useCallback, useMemo } from 'react'
import { DEFAULT_STAGES } from '@/components/settings/RecruitmentJourneyConfig'
import type { RecruitmentStage } from '@/components/settings/recruitment-journey.types'

export type { RecruitmentStage }

interface SLACalculations {
  screeningSLA: number
  shortlistSLA: number
  totalSLA: number
  calculateDeadline: (slaInDays: number) => string
}

interface UseRecruitmentStagesResult {
  stages: RecruitmentStage[]
  activeStages: RecruitmentStage[]
  interviewStages: RecruitmentStage[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  sla: SLACalculations
}

export function useRecruitmentStages(): UseRecruitmentStagesResult {
  const [stages, setStages] = useState<RecruitmentStage[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStages = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/backend-proxy/company-pipeline')
      
      if (!response.ok) {
        throw new Error(`Failed to fetch stages: ${response.status}`)
      }

      const data = await response.json()
      
      if (data.pipeline && Array.isArray(data.pipeline)) {
        const stages: RecruitmentStage[] = data.pipeline.map((s: Record<string, unknown>, idx: number) => ({
          id: s.id,
          name: s.name,
          display_name: s.display_name,
          order: s.stage_order || idx + 1,
          isActive: s.is_active ?? true,
          notes: s.description || "",
          sla: s.sla_hours ? Math.round(Number(s.sla_hours) / 24) : 0,
          type: s.stage_category === 'system' ? 'system' : (s.stage_category === 'catalog' ? 'default' : 'custom'),
          color: s.color,
          icon: s.icon,
          action_behavior: s.action_behavior,
          default_channel: s.default_channel,
          stage_category: s.stage_category,
          sub_statuses: Array.isArray(s.sub_statuses) ? s.sub_statuses : [],
        }))
        setStages(stages)
      } else if (data && Array.isArray(data.stages)) {
        setStages(data.stages)
      } else if (data && Array.isArray(data)) {
        setStages(data)
      } else {
        setStages(DEFAULT_STAGES)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setStages(DEFAULT_STAGES)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStages()
  }, [fetchStages])

  const activeStages = useMemo(() => 
    stages.filter(stage => stage.isActive).sort((a, b) => a.order - b.order),
    [stages]
  )

  const interviewStages = useMemo(() => 
    activeStages.filter(stage => stage.type !== 'system'),
    [activeStages]
  )

  const sla = useMemo((): SLACalculations => {
    const screeningStage = activeStages.find(s => 
      s.name.toLowerCase().includes('triagem') || s.name.toLowerCase().includes('screening')
    )
    const screeningSLA = screeningStage?.sla || 3

    const halfwayIndex = Math.ceil(interviewStages.length / 2)
    const shortlistSLA = interviewStages
      .slice(0, halfwayIndex)
      .reduce((acc, s) => acc + s.sla, 0) || 14

    const totalSLA = interviewStages.reduce((acc, s) => acc + s.sla, 0) || 30

    const calculateDeadline = (slaInDays: number): string => {
      const deadline = new Date()
      deadline.setDate(deadline.getDate() + slaInDays)
      return deadline.toISOString().split('T')[0]
    }

    return { screeningSLA, shortlistSLA, totalSLA, calculateDeadline }
  }, [activeStages, interviewStages])

  return {
    stages,
    activeStages,
    interviewStages,
    isLoading,
    error,
    refetch: fetchStages,
    sla
  }
}

export default useRecruitmentStages
