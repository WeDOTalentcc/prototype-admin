"use client"

import { useCallback } from "react"
import {
  type ArchetypeVacancy,
  API_BASE,
} from "./smartSearchConstants"

export interface UseArchetypeCrudParams {
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
  loadArchetypes: () => Promise<void>
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
  setShowArchetypeActions: React.Dispatch<React.SetStateAction<string | null>>
  setIsSavingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setIsDeletingArchetype: React.Dispatch<React.SetStateAction<string | null>>
}

export function useArchetypeCrud(params: UseArchetypeCrudParams) {
  const {
    selectedArchetype,
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
    loadArchetypes,
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
    setShowArchetypeActions,
    setIsSavingArchetype,
    setIsDeletingArchetype,
  } = params

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
    openEditArchetype,
    closeEditArchetype,
    saveArchetype,
    deleteArchetype,
    buildArchetypePrompt,
  }
}
