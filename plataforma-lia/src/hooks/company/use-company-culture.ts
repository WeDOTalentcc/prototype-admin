"use client"

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useCompanyId } from './useCompanyId'

export interface BigFiveProfile {
  openness: number
  conscientiousness: number
  extraversion: number
  agreeableness: number
  stability: number
}

export interface CultureProfile {
  mission?: string
  vision?: string
  values?: string[]
  coreCompetencies?: string[]
  evpBullets?: string[]
  workModel?: string
  growthOpportunities?: string
  teamDynamics?: string
  leadershipStyle?: string
  deiInitiatives?: string
  sustainability?: string
  socialImpact?: string
  engineeringCulture?: string
  defaultLanguages?: string[]
  bigFive: BigFiveProfile
}

interface UseCompanyCultureResult {
  culture: CultureProfile | null
  bigFive: BigFiveProfile
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  hasProfileData: boolean
  getIdealBigFiveForRole: (department?: string, seniority?: string) => BigFiveProfile
  getArchetypeDescription: () => string
}

const DEFAULT_BIG_FIVE: BigFiveProfile = {
  openness: 50,
  conscientiousness: 50,
  extraversion: 50,
  agreeableness: 50,
  stability: 50
}

const ARCHETYPE_DESCRIPTIONS: Record<string, { name: string, description: string }> = {
  'high-openness': { name: 'Inovador', description: 'Perfil criativo e aberto a novas ideias' },
  'high-conscientiousness': { name: 'Metódico', description: 'Perfil organizado e orientado a resultados' },
  'high-extraversion': { name: 'Comunicador', description: 'Perfil sociável e energético' },
  'high-agreeableness': { name: 'Colaborador', description: 'Perfil cooperativo e empático' },
  'high-stability': { name: 'Resiliente', description: 'Perfil estável e equilibrado' },
  'balanced': { name: 'Versátil', description: 'Perfil equilibrado em todas as dimensões' }
}

