"use client"

import { useState, useEffect, useCallback } from 'react'

export interface CompanyDefaults {
  workModel: string
  employmentTypes: string[]
  defaultLanguages: string[]
  benefits: CompanyBenefit[]
}

export interface CompanyBenefit {
  id: string
  name: string
  category: string
  isActive: boolean
}

interface UseCompanyDefaultsResult {
  defaults: CompanyDefaults
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

const EMPTY_DEFAULTS: CompanyDefaults = {
  workModel: '',
  employmentTypes: [],
  defaultLanguages: [],
  benefits: [],
}

export function useCompanyDefaults(): UseCompanyDefaultsResult {
  const [defaults, setDefaults] = useState<CompanyDefaults>(EMPTY_DEFAULTS)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDefaults = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const profileRes = await fetch('/api/backend-proxy/company/profile')
      let companyId: string | null = null

      if (profileRes.ok) {
        const profile = await profileRes.json()
        // Prefer clientAccountId (what JWT knows) for benefits API
        companyId = profile?.client_account_id || profile?.id || null
      }

      const fetches: Promise<Response>[] = []

      if (companyId) {
        fetches.push(fetch(`/api/backend-proxy/company/culture-profile?company_id=${companyId}`))
        fetches.push(fetch(`/api/backend-proxy/company/benefits/?company_id=${companyId}`))
      }

      const responses = await Promise.all(fetches)

      let workModel = ''
      let employmentTypes: string[] = []
      let defaultLanguages: string[] = []

      if (companyId && responses[0]?.ok) {
        const culture = await responses[0].json()
        if (culture && !culture.notFound) {
          workModel = culture.work_model || ''
          employmentTypes = culture.employment_types || []
          defaultLanguages = culture.default_languages || []
        }
      }

      let benefits: CompanyBenefit[] = []
      if (companyId && responses[1]?.ok) {
        const benefitsData = await responses[1].json()
        const rawBenefits = Array.isArray(benefitsData) ? benefitsData : benefitsData.items || []
        benefits = rawBenefits
          .filter((b: Record<string, unknown>) => b.is_active !== false)
          .map((b: Record<string, unknown>) => ({
            id: b.id,
            name: b.name,
            category: b.category || 'Outros',
            isActive: b.is_active !== false,
          }))
      }

      setDefaults({ workModel, employmentTypes, defaultLanguages, benefits })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar padrões da empresa')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDefaults()
  }, [fetchDefaults])

  return { defaults, isLoading, error, refetch: fetchDefaults }
}

export default useCompanyDefaults
