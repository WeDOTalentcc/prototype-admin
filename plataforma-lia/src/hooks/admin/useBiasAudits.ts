"use client"

import { useState, useCallback } from "react"
import useSWR from "swr"
import {
  biasAuditService,
  BiasAuditReport,
  BiasAuditSummary,
  BiasResult,
  BiasAuditListParams,
} from "@/services/admin/bias-service"

export interface UseBiasAuditsResult {
  summary: BiasAuditSummary | null
  latestAudit: BiasAuditReport | null
  audits: BiasAuditReport[]
  totalAudits: number
  isLoading: boolean
  error: Error | null
  refetch: () => void
  fetchAudits: (params?: BiasAuditListParams) => Promise<void>
  fetchAudit: (auditId: string) => Promise<BiasAuditReport | null>
}

export function useBiasAudits(clientId: string): UseBiasAuditsResult {
  const { data, error, isLoading, mutate } = useSWR(
    clientId ? ["adminBiasAudits", clientId] : null,
    async ([, id]) => {
      const [summaryData, latestData, auditsData] = await Promise.all([
        biasAuditService.getSummary(id),
        biasAuditService.getLatest(id),
        biasAuditService.getAudits(id, { limit: 10 }),
      ])
      return { summary: summaryData, latestAudit: latestData, audits: auditsData.audits, total: auditsData.total }
    }
  )

  const fetchAudits = useCallback(async (params?: BiasAuditListParams) => {
    if (!clientId) return
    try {
      const result = await biasAuditService.getAudits(clientId, params)
      await mutate(
        (prev) => prev ? { ...prev, audits: result.audits, total: result.total } : prev,
        false
      )
    } catch (err) {
    }
  }, [clientId, mutate])

  const fetchAudit = useCallback(async (auditId: string): Promise<BiasAuditReport | null> => {
    if (!clientId) return null
    try {
      return await biasAuditService.getAudit(clientId, auditId)
    } catch (err) {
      return null
    }
  }, [clientId])

  return {
    summary: data?.summary ?? null,
    latestAudit: data?.latestAudit ?? null,
    audits: data?.audits ?? [],
    totalAudits: data?.total ?? 0,
    isLoading,
    error: error instanceof Error ? error : error ? new Error(String(error)) : null,
    refetch: () => mutate(),
    fetchAudits,
    fetchAudit,
  }
}

export type { BiasAuditReport, BiasAuditSummary, BiasResult }
