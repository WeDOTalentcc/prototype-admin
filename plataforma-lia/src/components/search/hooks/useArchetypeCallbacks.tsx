"use client"

import { useCallback } from "react"
import {
  type ArchetypeVacancy,
  API_BASE,
} from "./smartSearchConstants"
import { useArchetypeCrud, type UseArchetypeCrudParams } from "./useArchetypeCrud"

export interface UseArchetypeCallbacksParams {
  selectedArchetype: ArchetypeVacancy | null
  editingArchetype: Record<string, unknown> | null
  editArchetypeName: string
  editArchetypeQuery: string
  editArchetypeDescription: string
  editArchetypeEmoji: string
  editArchetypeTags: string[]
  editArchetypeSkills: string[]
  editArchetypeSeniority: string
  editArchetypeIndustry: string
  editArchetypeExperienceMin: number | null
  editArchetypeLocation: string
  editArchetypeWorkModel: string
  editArchetypeLanguages: string[]
  editArchetypeEmploymentType: string
  setArchetypeVacancies: React.Dispatch<React.SetStateAction<ArchetypeVacancy[]>>
  setIsLoadingArchetypes: React.Dispatch<React.SetStateAction<boolean>>
  setClosedJobSuggestions: React.Dispatch<React.SetStateAction<Array<Record<string, unknown>>>>
  setIsLoadingClosedJobs: React.Dispatch<React.SetStateAction<boolean>>
  setJobSearchResults: React.Dispatch<React.SetStateAction<Array<{
    id: string
    title: string
    department: string | null
    seniority_level: string | null
    status: string
    created_at: string
    description: string | null
    technical_requirements: Array<Record<string, unknown>> | null
  }>>>
  setIsSearchingJobs: React.Dispatch<React.SetStateAction<boolean>>
  setIsCreatingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setArchetypeTab: React.Dispatch<React.SetStateAction<"list" | "create">>
  setSelectedArchetype: React.Dispatch<React.SetStateAction<ArchetypeVacancy | null>>
  setEditingArchetype: React.Dispatch<React.SetStateAction<Record<string, unknown> | null>>
  setEditArchetypeName: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeQuery: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeDescription: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeEmoji: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeTags: React.Dispatch<React.SetStateAction<string[]>>
  setEditArchetypeSkills: React.Dispatch<React.SetStateAction<string[]>>
  setEditArchetypeSeniority: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeIndustry: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeExperienceMin: React.Dispatch<React.SetStateAction<number | null>>
  setEditArchetypeLocation: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeWorkModel: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeLanguages: React.Dispatch<React.SetStateAction<string[]>>
  setEditArchetypeEmploymentType: React.Dispatch<React.SetStateAction<string>>
  setNewLanguageInput: React.Dispatch<React.SetStateAction<string>>
  setNewTagInput: React.Dispatch<React.SetStateAction<string>>
  setNewSkillInput: React.Dispatch<React.SetStateAction<string>>
  setJobSearchQuery: React.Dispatch<React.SetStateAction<string>>
  setArchetypeDescription: React.Dispatch<React.SetStateAction<string>>
  setShowArchetypeActions: React.Dispatch<React.SetStateAction<string | null>>
  setIsSavingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setIsDeletingArchetype: React.Dispatch<React.SetStateAction<string | null>>
}

