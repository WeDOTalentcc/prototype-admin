'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useCompanyId } from '@/hooks/company/useCompanyId'
import type { CompanyBenefit } from '@/types/benefits'

export type Benefit = CompanyBenefit
export type { CompanyBenefit, JobBenefit, BenefitCategory, BenefitValueType } from '@/types/benefits'
export { toCompanyBenefit, toJobBenefit } from '@/types/benefits'

interface UseCompanyBenefitsOptions {
  companyId?: string
  seniorityLevel?: string
  activeOnly?: boolean
  autoFetch?: boolean
  cacheTime?: number
}

interface UseCompanyBenefitsReturn {
  benefits: Benefit[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  getBenefits: () => Benefit[]
  getHighlightedBenefits: () => Benefit[]
  getBenefitsByCategory: (category: string) => Benefit[]
  getActiveBenefits: () => Benefit[]
  lastFetched: Date | null
}

const benefitsCache: Map<string, { data: Benefit[]; timestamp: number }> = new Map()

export function useCompanyBenefits({
  companyId = '',
  seniorityLevel,
  activeOnly = true,
  autoFetch = true,
  cacheTime = 60000
}: UseCompanyBenefitsOptions = {}): UseCompanyBenefitsReturn {
  const { tenantInfo } = useCompanyId()
  // clientAccountId é o que o JWT conhece — preferir sobre company_profile_id
  const apiCompanyId = tenantInfo?.clientAccountId || companyId
  const [benefits, setBenefits] = useState<Benefit[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastFetched, setLastFetched] = useState<Date | null>(null)

  const cacheKey = useMemo(() => 
    `benefits_${apiCompanyId}_${seniorityLevel || 'all'}_${activeOnly}`,
    [apiCompanyId, seniorityLevel, activeOnly]
  )

  const fetchBenefits = useCallback(async () => {
    const cached = benefitsCache.get(cacheKey)
    if (cached && Date.now() - cached.timestamp < cacheTime) {
      setBenefits(cached.data)
      setLastFetched(new Date(cached.timestamp))
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const endpoint = activeOnly 
        ? `/api/backend-proxy/company/benefits/active?company_id=${apiCompanyId}`
        : `/api/backend-proxy/company/benefits/?company_id=${apiCompanyId}`
      
      const response = await fetch(endpoint)
      
      if (!response.ok) {
        throw new Error('Falha ao carregar benefícios')
      }

      const data = await response.json()
      let benefitsList: Benefit[] = Array.isArray(data) ? data : data.items || []

      if (seniorityLevel && seniorityLevel !== 'all') {
        benefitsList = benefitsList.filter(b => 
          b.seniority_levels.includes('all') || 
          b.seniority_levels.includes(seniorityLevel)
        )
      }

      benefitsCache.set(cacheKey, { data: benefitsList, timestamp: Date.now() })
      setBenefits(benefitsList)
      setLastFetched(new Date())
    } catch (err: unknown) {
      setError(err instanceof Error ? err instanceof Error ? err.message : String(err) : 'Erro ao carregar benefícios')
    } finally {
      setIsLoading(false)
    }
  }, [cacheKey, cacheTime, apiCompanyId, activeOnly, seniorityLevel])

  useEffect(() => {
    if (autoFetch) {
      fetchBenefits()
    }
  }, [autoFetch, fetchBenefits])

  const getBenefits = useCallback(() => {
    return benefits
  }, [benefits])

  const getHighlightedBenefits = useCallback(() => {
    return benefits.filter(b => b.is_highlighted && b.is_active)
  }, [benefits])

  const getBenefitsByCategory = useCallback((category: string) => {
    return benefits.filter(b => b.category === category && b.is_active)
  }, [benefits])

  const getActiveBenefits = useCallback(() => {
    return benefits.filter(b => b.is_active)
  }, [benefits])

  return {
    benefits,
    isLoading,
    error,
    refetch: fetchBenefits,
    getBenefits,
    getHighlightedBenefits,
    getBenefitsByCategory,
    getActiveBenefits,
    lastFetched
  }
}

export function clearBenefitsCache() {
  benefitsCache.clear()
}

export function invalidateBenefitsCache(companyId?: string) {
  if (companyId) {
    for (const key of benefitsCache.keys()) {
      if (key.startsWith(`benefits_${companyId}`)) {
        benefitsCache.delete(key)
      }
    }
  } else {
    benefitsCache.clear()
  }
}