export function useCompanyCulture(): UseCompanyCultureResult {
  const [culture, setCulture] = useState<CultureProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { companyId, isLoading: isLoadingCompany } = useCompanyId()

  const fetchCulture = useCallback(async () => {
    if (!companyId) return
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`)
      
      if (!response.ok) {
        if (response.status === 404) {
          setCulture(null)
          return
        }
        throw new Error(`Failed to fetch culture profile: ${response.status}`)
      }

      const data = await response.json()
      
      if (data.notFound) {
        setCulture(null)
        return
      }

      setCulture({
        mission: data.mission,
        vision: data.vision,
        values: data.values || [],
        coreCompetencies: data.core_competencies || [],
        evpBullets: data.evp_bullets || [],
        workModel: data.work_model,
        growthOpportunities: data.growth_opportunities,
        teamDynamics: data.team_dynamics,
        leadershipStyle: data.leadership_style,
        deiInitiatives: data.dei_initiatives,
        sustainability: data.sustainability,
        socialImpact: data.social_impact,
        engineeringCulture: data.engineering_culture,
        defaultLanguages: data.default_languages || [],
        bigFive: {
          openness: data.openness_score ?? 50,
          conscientiousness: data.conscientiousness_score ?? 50,
          extraversion: data.extraversion_score ?? 50,
          agreeableness: data.agreeableness_score ?? 50,
          stability: data.stability_score ?? 50
        }
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setCulture(null)
    } finally {
      setIsLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    if (!isLoadingCompany && companyId) {
      fetchCulture()
    } else if (!isLoadingCompany && !companyId) {
      setIsLoading(false)
    }
  }, [fetchCulture, isLoadingCompany, companyId])

  const bigFive = useMemo(() => {
    return culture?.bigFive || DEFAULT_BIG_FIVE
  }, [culture])

  const hasProfileData = useMemo(() => {
    if (!culture) return false
    return !!(culture.mission || culture.vision || (culture.values && culture.values.length > 0))
  }, [culture])

  const getIdealBigFiveForRole = useCallback((department?: string, seniority?: string): BigFiveProfile => {
    const base = culture?.bigFive || DEFAULT_BIG_FIVE
    
    // Adjust based on department
    const adjustments: BigFiveProfile = { ...base }
    
    if (department) {
      const deptLower = department.toLowerCase()
      
      if (deptLower.includes('tech') || deptLower.includes('eng') || deptLower.includes('dev')) {
        adjustments.openness = Math.min(100, base.openness + 10)
        adjustments.conscientiousness = Math.min(100, base.conscientiousness + 10)
      } else if (deptLower.includes('sales') || deptLower.includes('comercial') || deptLower.includes('vendas')) {
        adjustments.extraversion = Math.min(100, base.extraversion + 15)
        adjustments.agreeableness = Math.min(100, base.agreeableness + 5)
      } else if (deptLower.includes('rh') || deptLower.includes('people') || deptLower.includes('hr')) {
        adjustments.agreeableness = Math.min(100, base.agreeableness + 15)
        adjustments.extraversion = Math.min(100, base.extraversion + 10)
      } else if (deptLower.includes('finance') || deptLower.includes('financ')) {
        adjustments.conscientiousness = Math.min(100, base.conscientiousness + 15)
        adjustments.stability = Math.min(100, base.stability + 10)
      } else if (deptLower.includes('marketing') || deptLower.includes('design') || deptLower.includes('criat')) {
        adjustments.openness = Math.min(100, base.openness + 20)
        adjustments.extraversion = Math.min(100, base.extraversion + 5)
      }
    }
    
    // Adjust based on seniority
    if (seniority) {
      const seniorityLower = seniority.toLowerCase()
      
      if (seniorityLower.includes('senior') || seniorityLower.includes('sênior') || seniorityLower.includes('lead')) {
        adjustments.conscientiousness = Math.min(100, adjustments.conscientiousness + 5)
        adjustments.stability = Math.min(100, adjustments.stability + 5)
      } else if (seniorityLower.includes('manager') || seniorityLower.includes('gerente') || seniorityLower.includes('coord')) {
        adjustments.extraversion = Math.min(100, adjustments.extraversion + 10)
        adjustments.conscientiousness = Math.min(100, adjustments.conscientiousness + 5)
        adjustments.stability = Math.min(100, adjustments.stability + 10)
      } else if (seniorityLower.includes('director') || seniorityLower.includes('diretor') || seniorityLower.includes('c-level') || seniorityLower.includes('vp')) {
        adjustments.stability = Math.min(100, adjustments.stability + 15)
        adjustments.conscientiousness = Math.min(100, adjustments.conscientiousness + 10)
        adjustments.extraversion = Math.min(100, adjustments.extraversion + 10)
      }
    }
    
    return adjustments
  }, [culture])

  const getArchetypeDescription = useCallback((): string => {
    const bf = bigFive
    const maxTrait = Object.entries(bf).reduce((max, [key, value]) => {
      return value > max.value ? { key, value } : max
    }, { key: 'balanced', value: 0 })
    
    // Check if balanced (all traits within 15 points of each other)
    const values = Object.values(bf)
    const minVal = Math.min(...values)
    const maxVal = Math.max(...values)
    
    if (maxVal - minVal <= 15) {
      return ARCHETYPE_DESCRIPTIONS['balanced'].description
    }
    
    const archetypeKey = `high-${maxTrait.key}`
    return ARCHETYPE_DESCRIPTIONS[archetypeKey]?.description || ARCHETYPE_DESCRIPTIONS['balanced'].description
  }, [bigFive])

  return {
    culture,
    bigFive,
    isLoading,
    error,
    refetch: fetchCulture,
    hasProfileData,
    getIdealBigFiveForRole,
    getArchetypeDescription
  }
}

export default useCompanyCulture
