"use client"

import { useState, useCallback } from "react"
import { type ArchetypeVacancy, API_BASE } from "./smartSearchConstants"

export interface ArchetypeState {
  archetypeVacancies: ArchetypeVacancy[]
  selectedArchetype: ArchetypeVacancy | null
  isLoadingArchetypes: boolean
  archetypeSearch: string
  archetypeTab: "list" | "create"
  archetypeCreateMode: "job" | "description"
  closedJobSuggestions: ArchetypeVacancy[]
  isLoadingClosedJobs: boolean
  jobSearchQuery: string
  jobSearchResults: Array<{
    id: string
    title: string
    department: string | null
    seniority_level: string | null
    status: string
    created_at: string
    description: string | null
    technical_requirements: Array<Record<string, unknown>> | null
  }>
  isSearchingJobs: boolean
  archetypeDescription: string
  isCreatingArchetype: boolean
  editingArchetype: ArchetypeVacancy | null
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
  newLanguageInput: string
  newTagInput: string
  newSkillInput: string
  isSavingArchetype: boolean
  isDeletingArchetype: string | null
  showArchetypeActions: string | null
  expandedArchetypeId: string | null
  skillSuggestions: string[]
  isLoadingSkillSuggestions: boolean
  isFindingSimilarSkills: boolean
  tagSuggestions: string[]
  isLoadingTagSuggestions: boolean
  isFindingSimilarTags: boolean
  aiSuggestedSkills: string[]
  selectedAiSkills: string[]
  showSkillSuggestions: boolean
  aiSuggestedTags: string[]
  selectedAiTags: string[]
  showTagSuggestions: boolean
  industrySearchQuery: string
  isIndustryDropdownOpen: boolean
  archetypeSearchPrompt: string
}