export function useArchetypeCallbacks(params: UseArchetypeCallbacksParams) {
  const {
    setArchetypeVacancies,
    setIsLoadingArchetypes,
    setClosedJobSuggestions,
    setIsLoadingClosedJobs,
    setJobSearchResults,
    setIsSearchingJobs,
    setIsCreatingArchetype,
    setArchetypeTab,
    setSelectedArchetype,
    setEditingArchetype,
    setEditArchetypeName,
    setEditArchetypeQuery,
    setEditArchetypeDescription,
    setEditArchetypeEmoji,
    setEditArchetypeTags,
    setEditArchetypeSkills,
    setEditArchetypeSeniority,
    setEditArchetypeIndustry,
    setEditArchetypeExperienceMin,
    setEditArchetypeLocation,
    setEditArchetypeWorkModel,
    setEditArchetypeLanguages,
    setEditArchetypeEmploymentType,
    setNewLanguageInput,
    setNewTagInput,
    setNewSkillInput,
    setJobSearchQuery,
    setArchetypeDescription,
  } = params

  const loadArchetypes = useCallback(async () => {
    setIsLoadingArchetypes(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes`)
      if (response.ok) {
        const data = await response.json()
        setArchetypeVacancies(data.archetypes || [])
      }
    } catch (error) {
    } finally {
      setIsLoadingArchetypes(false)
    }
  }, [setArchetypeVacancies, setIsLoadingArchetypes])

  const loadClosedJobSuggestions = useCallback(async () => {
    setIsLoadingClosedJobs(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes/suggestions/closed-jobs?limit=5`)
      if (response.ok) {
        const data = await response.json()
        setClosedJobSuggestions(data.suggestions || [])
      }
    } catch (error) {
    } finally {
      setIsLoadingClosedJobs(false)
    }
  }, [setClosedJobSuggestions, setIsLoadingClosedJobs])

  const searchJobsForArchetype = useCallback(async (query: string) => {
    if (!query.trim()) {
      setJobSearchResults([])
      return
    }

    setIsSearchingJobs(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/job-vacancies?limit=20`)
      if (response.ok) {
        const data = await response.json()
        const jobs = data.items || []
        const queryLower = query.toLowerCase()
        const filtered = jobs.filter((job: Record<string, unknown>) =>
          (job.title as string)?.toLowerCase().includes(queryLower) ||
          (job.id as string)?.toLowerCase().includes(queryLower) ||
          (job.department as string)?.toLowerCase().includes(queryLower)
        )
        setJobSearchResults(filtered.slice(0, 10))
      }
    } catch (error) {
      setJobSearchResults([])
    } finally {
      setIsSearchingJobs(false)
    }
  }, [setJobSearchResults, setIsSearchingJobs])

  const resetArchetypeEditFields = useCallback(() => {
    setNewLanguageInput("")
    setNewTagInput("")
    setNewSkillInput("")
  }, [setNewLanguageInput, setNewTagInput, setNewSkillInput])

  const openArchetypeFromJob = useCallback((job: Record<string, unknown>) => {
    const skills: string[] = []
    if (job.technical_requirements && Array.isArray(job.technical_requirements)) {
      job.technical_requirements.forEach((req: Record<string, unknown>) => {
        if (req.skill) skills.push(req.skill as string)
        else if (typeof req === 'string') skills.push(req)
      })
    }

    const seniorityMap: Record<string, string> = {
      "Júnior": "junior", "Junior": "junior",
      "Pleno": "pleno",
      "Sênior": "senior", "Senior": "senior",
      "Especialista": "senior",
      "Lead": "lead", "Tech Lead": "lead",
      "Staff": "staff", "Principal": "principal",
      "Gerente": "manager", "Diretor": "director"
    }

    setEditingArchetype({ id: null, is_default: false, fromJob: true, jobId: job.id })
    setEditArchetypeName((job.title as string) || "")
    setEditArchetypeQuery(`${(job.title as string) || ""} ${job.department ? `${job.department}` : ""}`.trim())
    setEditArchetypeDescription((job.description as string)?.slice(0, 300) || "")
    setEditArchetypeEmoji("🎯")
    setEditArchetypeTags([job.department as string, job.status as string].filter(Boolean) as string[])
    setEditArchetypeSkills(skills.slice(0, 10))
    setEditArchetypeSeniority(seniorityMap[job.seniority_level as string] || "")
    setEditArchetypeIndustry("")
    setEditArchetypeExperienceMin(null)
    setEditArchetypeLocation("")
    setEditArchetypeWorkModel("")
    setEditArchetypeLanguages([])
    setEditArchetypeEmploymentType("")
    resetArchetypeEditFields()
    setJobSearchQuery("")
    setJobSearchResults([])
  }, [setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills, setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin, setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages, setEditArchetypeEmploymentType, resetArchetypeEditFields, setJobSearchQuery, setJobSearchResults])

  const createArchetypeFromJob = useCallback(async (jobId: string, customName?: string) => {
    setIsCreatingArchetype(true)
    try {
      let url = `${API_BASE}/api/backend-proxy/search/archetypes/from-job/${jobId}`
      if (customName) {
        url += `?custom_name=${encodeURIComponent(customName)}`
      }
      const response = await fetch(url, { method: 'POST' })
      if (response.ok) {
        const newArchetype = await response.json()
        await loadArchetypes()
        setArchetypeTab("list")
        setSelectedArchetype(newArchetype)
        return newArchetype
      }
    } catch (error) {
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [loadArchetypes, setIsCreatingArchetype, setArchetypeTab, setSelectedArchetype])

  const createArchetypeFromDescription = useCallback(async (description: string) => {
    setIsCreatingArchetype(true)
    try {
      const response = await fetch('/api/ai/extract-archetype-info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description })
      })

      let extractedData: Record<string, unknown> = {}
      if (response.ok) {
        extractedData = await response.json()
      }

      setEditingArchetype({ id: null, is_default: false, fromDescription: true })
      setEditArchetypeName((extractedData.name as string) || "Novo Arquétipo")
      setEditArchetypeQuery((extractedData.query as string) || description)
      setEditArchetypeDescription(description)
      setEditArchetypeEmoji((extractedData.emoji as string) || "🎯")
      setEditArchetypeTags((extractedData.tags as string[]) || [])
      setEditArchetypeSkills((extractedData.skills as string[]) || [])
      setEditArchetypeSeniority((extractedData.seniority as string) || "")
      setEditArchetypeIndustry((extractedData.industry as string) || "")
      setEditArchetypeExperienceMin((extractedData.experience_years_min as number) || null)
      setEditArchetypeLocation("")
      setEditArchetypeWorkModel("")
      setEditArchetypeLanguages([])
      setEditArchetypeEmploymentType("")
      resetArchetypeEditFields()
      setArchetypeDescription("")
      setArchetypeTab("list")
    } catch (error) {
      setEditingArchetype({ id: null, is_default: false, fromDescription: true })
      setEditArchetypeName("Novo Arquétipo")
      setEditArchetypeQuery(description)
      setEditArchetypeDescription(description)
      setEditArchetypeEmoji("🎯")
      setEditArchetypeTags([])
      setEditArchetypeSkills([])
      setEditArchetypeSeniority("")
      setEditArchetypeIndustry("")
      setEditArchetypeExperienceMin(null)
      setEditArchetypeLocation("")
      setEditArchetypeWorkModel("")
      setEditArchetypeLanguages([])
      setEditArchetypeEmploymentType("")
      resetArchetypeEditFields()
      setArchetypeDescription("")
      setArchetypeTab("list")
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [setIsCreatingArchetype, setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills, setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin, setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages, setEditArchetypeEmploymentType, resetArchetypeEditFields, setArchetypeDescription, setArchetypeTab])

  const crudCallbacks = useArchetypeCrud({
    selectedArchetype: params.selectedArchetype,
    editingArchetype: params.editingArchetype,
    editArchetypeName: params.editArchetypeName,
    editArchetypeQuery: params.editArchetypeQuery,
    editArchetypeDescription: params.editArchetypeDescription,
    editArchetypeEmoji: params.editArchetypeEmoji,
    editArchetypeTags: params.editArchetypeTags,
    editArchetypeSkills: params.editArchetypeSkills,
    editArchetypeSeniority: params.editArchetypeSeniority,
    editArchetypeIndustry: params.editArchetypeIndustry,
    editArchetypeExperienceMin: params.editArchetypeExperienceMin,
    editArchetypeLocation: params.editArchetypeLocation,
    editArchetypeWorkModel: params.editArchetypeWorkModel,
    editArchetypeLanguages: params.editArchetypeLanguages,
    editArchetypeEmploymentType: params.editArchetypeEmploymentType,
    loadArchetypes,
    setArchetypeTab: params.setArchetypeTab,
    setSelectedArchetype: params.setSelectedArchetype,
    setEditingArchetype: params.setEditingArchetype,
    setEditArchetypeName: params.setEditArchetypeName,
    setEditArchetypeQuery: params.setEditArchetypeQuery,
    setEditArchetypeDescription: params.setEditArchetypeDescription,
    setEditArchetypeEmoji: params.setEditArchetypeEmoji,
    setEditArchetypeTags: params.setEditArchetypeTags,
    setEditArchetypeSkills: params.setEditArchetypeSkills,
    setEditArchetypeSeniority: params.setEditArchetypeSeniority,
    setEditArchetypeIndustry: params.setEditArchetypeIndustry,
    setEditArchetypeExperienceMin: params.setEditArchetypeExperienceMin,
    setEditArchetypeLocation: params.setEditArchetypeLocation,
    setEditArchetypeWorkModel: params.setEditArchetypeWorkModel,
    setEditArchetypeLanguages: params.setEditArchetypeLanguages,
    setEditArchetypeEmploymentType: params.setEditArchetypeEmploymentType,
    setNewLanguageInput: params.setNewLanguageInput,
    setNewTagInput: params.setNewTagInput,
    setNewSkillInput: params.setNewSkillInput,
    setShowArchetypeActions: params.setShowArchetypeActions,
    setIsSavingArchetype: params.setIsSavingArchetype,
    setIsDeletingArchetype: params.setIsDeletingArchetype,
  })

  return {
    loadArchetypes,
    loadClosedJobSuggestions,
    searchJobsForArchetype,
    openArchetypeFromJob,
    createArchetypeFromJob,
    createArchetypeFromDescription,
    ...crudCallbacks,
  }
}
