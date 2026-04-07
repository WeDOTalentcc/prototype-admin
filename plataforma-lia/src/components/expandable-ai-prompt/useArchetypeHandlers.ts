"use client"

import { useCallback } from "react"
import React from "react"
import { toast } from "sonner"

interface BackendEntities {
  location?: string
  job_title?: string
  years_experience?: string
  industry?: string
  skills?: string[]
  seniority?: string
  company?: string
}

interface ArchetypeData {
  id: string
  name: string
  description?: string
  department?: string
  hired_candidate?: { name: string }
  criteria?: Record<string, unknown>
}

interface SearchFilters {
  ppiOptions: Record<string, unknown>
  general: Record<string, unknown>
  locations: Record<string, unknown>
  job: Record<string, unknown>
  company: Record<string, unknown>
  skills: Record<string, unknown>
  education: Record<string, unknown>
  languages: Record<string, unknown>
}

interface UseArchetypeHandlersParams {
  parsedEntities: BackendEntities
  advancedFilters: SearchFilters
  naturalSearchValue: string
  editingArchetype: ArchetypeData | null
  editArchetypeName: string
  editArchetypeQuery: string
  editArchetypeDescription: string
  editArchetypeEmoji: string
  editArchetypeTags: string[]
  archetypeToDelete: { id: string; name: string } | null
  setArchetypes: React.Dispatch<React.SetStateAction<ArchetypeData[]>>
  setIsCreatingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setSelectedJobForArchetype: React.Dispatch<React.SetStateAction<string | null>>
  setIsCreatingFromSearch: React.Dispatch<React.SetStateAction<boolean>>
  setNewArchetypeDescription: React.Dispatch<React.SetStateAction<string>>
  setEditingArchetype: React.Dispatch<React.SetStateAction<ArchetypeData | null>>
  setEditArchetypeName: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeQuery: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeDescription: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeEmoji: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeTags: React.Dispatch<React.SetStateAction<string[]>>
  setNewTagInput: React.Dispatch<React.SetStateAction<string>>
  setIsSavingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setIsDeletingArchetype: React.Dispatch<React.SetStateAction<string | null>>
  setShowDeleteArchetypeDialog: React.Dispatch<React.SetStateAction<boolean>>
  setArchetypeToDelete: React.Dispatch<React.SetStateAction<{ id: string; name: string } | null>>
}

