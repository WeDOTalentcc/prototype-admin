"use client"

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useCompanyId } from './useCompanyId'

export const TECH_STACK_CATEGORIES = [
  { key: "backend", label: "Backend", suggestions: ["Node.js", "Python", "Java", ".NET", "Go", "Ruby", "PHP", "Rust"] },
  { key: "frontend", label: "Frontend", suggestions: ["React", "Vue.js", "Angular", "Next.js", "Svelte", "TypeScript", "HTML/CSS", "Tailwind"] },
  { key: "dados", label: "Dados", suggestions: ["PostgreSQL", "MongoDB", "MySQL", "Redis", "Elasticsearch", "Snowflake", "BigQuery", "Kafka"] },
  { key: "cloud", label: "Cloud", suggestions: ["AWS", "Azure", "GCP", "Vercel", "Heroku", "DigitalOcean", "Cloudflare"] },
  { key: "devops", label: "DevOps", suggestions: ["Docker", "Kubernetes", "Jenkins", "GitHub Actions", "Terraform", "Ansible", "GitLab CI"] },
  { key: "ia_ml", label: "IA/ML", suggestions: ["TensorFlow", "PyTorch", "OpenAI", "Anthropic", "LangChain", "Hugging Face", "scikit-learn"] },
  { key: "erps", label: "ERPs", suggestions: ["SAP", "Oracle", "Totvs", "Salesforce", "Dynamics 365", "NetSuite", "Workday"] },
  { key: "design", label: "Design", suggestions: ["Figma", "Adobe XD", "Sketch", "InVision", "Framer", "Photoshop", "Illustrator"] },
  { key: "mobile", label: "Mobile", suggestions: ["React Native", "Flutter", "Swift", "Kotlin", "iOS", "Android", "Expo"] }
] as const

export type TechCategory = typeof TECH_STACK_CATEGORIES[number]['key']

export interface TechStackByCategory {
  [key: string]: string[]
}

interface UseCompanyTechStackResult {
  techStack: string[]
  techStackByCategory: TechStackByCategory
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  getTechByCategory: (category: TechCategory) => string[]
  getAllCategories: () => typeof TECH_STACK_CATEGORIES
  getSuggestionsForCategory: (category: TechCategory) => string[]
}

const parseTechStackToCategories = (techStack: string[]): TechStackByCategory => {
  const result: TechStackByCategory = {}
  TECH_STACK_CATEGORIES.forEach(cat => { result[cat.key] = [] })
  result["outros"] = []
  
  techStack.forEach(tech => {
    const parts = tech.split(":")
    if (parts.length === 2) {
      const [category, techName] = parts
      if (result[category]) {
        result[category].push(techName)
      } else {
        result["outros"].push(tech)
      }
    } else {
      // Try to match tech to a category by checking suggestions
      let matched = false
      for (const cat of TECH_STACK_CATEGORIES) {
        if (cat.suggestions.some(s => s.toLowerCase() === tech.toLowerCase())) {
          result[cat.key].push(tech)
          matched = true
          break
        }
      }
      if (!matched) {
        result["outros"].push(tech)
      }
    }
  })
  return result
}

export function useCompanyTechStack(): UseCompanyTechStackResult {
  const [techStack, setTechStack] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { companyId, isLoading: isLoadingCompany } = useCompanyId()

  const fetchTechStack = useCallback(async () => {
    if (!companyId) return
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`)
      
      if (!response.ok) {
        if (response.status === 404) {
          setTechStack([])
          return
        }
        throw new Error(`Failed to fetch tech stack: ${response.status}`)
      }

      const data = await response.json()
      setTechStack(data.tech_stack || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setTechStack([])
    } finally {
      setIsLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    if (!isLoadingCompany && companyId) {
      fetchTechStack()
    } else if (!isLoadingCompany && !companyId) {
      setIsLoading(false)
    }
  }, [fetchTechStack, isLoadingCompany, companyId])

  const techStackByCategory = useMemo(() => 
    parseTechStackToCategories(techStack), 
    [techStack]
  )

  const getTechByCategory = useCallback((category: TechCategory): string[] => {
    return techStackByCategory[category] || []
  }, [techStackByCategory])

  const getAllCategories = useCallback(() => {
    return TECH_STACK_CATEGORIES
  }, [])

  const getSuggestionsForCategory = useCallback((category: TechCategory): string[] => {
    const cat = TECH_STACK_CATEGORIES.find(c => c.key === category)
    return cat ? [...cat.suggestions] : []
  }, [])

  return {
    techStack,
    techStackByCategory,
    isLoading,
    error,
    refetch: fetchTechStack,
    getTechByCategory,
    getAllCategories,
    getSuggestionsForCategory
  }
}

export default useCompanyTechStack
