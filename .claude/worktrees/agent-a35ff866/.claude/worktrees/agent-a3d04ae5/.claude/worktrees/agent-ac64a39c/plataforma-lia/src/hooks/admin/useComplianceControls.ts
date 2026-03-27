'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  complianceService,
  ComplianceDashboard,
  CompanyControl,
  ControlLibrary,
  ComplianceAudit,
  SOXControl,
  FrameworkStats,
  CompanyControlListParams,
} from '@/services/admin/compliance-service'

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
  const [dashboard, setDashboard] = useState<ComplianceDashboard | null>(null)
  const [controls, setControls] = useState<CompanyControl[]>([])
  const [audits, setAudits] = useState<ComplianceAudit[]>([])
  const [soxControls, setSoxControls] = useState<SOXControl[]>([])
  const [totalControls, setTotalControls] = useState(0)
  const [totalAudits, setTotalAudits] = useState(0)
  const [totalSoxControls, setTotalSoxControls] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchData = useCallback(async () => {
    if (!clientId) return

    setIsLoading(true)
    setError(null)

    try {
      const [dashboardData, controlsData, auditsData, soxData] = await Promise.all([
        complianceService.getDashboard(clientId),
        complianceService.getCompanyControls(clientId, { limit: 20 }),
        complianceService.getAudits(clientId),
        complianceService.getSOXControls(clientId),
      ])

      setDashboard(dashboardData)
      setControls(controlsData.controls)
      setTotalControls(controlsData.total)
      setAudits(auditsData.audits)
      setTotalAudits(auditsData.total)
      setSoxControls(soxData.controls)
      setTotalSoxControls(soxData.total)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch compliance data'))
    } finally {
      setIsLoading(false)
    }
  }, [clientId])

  const fetchControls = useCallback(async (params?: CompanyControlListParams) => {
    if (!clientId) return

    try {
      const data = await complianceService.getCompanyControls(clientId, params)
      setControls(data.controls)
      setTotalControls(data.total)
    } catch (err) {
      console.error('Error fetching controls:', err)
    }
  }, [clientId])

  const fetchAudits = useCallback(async (framework?: string) => {
    if (!clientId) return

    try {
      const data = await complianceService.getAudits(clientId, framework)
      setAudits(data.audits)
      setTotalAudits(data.total)
    } catch (err) {
      console.error('Error fetching audits:', err)
    }
  }, [clientId])

  const fetchSOXControls = useCallback(async (section?: string, testResult?: string) => {
    if (!clientId) return

    try {
      const data = await complianceService.getSOXControls(clientId, section, testResult)
      setSoxControls(data.controls)
      setTotalSoxControls(data.total)
    } catch (err) {
      console.error('Error fetching SOX controls:', err)
    }
  }, [clientId])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    dashboard,
    controls,
    audits,
    soxControls,
    totalControls,
    totalAudits,
    totalSoxControls,
    isLoading,
    error,
    refetch: fetchData,
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