export function useArchetypeHandlers(params: UseArchetypeHandlersParams) {
  const {
    parsedEntities,
    advancedFilters,
    naturalSearchValue,
    editingArchetype,
    editArchetypeName,
    editArchetypeQuery,
    editArchetypeDescription,
    editArchetypeEmoji,
    editArchetypeTags,
    archetypeToDelete,
    setArchetypes,
    setIsCreatingArchetype,
    setSelectedJobForArchetype,
    setIsCreatingFromSearch,
    setNewArchetypeDescription,
    setEditingArchetype,
    setEditArchetypeName,
    setEditArchetypeQuery,
    setEditArchetypeDescription,
    setEditArchetypeEmoji,
    setEditArchetypeTags,
    setNewTagInput,
    setIsSavingArchetype,
    setIsDeletingArchetype,
    setShowDeleteArchetypeDialog,
    setArchetypeToDelete,
  } = params

  const hasParsedEntities = useCallback(() => {
    return !!(
      parsedEntities.job_title ||
      parsedEntities.location ||
      parsedEntities.seniority ||
      parsedEntities.industry ||
      parsedEntities.company ||
      parsedEntities.years_experience ||
      (parsedEntities.skills && parsedEntities.skills.length > 0)
    )
  }, [parsedEntities])

  const buildSearchSpec = useCallback(() => {
    const spec: Record<string, unknown> = {}

    if (parsedEntities.job_title) spec.job_title = parsedEntities.job_title
    if (parsedEntities.location) spec.location = parsedEntities.location
    if (parsedEntities.seniority) spec.seniority = parsedEntities.seniority
    if (parsedEntities.industry) spec.industry = parsedEntities.industry
    if (parsedEntities.company) spec.company = parsedEntities.company
    if (parsedEntities.years_experience) spec.years_experience = parsedEntities.years_experience
    if (parsedEntities.skills && parsedEntities.skills.length > 0) {
      spec.skills = parsedEntities.skills
    }

    if (advancedFilters.locations?.locations && (advancedFilters.locations.locations as string[]).length > 0) {
      spec.locations = advancedFilters.locations.locations
    }
    if (advancedFilters.job?.titles && (advancedFilters.job.titles as string[]).length > 0) {
      spec.job_titles = advancedFilters.job.titles
    }
    if (advancedFilters.job?.levels && (advancedFilters.job.levels as string[]).length > 0) {
      spec.seniority_levels = advancedFilters.job.levels
    }
    if (advancedFilters.skills?.skillItems && (advancedFilters.skills.skillItems as Array<{ name: string }>).length > 0) {
      spec.required_skills = (advancedFilters.skills.skillItems as Array<{ name: string }>).map(s => s.name)
    }
    if (advancedFilters.languages?.languages && (advancedFilters.languages.languages as string[]).length > 0) {
      spec.languages = advancedFilters.languages.languages
    }
    if (advancedFilters.general?.minExperience) {
      spec.years_experience_min = advancedFilters.general.minExperience
    }
    if (advancedFilters.general?.maxExperience) {
      spec.years_experience_max = advancedFilters.general.maxExperience
    }

    return spec
  }, [parsedEntities, advancedFilters])

  const generateArchetypeName = useCallback(() => {
    const nameParts: string[] = []
    if (parsedEntities.job_title) nameParts.push(parsedEntities.job_title)
    if (parsedEntities.seniority) nameParts.push(parsedEntities.seniority)
    if (parsedEntities.location) nameParts.push(parsedEntities.location)
    if (parsedEntities.skills && parsedEntities.skills.length > 0) {
      nameParts.push(parsedEntities.skills.slice(0, 2).join('/'))
    }
    return nameParts.length > 0 ? nameParts.slice(0, 3).join(' - ') : undefined
  }, [parsedEntities])

  const createArchetypeFromJob = useCallback(async (jobId: string) => {
    setIsCreatingArchetype(true)
    try {
      const res = await fetch(`/api/backend-proxy/search/archetypes/from-job/${jobId}/`, {
        method: 'POST'
      })

      if (res.ok) {
        const data = await res.json()
        setArchetypes(prev => [...prev, data])
        setSelectedJobForArchetype(null)
      }
    } catch (error) {
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [setIsCreatingArchetype, setArchetypes, setSelectedJobForArchetype])

  const createArchetypeFromActiveSearch = useCallback(async () => {
    if (!hasParsedEntities()) {
      toast.error("Busca incompleta", { description: "Faça uma busca com critérios definidos antes de salvar como arquétipo." })
      return
    }

    setIsCreatingFromSearch(true)
    try {
      const searchSpec = buildSearchSpec()
      const generatedName = generateArchetypeName()

      const payload = {
        search_spec: searchSpec,
        name: generatedName,
        description: naturalSearchValue || "Arquétipo criado a partir de busca",
        emoji: "🎯"
      }

      const res = await fetch('/api/backend-proxy/search/archetypes/from-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (res.ok) {
        const data = await res.json()
        const newArchetype = data.archetype || data
        setArchetypes(prev => [...prev, newArchetype])
        toast.success("Arquétipo salvo!", { description: `"${newArchetype.name || generatedName || 'Novo arquétipo'}" foi criado a partir da sua busca.` })
      } else {
        const error = await res.json()
        toast.error("Erro ao salvar arquétipo", { description: error.detail || error.error || "Não foi possível salvar o arquétipo." })
      }
    } catch (error) {
      toast.error("Erro ao salvar arquétipo", { description: "Ocorreu um erro de conexão. Tente novamente." })
    } finally {
      setIsCreatingFromSearch(false)
    }
  }, [hasParsedEntities, buildSearchSpec, generateArchetypeName, naturalSearchValue, setIsCreatingFromSearch, setArchetypes])

  const createArchetypeFromDescription = useCallback(async (description: string) => {
    if (!description.trim()) return

    setIsCreatingArchetype(true)
    try {
      const generatedName = generateArchetypeName()

      if (hasParsedEntities()) {
        const searchSpec = buildSearchSpec()

        const payload = {
          search_spec: searchSpec,
          name: generatedName,
          description,
          emoji: "🎯"
        }

        const res = await fetch('/api/backend-proxy/search/archetypes/from-search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })

        if (res.ok) {
          const data = await res.json()
          const newArchetype = data.archetype || data
          setArchetypes(prev => [...prev, newArchetype])
          setNewArchetypeDescription("")
          toast.success("Arquétipo criado", { description: `"${newArchetype.name || generatedName || 'Novo arquétipo'}" foi criado com sucesso.` })
        } else {
          const error = await res.json()
          toast.error("Erro ao criar arquétipo", { description: error.detail || error.error || "Não foi possível criar o arquétipo." })
        }
      } else {
        const payload: Record<string, unknown> = {
          description,
          name: generatedName,
          emoji: "🎯"
        }

        const res = await fetch('/api/backend-proxy/search/archetypes/from-description/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })

        if (res.ok) {
          const data = await res.json()
          const newArchetype = data.archetype || data
          setArchetypes(prev => [...prev, newArchetype])
          setNewArchetypeDescription("")
          toast.success("Arquétipo criado", { description: `"${newArchetype.name || generatedName || 'Novo arquétipo'}" foi criado com sucesso.` })
        } else {
          const error = await res.json()
          toast.error("Erro ao criar arquétipo", { description: error.detail || error.error || "Não foi possível criar o arquétipo." })
        }
      }
    } catch (error) {
      toast.error("Erro ao criar arquétipo", { description: "Ocorreu um erro de conexão. Tente novamente." })
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [generateArchetypeName, hasParsedEntities, buildSearchSpec, setIsCreatingArchetype, setArchetypes, setNewArchetypeDescription])

  const openEditArchetype = useCallback((arch: ArchetypeData, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingArchetype(arch)
    setEditArchetypeName(arch.name || "")
    const archRecord = arch as unknown as Record<string, unknown>
    const query = (archRecord.query as string) || (arch.criteria?.query as string) || ""
    setEditArchetypeQuery(query)
    setEditArchetypeDescription(arch.description || "")
    const emoji = (archRecord.emoji as string) || (arch.criteria?.emoji as string) || "🎯"
    setEditArchetypeEmoji(emoji)
    const tags: string[] = []
    const criteria = arch.criteria || {}
    if (criteria.job_title) tags.push(criteria.job_title as string)
    if (criteria.location) tags.push(criteria.location as string)
    if (criteria.seniority) tags.push(criteria.seniority as string)
    if (criteria.industry) tags.push(criteria.industry as string)
    if (criteria.skills && Array.isArray(criteria.skills)) {
      tags.push(...(criteria.skills as string[]))
    }
    setEditArchetypeTags(tags)
    setNewTagInput("")
  }, [setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setNewTagInput])

  const closeEditArchetype = useCallback(() => {
    setEditingArchetype(null)
    setEditArchetypeName("")
    setEditArchetypeQuery("")
    setEditArchetypeDescription("")
    setEditArchetypeEmoji("")
    setEditArchetypeTags([])
    setNewTagInput("")
  }, [setEditingArchetype, setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription, setEditArchetypeEmoji, setEditArchetypeTags, setNewTagInput])

  const saveArchetype = useCallback(async () => {
    if (!editingArchetype || !editArchetypeName.trim() || !editArchetypeQuery.trim()) return

    setIsSavingArchetype(true)
    try {
      const res = await fetch(`/api/backend-proxy/search/archetypes/${editingArchetype.id}/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editArchetypeName.trim(),
          query: editArchetypeQuery.trim(),
          description: editArchetypeDescription.trim() || null,
          emoji: editArchetypeEmoji || "🎯",
          tags: editArchetypeTags.length > 0 ? editArchetypeTags : null
        })
      })

      if (res.ok) {
        const updated = await res.json()
        setArchetypes(prev => prev.map(a => a.id === editingArchetype.id ? { ...a, ...updated } : a))
        closeEditArchetype()
        toast.success("Arquétipo atualizado", { description: `"${editArchetypeName}" foi salvo com sucesso.` })
      } else {
        const error = await res.json()
        toast.error("Erro ao atualizar arquétipo", { description: error.detail || error.error || "Não foi possível salvar as alterações." })
      }
    } catch (error) {
      toast.error("Erro ao atualizar arquétipo", { description: "Ocorreu um erro de conexão. Tente novamente." })
    } finally {
      setIsSavingArchetype(false)
    }
  }, [editingArchetype, editArchetypeName, editArchetypeQuery, editArchetypeDescription, editArchetypeEmoji, editArchetypeTags, closeEditArchetype, setIsSavingArchetype, setArchetypes])

  const openDeleteArchetypeDialog = useCallback((arch: ArchetypeData, e: React.MouseEvent) => {
    e.stopPropagation()
    setArchetypeToDelete({ id: arch.id, name: arch.name })
    setShowDeleteArchetypeDialog(true)
  }, [setArchetypeToDelete, setShowDeleteArchetypeDialog])

  const confirmDeleteArchetype = useCallback(async () => {
    if (!archetypeToDelete) return

    const archId = archetypeToDelete.id
    const archName = archetypeToDelete.name
    setIsDeletingArchetype(archId)
    setShowDeleteArchetypeDialog(false)

    try {
      const res = await fetch(`/api/backend-proxy/search/archetypes/${archId}/`, {
        method: 'DELETE'
      })

      if (res.ok) {
        setArchetypes(prev => prev.filter(a => a.id !== archId))
        toast.success("Arquétipo excluído", { description: `"${archName}" foi removido com sucesso.` })
      } else {
        const error = await res.json()
        toast.error("Erro ao excluir arquétipo", { description: error.detail || error.error || "Não foi possível excluir o arquétipo." })
      }
    } catch (error) {
      toast.error("Erro ao excluir arquétipo", { description: "Ocorreu um erro de conexão. Tente novamente." })
    } finally {
      setIsDeletingArchetype(null)
      setArchetypeToDelete(null)
    }
  }, [archetypeToDelete, setIsDeletingArchetype, setShowDeleteArchetypeDialog, setArchetypes, setArchetypeToDelete])

  return {
    hasParsedEntities,
    buildSearchSpec,
    generateArchetypeName,
    createArchetypeFromJob,
    createArchetypeFromActiveSearch,
    createArchetypeFromDescription,
    openEditArchetype,
    closeEditArchetype,
    saveArchetype,
    openDeleteArchetypeDialog,
    confirmDeleteArchetype,
  }
}
