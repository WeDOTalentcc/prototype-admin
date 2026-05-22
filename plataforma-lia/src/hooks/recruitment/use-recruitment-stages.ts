"use client"

import { useState, useEffect, useCallback, useMemo } from 'react'
import { DEFAULT_STAGES } from '@/components/settings/RecruitmentJourneyConfig'
import type { RecruitmentStage } from '@/components/settings/recruitment-journey.types'
// WT-2022 P0.STAGES + P0.SUB_STATUSES: adapter import to expose legacy back-compat variants
import {
  normalizeStagesFromHook,
  normalizeSubStatusesFromHook,
  type RecruitmentStage as LegacyRecruitmentStage,
  type SubStatus as LegacySubStatus,
  type HookSubStatus,
} from '@/lib/recruitment'

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
  /**
   * WT-2022 P0.STAGES — stages normalizadas pro shape legacy (camelCase).
   * Use em consumers transitional que ainda dependem de
   * {displayName, stageOrder, stageType, isInitial, isFinal, stageCategory,
   * allowedTransitions} ao inves de importar RECRUITMENT_STAGES direto.
   */
  legacyStages: LegacyRecruitmentStage[]
  /**
   * WT-2022 P0.SUB_STATUSES — sub-statuses canonical agrupados por stage name
   * (snake_case, vindo direto de /api/backend-proxy/company-pipeline).
   * Reflete customizacao de Configuracoes > Pipeline > sub-statuses por estagio.
   */
  subStatuses: Record<string, HookSubStatus[]>
  /**
   * WT-2022 P0.SUB_STATUSES — sub-statuses normalizados pro shape legacy
   * (camelCase: displayName/isDefault/isWaiting/isApproval/isRejection).
   * Use em consumers transitional que ainda dependem do shape SUB_STATUSES
   * hardcoded de @/lib/recruitment ao inves de importa-lo direto.
   */
  legacySubStatuses: Record<string, LegacySubStatus[]>
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

  // WT-2022 P0.STAGES: memoized adapter pra back-compat consumers
  const legacyStages = useMemo(
    () => normalizeStagesFromHook(stages),
    [stages]
  )

  // WT-2022 P0.SUB_STATUSES: extrai sub_statuses canonical por stage name
  // (snake_case do backend, pronto pra consumers que querem o shape real)
  const subStatuses = useMemo<Record<string, HookSubStatus[]>>(() => {
    const map: Record<string, HookSubStatus[]> = {}
    for (const stage of stages) {
      const list = stage.sub_statuses
      if (Array.isArray(list) && list.length > 0) {
        // Backend ja retorna HookSubStatus-compatible em sub_statuses; cast
        // pra preservar tipos. is_active filter aplicado pra refletir toggles
        // de Configuracoes > Pipeline.
        map[stage.name] = (list as unknown as HookSubStatus[]).filter(
          (ss) => ss.is_active !== false,
        )
      }
    }
    return map
  }, [stages])

  // WT-2022 P0.SUB_STATUSES: legacy camelCase shape pra consumers transitional
  const legacySubStatuses = useMemo(
    () => normalizeSubStatusesFromHook(subStatuses),
    [subStatuses]
  )

  return {
    stages,
    activeStages,
    interviewStages,
    legacyStages,
    subStatuses,
    legacySubStatuses,
    isLoading,
    error,
    refetch: fetchStages,
    sla
  }
}

export default useRecruitmentStages