export function useSmartSearchArchetypes() {
  const [archetypeVacancies, setArchetypeVacancies] = useState<ArchetypeVacancy[]>([])
  const [selectedArchetype, setSelectedArchetype] = useState<ArchetypeVacancy | null>(null)
  const [isLoadingArchetypes, setIsLoadingArchetypes] = useState(false)
  const [archetypeSearch, setArchetypeSearch] = useState("")
  const [archetypeTab, setArchetypeTab] = useState<"list" | "create">("list")
  const [archetypeCreateMode, setArchetypeCreateMode] = useState<"job" | "description">("job")
  const [closedJobSuggestions, setClosedJobSuggestions] = useState<any[]>([])
  const [isLoadingClosedJobs, setIsLoadingClosedJobs] = useState(false)
  const [jobSearchQuery, setJobSearchQuery] = useState("")
  const [jobSearchResults, setJobSearchResults] = useState<Array<{
    id: string
    title: string
    department: string | null
    seniority_level: string | null
    status: string
    created_at: string
    description: string | null
    technical_requirements: Array<Record<string, unknown>> | null
  }>>([])
  const [isSearchingJobs, setIsSearchingJobs] = useState(false)
  const [archetypeDescription, setArchetypeDescription] = useState("")
  const [isCreatingArchetype, setIsCreatingArchetype] = useState(false)
  const [editingArchetype, setEditingArchetype] = useState<any | null>(null)
  const [editArchetypeName, setEditArchetypeName] = useState("")
  const [editArchetypeQuery, setEditArchetypeQuery] = useState("")
  const [editArchetypeDescription, setEditArchetypeDescription] = useState("")
  const [editArchetypeEmoji, setEditArchetypeEmoji] = useState("")
  const [editArchetypeTags, setEditArchetypeTags] = useState<string[]>([])
  const [editArchetypeSkills, setEditArchetypeSkills] = useState<string[]>([])
  const [editArchetypeSeniority, setEditArchetypeSeniority] = useState("")
  const [editArchetypeIndustry, setEditArchetypeIndustry] = useState("")
  const [editArchetypeExperienceMin, setEditArchetypeExperienceMin] = useState<number | null>(null)
  const [editArchetypeLocation, setEditArchetypeLocation] = useState("")
  const [editArchetypeWorkModel, setEditArchetypeWorkModel] = useState("")
  const [editArchetypeLanguages, setEditArchetypeLanguages] = useState<string[]>([])
  const [editArchetypeEmploymentType, setEditArchetypeEmploymentType] = useState("")
  const [newLanguageInput, setNewLanguageInput] = useState("")
  const [newTagInput, setNewTagInput] = useState("")
  const [newSkillInput, setNewSkillInput] = useState("")
  const [isSavingArchetype, setIsSavingArchetype] = useState(false)
  const [isDeletingArchetype, setIsDeletingArchetype] = useState<string | null>(null)
  const [showArchetypeActions, setShowArchetypeActions] = useState<string | null>(null)
  const [expandedArchetypeId, setExpandedArchetypeId] = useState<string | null>(null)
  const [skillSuggestions, setSkillSuggestions] = useState<string[]>([])
  const [isLoadingSkillSuggestions, setIsLoadingSkillSuggestions] = useState(false)
  const [isFindingSimilarSkills, setIsFindingSimilarSkills] = useState(false)
  const [tagSuggestions, setTagSuggestions] = useState<string[]>([])
  const [isLoadingTagSuggestions, setIsLoadingTagSuggestions] = useState(false)
  const [isFindingSimilarTags, setIsFindingSimilarTags] = useState(false)
  const [aiSuggestedSkills, setAiSuggestedSkills] = useState<string[]>([])
  const [selectedAiSkills, setSelectedAiSkills] = useState<string[]>([])
  const [showSkillSuggestions, setShowSkillSuggestions] = useState(false)
  const [aiSuggestedTags, setAiSuggestedTags] = useState<string[]>([])
  const [selectedAiTags, setSelectedAiTags] = useState<string[]>([])
  const [showTagSuggestions, setShowTagSuggestions] = useState(false)
  const [industrySearchQuery, setIndustrySearchQuery] = useState("")
  const [isIndustryDropdownOpen, setIsIndustryDropdownOpen] = useState(false)
  const [archetypeSearchPrompt, setArchetypeSearchPrompt] = useState("")

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
  }, [])

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
  }, [])

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
  }, [])

  const openArchetypeFromJob = useCallback((job: Record<string, unknown>) => {
    const skills: string[] = []
    if (job.technical_requirements && Array.isArray(job.technical_requirements)) {
      job.technical_requirements.forEach((req: Record<string, unknown>) => {
        if (req.skill) skills.push(req.skill as string)
        else if (typeof req === "string") skills.push(req)
      })
    }

    const seniorityMap: Record<string, string> = {
      "Júnior": "junior",
      "Junior": "junior",
      "Pleno": "pleno",
      "Sênior": "senior",
      "Senior": "senior",
      "Especialista": "senior",
      "Lead": "lead",
      "Tech Lead": "lead",
      "Staff": "staff",
      "Principal": "principal",
      "Gerente": "manager",
      "Diretor": "director"
    }

    setEditingArchetype({ id: null, is_default: false, fromJob: true, jobId: job.id })
    setEditArchetypeName((job.title as string) || "")
    setEditArchetypeQuery(`${job.title || ""} ${job.department ? `${job.department}` : ""}`.trim())
    setEditArchetypeDescription(((job.description as string) || "").slice(0, 300))
    setEditArchetypeEmoji("🎯")
    setEditArchetypeTags([job.department, job.status].filter(Boolean) as string[])
    setEditArchetypeSkills(skills.slice(0, 10))
    setEditArchetypeSeniority(seniorityMap[(job.seniority_level as string)] || "")
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
  }, [])

  const createArchetypeFromJob = useCallback(async (jobId: string, customName?: string) => {
    setIsCreatingArchetype(true)
    try {
      let url = `${API_BASE}/api/backend-proxy/search/archetypes/from-job/${jobId}`
      if (customName) {
        url += `?custom_name=${encodeURIComponent(customName)}`
      }
      const response = await fetch(url, { method: "POST" })
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
  }, [loadArchetypes])

  const createArchetypeFromDescription = useCallback(async (description: string) => {
    setIsCreatingArchetype(true)
    try {
      const response = await fetch("/api/ai/extract-archetype-info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
  }, [])

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
  }, [])

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
  }, [])

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
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        })
      } else {
        response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
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
  }, [
    editingArchetype, editArchetypeName, editArchetypeQuery, editArchetypeDescription,
    editArchetypeEmoji, editArchetypeTags, editArchetypeSkills, editArchetypeSeniority,
    editArchetypeIndustry, editArchetypeExperienceMin, editArchetypeLocation,
    editArchetypeWorkModel, editArchetypeLanguages, editArchetypeEmploymentType,
    loadArchetypes, closeEditArchetype
  ])

  const deleteArchetype = useCallback(async (archId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm("Tem certeza que deseja excluir este arquétipo?")) return

    setIsDeletingArchetype(archId)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search/archetypes/${archId}/`, {
        method: "DELETE"
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
  }, [loadArchetypes, selectedArchetype])

  const buildArchetypePrompt = useCallback((arch: Record<string, unknown>): string => {
    const parts: string[] = []

    if (arch.query) {
      parts.push(arch.query as string)
    }

    const filters = arch.filters as Record<string, unknown> | undefined
    if (filters?.skills && Array.isArray(filters.skills) && filters.skills.length > 0) {
      parts.push(`Skills: ${(filters.skills as string[]).join(", ")}`)
    } else if (arch.tags && Array.isArray(arch.tags) && (arch.tags as string[]).length > 0) {
      parts.push(`Tags: ${(arch.tags as string[]).join(", ")}`)
    }

    if (arch.seniority) {
      const seniorityMap: Record<string, string> = {
        junior: "Júnior",
        pleno: "Pleno",
        senior: "Sênior",
        lead: "Lead/Tech Lead",
        staff: "Staff",
        principal: "Principal",
        manager: "Gerente",
        director: "Diretor",
        executive: "Executivo"
      }
      parts.push(`Senioridade: ${seniorityMap[arch.seniority as string] || arch.seniority}`)
    }

    if (arch.industry) {
      const industryMap: Record<string, string> = {
        technology: "Tecnologia",
        fintech: "Fintech/Finanças",
        healthcare: "Saúde",
        education: "Educação",
        ecommerce: "E-commerce/Varejo",
        logistics: "Logística",
        consulting: "Consultoria",
        manufacturing: "Indústria/Manufatura",
        agritech: "Agronegócio",
        other: "Outro"
      }
      parts.push(`Indústria: ${industryMap[arch.industry as string] || arch.industry}`)
    }

    if (filters?.experience_years_min) {
      parts.push(`${filters.experience_years_min}+ anos de experiência`)
    }

    if (parts.length === 0) {
      return `Buscar candidatos similares ao arquétipo "${arch.name || arch.title}"`
    }

    return parts.join(", ")
  }, [])

  return {
    // State
    archetypeVacancies,
    selectedArchetype,
    isLoadingArchetypes,
    archetypeSearch,
    archetypeTab,
    archetypeCreateMode,
    closedJobSuggestions,
    isLoadingClosedJobs,
    jobSearchQuery,
    jobSearchResults,
    isSearchingJobs,
    archetypeDescription,
    isCreatingArchetype,
    editingArchetype,
    editArchetypeName,
    editArchetypeQuery,
    editArchetypeDescription,
    editArchetypeEmoji,
    editArchetypeTags,
    editArchetypeSkills,
    editArchetypeSeniority,
    editArchetypeIndustry,
    editArchetypeExperienceMin,
    editArchetypeLocation,
    editArchetypeWorkModel,
    editArchetypeLanguages,
    editArchetypeEmploymentType,
    newLanguageInput,
    newTagInput,
    newSkillInput,
    isSavingArchetype,
    isDeletingArchetype,
    showArchetypeActions,
    expandedArchetypeId,
    skillSuggestions,
    isLoadingSkillSuggestions,
    isFindingSimilarSkills,
    tagSuggestions,
    isLoadingTagSuggestions,
    isFindingSimilarTags,
    aiSuggestedSkills,
    selectedAiSkills,
    showSkillSuggestions,
    aiSuggestedTags,
    selectedAiTags,
    showTagSuggestions,
    industrySearchQuery,
    isIndustryDropdownOpen,
    archetypeSearchPrompt,
    // Setters
    setArchetypeVacancies,
    setSelectedArchetype,
    setArchetypeSearch,
    setArchetypeTab,
    setArchetypeCreateMode,
    setArchetypeDescription,
    setJobSearchQuery,
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
    setShowArchetypeActions,
    setExpandedArchetypeId,
    setAiSuggestedSkills,
    setSelectedAiSkills,
    setShowSkillSuggestions,
    setAiSuggestedTags,
    setSelectedAiTags,
    setShowTagSuggestions,
    setIndustrySearchQuery,
    setIsIndustryDropdownOpen,
    setArchetypeSearchPrompt,
    setIsFindingSimilarSkills,
    setIsFindingSimilarTags,
    // Callbacks
    loadArchetypes,
    loadClosedJobSuggestions,
    searchJobsForArchetype,
    openArchetypeFromJob,
    createArchetypeFromJob,
    createArchetypeFromDescription,
    openEditArchetype,
    closeEditArchetype,
    saveArchetype,
    deleteArchetype,
    buildArchetypePrompt,
  }
}
