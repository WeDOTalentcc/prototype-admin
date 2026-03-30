use client

import { useState, useCallback } from react
import useSWR from swr
import {
  complianceService,
  ComplianceDashboard,
  CompanyControl,
  ControlLibrary,
  ComplianceAudit,
  SOXControl,
  FrameworkStats,
  CompanyControlListParams,
} from @/services/admin/compliance-service

export interface UseComplianceControlsResult {
  dashboard: ComplianceDashboard | null
  controls: CompanyControl[]
  audits: ComplianceAudit[]
  soxControls: SOXControl[]
  totalControls: number
  totalAudits: number
  totalSoxControls: number
  isLoading: boolean
  error: Error | null
  refetch: () => void
  fetchControls: (params?: CompanyControlListParams) => Promise<void>
  fetchAudits: (framework?: string) => Promise<void>
  fetchSOXControls: (section?: string, testResult?: string) => Promise<void>
}

export function useComplianceControls(clientId: string): UseComplianceControlsResult {
  const { data, error, isLoading, mutate } = useSWR(
    clientId ? [adminComplianceControls, clientId] : null,
    async ([, id]) => {
      const [dashboardData, controlsData, auditsData, soxData] = await Promise.all([
        complianceService.getDashboard(id),
        complianceService.getCompanyControls(id, { limit: 20 }),
        complianceService.getAudits(id),
        complianceService.getSOXControls(id),
      ])
      return {
        dashboard: dashboardData,
        controls: controlsData.controls,
        totalControls: controlsData.total,
        audits: auditsData.audits,
        totalAudits: auditsData.total,
        soxControls: soxData.controls,
        totalSoxControls: soxData.total,
      }
    }
  )

  const fetchControls = useCallback(async (params?: CompanyControlListParams) => {
    if (!clientId) return
    try {
      await complianceService.getCompanyControls(clientId, params)
    } catch (err) {
    }
  }, [clientId])

  const fetchAudits = useCallback(async (framework?: string) => {
    if (!clientId) return
    try {
      await complianceService.getAudits(clientId, framework)
    } catch (err) {
    }
  }, [clientId])

  const fetchSOXControls = useCallback(async (section?: string, testResult?: string) => {
    if (!clientId) return
    try {
      await complianceService.getSOXControls(clientId, section, testResult)
    } catch (err) {
    }
  }, [clientId])

  return {
    dashboard: data?.dashboard ?? null,
    controls: data?.controls ?? [],
    audits: data?.audits ?? [],
    soxControls: data?.soxControls ?? [],
    totalControls: data?.totalControls ?? 0,
    totalAudits: data?.totalAudits ?? 0,
    totalSoxControls: data?.totalSoxControls ?? 0,
    isLoading,
    error: error instanceof Error ? error : error ? new Error(String(error)) : null,
    refetch: () => mutate(),
    fetchControls,
    fetchAudits,
    fetchSOXControls,
  }
}

export type {
  ComplianceDashboard,
  CompanyControl,
  ControlLibrary,
  ComplianceAudit,
  SOXControl,
  FrameworkStats,
}
