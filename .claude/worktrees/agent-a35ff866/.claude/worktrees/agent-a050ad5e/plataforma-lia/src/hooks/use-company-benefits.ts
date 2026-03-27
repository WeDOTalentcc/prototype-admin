"use client"

import { useState, useEffect, useCallback } from 'react'

interface Benefit {
  id: string
  name: string
  description: string
  category: string
  value_type: string
  value?: number
  percentage_value?: number
  value_details?: string
  seniority_levels: string[]
  waiting_period_days: number
  is_mandatory: boolean
  is_active: boolean
  is_highlighted: boolean
  is_discount: boolean
  provider?: string
}

interface UseCompanyBenefitsOptions {
  seniority?: string
  department?: string
  category?: string
  activeOnly?: boolean
}

interface UseCompanyBenefitsResult {
  benefits: Benefit[]
  filteredBenefits: Benefit[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  filterBySeniority: (seniority: string) => Benefit[]
  filterByCategory: (category: string) => Benefit[]
  getHighlightedBenefits: () => Benefit[]
  getMandatoryBenefits: () => Benefit[]
}

export function useCompanyBenefits(options: UseCompanyBenefitsOptions = {}): UseCompanyBenefitsResult {
  const [benefits, setBenefits] = useState<Benefit[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchBenefits = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/backend-proxy/company/benefits/?company_id=default')
      
      if (!response.ok) {
        throw new Error(`Failed to fetch benefits: ${response.status}`)
      }

      const data = await response.json()
      const benefitsList = Array.isArray(data) ? data : data.items || []
      setBenefits(benefitsList)
    } catch (err) {
      console.error('Error fetching company benefits:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
      setBenefits([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchBenefits()
  }, [fetchBenefits])

  const filterBySeniority = useCallback((seniority: string): Benefit[] => {
    return benefits.filter(b => {
      if (!b.is_active) return false
      if (!b.seniority_levels || b.seniority_levels.length === 0) return true
      if (b.seniority_levels.includes('all')) return true
      return b.seniority_levels.includes(seniority)
    })
  }, [benefits])

  const filterByCategory = useCallback((category: string): Benefit[] => {
    return benefits.filter(b => b.is_active && b.category === category)
  }, [benefits])

  const getHighlightedBenefits = useCallback((): Benefit[] => {
    return benefits.filter(b => b.is_active && b.is_highlighted)
  }, [benefits])

  const getMandatoryBenefits = useCallback((): Benefit[] => {
    return benefits.filter(b => b.is_active && b.is_mandatory)
  }, [benefits])

  const filteredBenefits = benefits.filter(b => {
    if (options.activeOnly !== false && !b.is_active) return false
    
    if (options.seniority) {
      if (!b.seniority_levels || b.seniority_levels.length === 0) {
        // No restriction, include
      } else if (!b.seniority_levels.includes('all') && !b.seniority_levels.includes(options.seniority)) {
        return false
      }
    }
    
    if (options.category && b.category !== options.category) {
      return false
    }
    
    return true
  })

  return {
    benefits,
    filteredBenefits,
    isLoading,
    error,
    refetch: fetchBenefits,
    filterBySeniority,
    filterByCategory,
    getHighlightedBenefits,
    getMandatoryBenefits
  }
}

export default useCompanyBenefits
