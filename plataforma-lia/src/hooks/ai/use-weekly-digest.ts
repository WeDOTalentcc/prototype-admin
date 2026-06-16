'use client'

import { useState, useEffect, useCallback } from 'react'
import type { WeeklyDigestData } from '@/components/notifications/weekly-digest-notification'

const STORAGE_KEY_PREFIX = 'lia_weekly_digest_last_shown'

function getStorageKey(userId?: string): string {
  return userId ? `${STORAGE_KEY_PREFIX}_${userId}` : STORAGE_KEY_PREFIX
}

function isMonday(): boolean {
  return new Date().getDay() === 1
}

function shouldShowDigest(userId?: string): boolean {
  try {
    const key = getStorageKey(userId)
    const lastShown = localStorage.getItem(key)
    if (!lastShown) return true
    const lastDate = new Date(lastShown)
    const now = new Date()
    const sameDay =
      lastDate.getFullYear() === now.getFullYear() &&
      lastDate.getMonth() === now.getMonth() &&
      lastDate.getDate() === now.getDate()
    return !sameDay
  } catch {
    return true
  }
}

function markDigestShown(userId?: string): void {
  try {
    localStorage.setItem(getStorageKey(userId), new Date().toISOString())
  } catch (error) {
    console.error("[use-weekly-digest] Error:", error)
    // ignore
  }
}

function mapBackendToDigestData(data: Record<string, unknown>): WeeklyDigestData {
  const digest = (data.digest as Record<string, unknown>) || data
  const pipeline = (digest.pipeline_health as Record<string, unknown>) || {}
  const atRisk = (digest.vagas_em_risco as Record<string, unknown>) || {}
  const compliance = (digest.compliance_summary as Record<string, unknown>) || {}
  const optimization = (digest.optimization_insights as Record<string, unknown>) || {}
  const period = (digest.period as Record<string, unknown>) || {}

  const date = period.end
    ? String(period.end)
    : new Date().toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })

  const atRiskJobs: WeeklyDigestData['atRiskJobs'] = ((atRisk.jobs as unknown[]) || []).map(
    (j: unknown) => {
      const job = j as Record<string, unknown>
      const detail = job.reason
        ? String(job.reason)
        : job.detail
        ? String(job.detail)
        : undefined
      return {
        title: String(job.title || job.job_title || ''),
        company: String(job.company || job.company_name || ''),
        daysOpen: Number(job.days_open || job.days_since_opened || 0),
        targetDays: Number(job.target_days || job.sla_days || 30),
        severity: (job.severity === 'critical' ? 'critical' : 'warning') as 'critical' | 'warning',
        detail,
      }
    }
  )

  const rawStatus = String(compliance.status || 'ok').toLowerCase()
  const complianceStatus: 'ok' | 'warning' | 'alert' =
    rawStatus === 'ok' ? 'ok'
    : rawStatus === 'warning' || rawStatus === 'attention' ? 'warning'
    : rawStatus === 'alert' || rawStatus === 'critical' ? 'alert'
    : rawStatus === 'unknown' ? 'warning'
    : 'ok'

  const complianceMessage =
    String(compliance.message || '') ||
    (complianceStatus === 'ok'
      ? 'FairnessGuard não bloqueou nenhuma triagem esta semana. Todas as avaliações dentro dos limites de equidade.'
      : 'Há alertas de compliance que precisam de atenção.')

  return {
    date,
    pipeline: {
      activeJobs: Number(pipeline.total_active_jobs || 0),
      screened: Number(pipeline.candidates_screened_week || 0),
      interviews: Number(pipeline.interviews_scheduled || 0),
      conversionRate:
        pipeline.conversion_rate != null ? Number(pipeline.conversion_rate) : undefined,
      conversionDelta:
        pipeline.conversion_change != null ? Number(pipeline.conversion_change) : undefined,
    },
    atRiskJobs,
    compliance: {
      status: complianceStatus,
      message: complianceMessage,
    },
    optimization: optimization.summary
      ? { message: String(optimization.summary) }
      : undefined,
  }
}

interface UseWeeklyDigestOptions {
  enabled?: boolean
  triggerOnMonday?: boolean
  userId?: string
}

interface UseWeeklyDigestReturn {
  digest: WeeklyDigestData | null
  isLoading: boolean
  error: string | null
  isVisible: boolean
  dismiss: () => void
  reload: () => Promise<void>
}

export function useWeeklyDigest({
  enabled = true,
  triggerOnMonday = true,
  userId,
}: UseWeeklyDigestOptions = {}): UseWeeklyDigestReturn {
  const [digest, setDigest] = useState<WeeklyDigestData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isVisible, setIsVisible] = useState(false)

  const fetchDigest = useCallback(async () => {
    if (!enabled) return
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/backend-proxy/digest/weekly/preview', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || `HTTP ${res.status}`)
      }
      const data = await res.json()
      const mapped = mapBackendToDigestData(data)
      setDigest(mapped)
      return mapped
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erro ao buscar resumo semanal')
      return null
    } finally {
      setIsLoading(false)
    }
  }, [enabled])

  const reload = useCallback(async () => {
    const mapped = await fetchDigest()
    if (mapped) {
      setIsVisible(true)
    }
  }, [fetchDigest])

  const dismiss = useCallback(() => {
    setIsVisible(false)
    markDigestShown(userId)
  }, [userId])

  useEffect(() => {
    if (!enabled) return
    const shouldTrigger = triggerOnMonday ? isMonday() : true
    if (!shouldTrigger) return
    if (!shouldShowDigest(userId)) return

    fetchDigest().then((mapped) => {
      if (mapped) {
        setIsVisible(true)
        markDigestShown(userId)
      }
    })
  }, [enabled, triggerOnMonday, userId, fetchDigest])

  return { digest, isLoading, error, isVisible, dismiss, reload }
}
