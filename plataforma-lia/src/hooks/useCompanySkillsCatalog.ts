// @ts-nocheck
'use client'

import { useState, useEffect, useCallback } from 'react'

export interface Skill {
  id: string
  name: string
  category: string
  subcategory?: string
  default_weight: number
  default_level: string
  source: string
  usage_count: number
}

export interface CompanySkillsCatalog {
  technical_skills: {
    language: Skill[]
    framework: Skill[]
    database: Skill[]
    tool: Skill[]
    infrastructure: Skill[]
    general: Skill[]
  }
  behavioral_competencies: Array<{
    id: string
    name: string
    description: string
    default_weight: number
  }>
  total_technical: number
  total_behavioral: number
}

export interface SkillSuggestion {
  id: string
  name: string
  category: string
  confidence_score: number
  reason: string
}

interface UseCompanySkillsCatalogResult {
  catalog: CompanySkillsCatalog | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

interface UseSkillSuggestionsResult {
  suggestions: SkillSuggestion[]
  isLoading: boolean
  error: string | null
}

export function useCompanySkillsCatalog(companyId: string = 'default'): UseCompanySkillsCatalogResult {
  const [catalog, setCatalog] = useState<CompanySkillsCatalog | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCatalog = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `/api/backend-proxy/company/skills-catalog?company_id=${companyId}`
      )

      if (!response.ok) {
        if (response.status === 404) {
          setCatalog(null)
          return
        }
        throw new Error(`Failed to fetch skills catalog: ${response.status}`)
      }

      const data = await response.json()
      
      // Transform backend response to frontend expected format
      // Backend returns: skills_by_category, competencies, total_skills, total_competencies
      // Frontend expects: technical_skills.{language, framework, database, tool, infrastructure, general}
      // Helper to generate unique stable IDs with category prefix to avoid collisions
      const mapSkillsFromCategory = (skills: Record<string, unknown>[], category: string) =>
        (skills || []).map((s: Record<string, unknown>, i: number) => ({
          id: s.id || `${category}-skill-${s.name?.toLowerCase().replace(/\s+/g, '-') || i}`,
          name: s.name,
          category,
          subcategory: s.subcategory,
          default_weight: s.default_weight || 3,
          default_level: s.default_level || 'Intermediário',
          source: s.source || 'company_catalog',
          usage_count: s.usage_count || 0,
        }))

      const transformedCatalog: CompanySkillsCatalog = {
        technical_skills: {
          language: mapSkillsFromCategory(data.skills_by_category?.language, 'language'),
          framework: mapSkillsFromCategory(data.skills_by_category?.framework, 'framework'),
          database: mapSkillsFromCategory(data.skills_by_category?.database, 'database'),
          tool: mapSkillsFromCategory(data.skills_by_category?.tool, 'tool'),
          infrastructure: mapSkillsFromCategory(data.skills_by_category?.infrastructure, 'infrastructure'),
          general: mapSkillsFromCategory(data.skills_by_category?.general, 'general'),
        },
        behavioral_competencies: (data.competencies || []).map((c: Record<string, unknown>) => ({
          id: c.id || c.name,
          name: c.name,
          description: c.description || '',
          default_weight: c.default_weight || 3,
        })),
        total_technical: data.total_skills || 0,
        total_behavioral: data.total_competencies || 0,
      }
      
      setCatalog(transformedCatalog)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setCatalog(null)
    } finally {
      setIsLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    fetchCatalog()
  }, [fetchCatalog])

  return {
    catalog,
    isLoading,
    error,
    refetch: fetchCatalog,
  }
}

export function useSkillSuggestions(jobTitle: string, seniority: string): UseSkillSuggestionsResult {
  const [suggestions, setSuggestions] = useState<SkillSuggestion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!jobTitle || !seniority) {
      setSuggestions([])
      return
    }

    const fetchSuggestions = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const params = new URLSearchParams({
          job_title: jobTitle,
          seniority: seniority,
        })

        const response = await fetch(
          `/api/backend-proxy/wizard/suggest-skills?${params.toString()}`
        )

        if (!response.ok) {
          throw new Error(`Failed to fetch skill suggestions: ${response.status}`)
        }

        const data = await response.json()
        setSuggestions(data.suggestions || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
        setSuggestions([])
      } finally {
        setIsLoading(false)
      }
    }

    fetchSuggestions()
  }, [jobTitle, seniority])

  return {
    suggestions,
    isLoading,
    error,
  }
}
