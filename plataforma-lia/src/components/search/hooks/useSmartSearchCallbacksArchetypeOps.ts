"use client"

import { useCallback } from "react"
import { API_BASE } from "./smartSearchConstants"
import type { UseSmartSearchCallbacksParams } from "./useSmartSearchCallbackTypes"

export function useCallbacksArchetypeOps(params: UseSmartSearchCallbacksParams) {
  const {
    setArchetypeVacancies, setIsLoadingArchetypes, setClosedJobSuggestions, setIsLoadingClosedJobs,
    setJobSearchResults, setIsSearchingJobs, setIsCreatingArchetype, setArchetypeTab,
    setSelectedArchetype, setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery,
    setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills,
    setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin,
    setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages,
    setEditArchetypeEmploymentType, setNewLanguageInput, setNewTagInput, setNewSkillInput,
    setJobSearchQuery, setArchetypeDescription, setShowArchetypeActions,
    setIsSavingArchetype, setIsDeletingArchetype,
    selectedArchetype, editingArchetype, editArchetypeName, editArchetypeQuery,
    editArchetypeDescription, editArchetypeEmoji, editArchetypeTags, editArchetypeSkills,
    editArchetypeSeniority, editArchetypeIndustry, editArchetypeExperienceMin,
    editArchetypeLocation, editArchetypeWorkModel, editArchetypeLanguages, editArchetypeEmploymentType,
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
    setNewLanguageInput("")
    setNewTagInput("")
    setNewSkillInput("")
    setJobSearchQuery("")
    setJobSearchResults([])
  }, [setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills, setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin, setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages, setEditArchetypeEmploymentType, setNewLanguageInput, setNewTagInput, setNewSkillInput, setJobSearchQuery, setJobSearchResults])

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
      setNewLanguageInput("")
      setNewTagInput("")
      setNewSkillInput("")
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
      setNewLanguageInput("")
      setNewTagInput("")
      setNewSkillInput("")
      setArchetypeDescription("")
      setArchetypeTab("list")
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [setIsCreatingArchetype, setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills, setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin, setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages, setEditArchetypeEmploymentType, setNewLanguageInput, setNewTagInput, setNewSkillInput, setArchetypeDescription, setArchetypeTab])

  const openEditArchetype = useCallback((arch: Record<string, unknown>, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingArchetype(arch)
    setEditArchetypeName((arch.name as string) || (arch.title as string) || "")
    setEditArchetypeQuery((arch.query as string) || "")
    setEditArchetypeDescription((arch.description as string) || "")
    setEditArchetypeEmoji((arch.emoji as string) || "🎯")
    setEditArchetypeTags((arch.tags as string[]) || [])
    setEditArchetypeSkills(((arch.filters as Record<string, unknown>)?.skills as string[]) || [])
    setEditArchetypeSeniority((arch.seniority as string) || ((arch.filters as Record<string, unknown>)?.seniority as string) || "")
    setEditArchetypeIndustry((arch.industry as string) || "")
    setEditArchetypeExperienceMin(((arch.filters as Record<string, unknown>)?.experience_years_min as number) || null)
    setEditArchetypeLocation(((arch.filters as Record<string, unknown>)?.location as string) || "")
    setEditArchetypeWorkModel(((arch.filters as Record<string, unknown>)?.work_model as string) || "")
    setEditArchetypeLanguages(((arch.filters as Record<string, unknown>)?.languages as string[]) || [])
    setEditArchetypeEmploymentType(((arch.filters as Record<string, unknown>)?.employment_type as string) || "")
    setNewTagInput("")
    setNewSkillInput("")
    setNewLanguageInput("")
    setShowArchetypeActions(null)
  }, [setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills, setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin, setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages, setEditArchetypeEmploymentType, setNewTagInput, setNewSkillInput, setNewLanguageInput, setShowArchetypeActions])

  const closeEditArchetype = useCallback(() => {
    setEditingArchetype(null)
    setEditArchetypeName("")
    setEditArchetypeQuery("")
    setEditArchetypeDescription("")
    setEditArchetypeEmoji("")
    setEditArchetypeTags([])
    setEditArchetypeSkills([])
    setEditArchetypeSeniority("")
    setEditArchetypeIndustry("")
    setEditArchetypeExperienceMin(null)
    setEditArchetypeLocation("")
    setEditArchetypeWorkModel("")
    setEditArchetypeLanguages([])
    setEditArchetypeEmploymentType("")
    setNewLanguageInput("")
    setNewTagInput("")
    setNewSkillInput("")
  }, [setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills, setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin, setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages, setEditArchetypeEmploymentType, setNewLanguageInput, setNewTagInput, setNewSkillInput])

  const saveArchetype = useCallback(async () => {
    if (!editingArchetype || !editArchetypeName.trim() || !editArchetypeQuery.trim()) return
    setIsSavingArchetype(true)
    try {
      const filters: Record<string, unknown> = {}
      if (editArchetypeSkills.length > 0) filters.skills = editArchetypeSkills
      if (editArchetypeSeniority) filters.seniority = editArchetypeSeniority
      if (editArchetypeExperienceMin !== null && editArchetypeExperienceMin > 0) {
        filters.experience_years_min = editArchetypeExperienceMin
      }
      if (editArchetypeLocation) filters.location = editArchetypeLocation
      if (editArchetypeWorkModel) filters.work_model = editArchetypeWorkModel
      if (editArchetypeLanguages.length > 0) filters.languages = editArchetypeLanguages
      if (editArchetypeEmploymentType) filters.employment_type = editArchetypeEmploymentType
      const payload = {
        name: editArchetypeName.trim(),
        query: editArchetypeQuery.trim(),
        description: editArchetypeDescription.trim() || null,
        emoji: editArchetypeEmoji || "🎯",
        tags: editArchetypeTags,
        seniority: editArchetypeSeniority || null,
        industry: editArchetypeIndustry || null,
        filters: Object.keys(filters).length > 0 ? filters : null
      }
      let response: Response
      if (editingArchetype.id) {
        response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes/${editingArchetype.id}/`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
      } else {
        response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
      }
      if (response.ok) {
        await loadArchetypes()
        closeEditArchetype()
        setArchetypeTab("list")
      } else {
        const error = await response.json()
        alert(error.detail || "Erro ao salvar arquétipo")
      }
    } catch (error) {
    } finally {
      setIsSavingArchetype(false)
    }
  }, [editingArchetype, editArchetypeName, editArchetypeQuery, editArchetypeDescription, editArchetypeEmoji, editArchetypeTags, editArchetypeSkills, editArchetypeSeniority, editArchetypeIndustry, editArchetypeExperienceMin, editArchetypeLocation, editArchetypeWorkModel, editArchetypeLanguages, editArchetypeEmploymentType, loadArchetypes, closeEditArchetype, setIsSavingArchetype, setArchetypeTab])

  const deleteArchetype = useCallback(async (archId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm("Tem certeza que deseja excluir este arquétipo?")) return
    setIsDeletingArchetype(archId)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes/${archId}/`, {
        method: 'DELETE'
      })
      if (response.ok) {
        await loadArchetypes()
        if (selectedArchetype?.id === archId) {
          setSelectedArchetype(null)
        }
      } else {
        const error = await response.json()
        alert(error.detail || "Erro ao excluir arquétipo")
      }
    } catch (error) {
    } finally {
      setIsDeletingArchetype(null)
      setShowArchetypeActions(null)
    }
  }, [loadArchetypes, selectedArchetype, setIsDeletingArchetype, setSelectedArchetype, setShowArchetypeActions])

  const buildArchetypePrompt = useCallback((arch: Record<string, unknown>): string => {
    const parts: string[] = []
    if (arch.query) {
      parts.push(arch.query as string)
    }
    if ((arch.filters as Record<string, unknown>)?.skills && ((arch.filters as Record<string, unknown>)?.skills as string[]).length > 0) {
      parts.push(`Skills: ${((arch.filters as Record<string, unknown>)?.skills as string[]).join(", ")}`)
    } else if (arch.tags && (arch.tags as string[]).length > 0) {
      parts.push(`Tags: ${(arch.tags as string[]).join(", ")}`)
    }
    if (arch.seniority) {
      const seniorityMap: Record<string, string> = {
        junior: "Júnior", pleno: "Pleno", senior: "Sênior",
        lead: "Lead/Tech Lead", staff: "Staff", principal: "Principal",
        manager: "Gerente", director: "Diretor", executive: "Executivo"
      }
      parts.push(`Senioridade: ${seniorityMap[arch.seniority as string] || arch.seniority}`)
    }
    if (arch.industry) {
      const industryMap: Record<string, string> = {
        technology: "Tecnologia", fintech: "Fintech/Finanças",
        healthcare: "Saúde", education: "Educação",
        ecommerce: "E-commerce/Varejo", logistics: "Logística",
        consulting: "Consultoria", manufacturing: "Indústria/Manufatura",
        agritech: "Agronegócio", other: "Outro"
      }
      parts.push(`Indústria: ${industryMap[arch.industry as string] || arch.industry}`)
    }
    if ((arch.filters as Record<string, unknown>)?.experience_years_min) {
      parts.push(`${(arch.filters as Record<string, unknown>)?.experience_years_min}+ anos de experiência`)
    }
    if (parts.length === 0) {
      return `Buscar candidatos similares ao arquétipo "${(arch.name as string) || (arch.title as string)}"`
    }
    return parts.join(", ")
  }, [])

  return {
    loadArchetypes, loadClosedJobSuggestions, searchJobsForArchetype,
    openArchetypeFromJob, createArchetypeFromJob, createArchetypeFromDescription,
    openEditArchetype, closeEditArchetype, saveArchetype, deleteArchetype,
    buildArchetypePrompt,
  }
}
