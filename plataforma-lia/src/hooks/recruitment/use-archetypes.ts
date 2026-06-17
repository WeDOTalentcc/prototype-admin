"use client"

/**
 * useArchetypes — CRUD de arquétipos de busca (criar, editar, deletar, listar).
 *
 * Extraído de ExpandableAIPrompt (P1-E).
 * Gerencia: archetypes, closedJobsForArchetype, edit/delete dialogs, e todos os handlers de API.
 *
 * Recebe como parâmetros estado externo de que depende:
 *   - parsedEntities — para gerar nomes e specs de arquétipo
 *   - advancedFilters — incluído no search_spec
 *   - naturalSearchValue — descrição padrão ao criar de busca ativa
 *   - toast — feedback visual
 *
 * Portabilidade Vue: mapeia para composable useArchetypes().
 */

import { useState, useCallback, useEffect } from "react"
import type { ArchetypeData, BackendEntities } from "@/components/search/expandable-ai-prompt.types"
import type { SearchFilters } from "@/components/search/expandable-ai-prompt.types"
import { toast } from "sonner"

export interface UseArchetypesResult {
  archetypes: ArchetypeData[]
  closedJobsForArchetype: unknown[]
  archetypeSearchFilter: string
  setArchetypeSearchFilter: (v: string) => void
  isCreatingArchetype: boolean
  isCreatingFromSearch: boolean
  newArchetypeDescription: string
  setNewArchetypeDescription: (v: string) => void
  selectedJobForArchetype: string | null
  setSelectedJobForArchetype: (v: string | null) => void
  editingArchetype: ArchetypeData | null
  editArchetypeName: string
  setEditArchetypeName: (v: string) => void
  editArchetypeQuery: string
  setEditArchetypeQuery: (v: string) => void
  editArchetypeDescription: string
  setEditArchetypeDescription: (v: string) => void
  editArchetypeEmoji: string
  setEditArchetypeEmoji: (v: string) => void
  editArchetypeTags: string[]
  setEditArchetypeTags: React.Dispatch<React.SetStateAction<string[]>>
  newTagInput: string
  setNewTagInput: (v: string) => void
  isSavingArchetype: boolean
  isDeletingArchetype: string | null
  showDeleteArchetypeDialog: boolean
  setShowDeleteArchetypeDialog: (v: boolean) => void
  archetypeToDelete: { id: string; name: string } | null
  showSaveArchetypeModal: boolean
  setShowSaveArchetypeModal: (v: boolean) => void
  filteredArchetypes: ArchetypeData[]
  hasParsedEntities: () => boolean
  createArchetypeFromJob: (jobId: string) => Promise<void>
  createArchetypeFromActiveSearch: () => Promise<void>
  createArchetypeFromDescription: (description: string) => Promise<void>
  openEditArchetype: (arch: ArchetypeData, e: React.MouseEvent) => void
  closeEditArchetype: () => void
  saveArchetype: () => Promise<void>
  openDeleteArchetypeDialog: (arch: ArchetypeData, e: React.MouseEvent) => void
  confirmDeleteArchetype: () => Promise<void>
}

interface UseArchetypesOptions {
  parsedEntities: BackendEntities
  advancedFilters: SearchFilters
  naturalSearchValue: string
}

export function useArchetypes({
  parsedEntities,
  advancedFilters,
  naturalSearchValue,
}: UseArchetypesOptions): UseArchetypesResult {
  const [archetypes, setArchetypes] = useState<ArchetypeData[]>([])
  const [closedJobsForArchetype, setClosedJobsForArchetype] = useState<unknown[]>([])
  const [archetypeSearchFilter, setArchetypeSearchFilter] = useState("")
  const [isCreatingArchetype, setIsCreatingArchetype] = useState(false)
  const [isCreatingFromSearch, setIsCreatingFromSearch] = useState(false)
  const [newArchetypeDescription, setNewArchetypeDescription] = useState("")
  const [selectedJobForArchetype, setSelectedJobForArchetype] = useState<string | null>(null)

  // Edit state
  const [editingArchetype, setEditingArchetype] = useState<ArchetypeData | null>(null)
  const [editArchetypeName, setEditArchetypeName] = useState("")
  const [editArchetypeQuery, setEditArchetypeQuery] = useState("")
  const [editArchetypeDescription, setEditArchetypeDescription] = useState("")
  const [editArchetypeEmoji, setEditArchetypeEmoji] = useState("")
  const [editArchetypeTags, setEditArchetypeTags] = useState<string[]>([])
  const [newTagInput, setNewTagInput] = useState("")

  // Delete dialog
  const [isSavingArchetype, setIsSavingArchetype] = useState(false)
  const [isDeletingArchetype, setIsDeletingArchetype] = useState<string | null>(null)
  const [showDeleteArchetypeDialog, setShowDeleteArchetypeDialog] = useState(false)
  const [archetypeToDelete, setArchetypeToDelete] = useState<{ id: string; name: string } | null>(null)

  // Save from search modal
  const [showSaveArchetypeModal, setShowSaveArchetypeModal] = useState(false)

  // ── Load on mount ──────────────────────────────────────────────────────

  useEffect(() => {
    const loadArchetypesAndJobs = async () => {
      try {
        const [archetypesRes, jobsRes] = await Promise.all([
          fetch('/api/backend-proxy/search/archetypes/'),
          fetch('/api/backend-proxy/search/archetypes/suggestions/closed-jobs/?limit=5'),
        ])
        if (archetypesRes.ok) {
          const data = await archetypesRes.json()
          setArchetypes(data.archetypes || data || [])
        }
        if (jobsRes.ok) {
          const data = await jobsRes.json()
          setClosedJobsForArchetype(data.jobs || data || [])
        }
      } catch (error) {
        console.error("[use-archetypes] Error:", error)
      }
    }
    loadArchetypesAndJobs()
  }, [])

  // ── Derived ────────────────────────────────────────────────────────────

  const filteredArchetypes = archetypeSearchFilter.trim()
    ? archetypes.filter(a =>
        (a.name || '').toLowerCase().includes(archetypeSearchFilter.toLowerCase()) ||
        (a.description || '').toLowerCase().includes(archetypeSearchFilter.toLowerCase())
      )
    : archetypes

  // ── Helpers (depend on parsedEntities / advancedFilters) ───────────────

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
    if (parsedEntities.skills && parsedEntities.skills.length > 0) spec.skills = parsedEntities.skills
    if ((advancedFilters as Record<string, unknown>).locations && ((advancedFilters as Record<string, unknown>).locations as string[]).length > 0) {
      spec.locations = (advancedFilters as Record<string, unknown>).locations as string[]
    }
    if (advancedFilters.job?.titles && advancedFilters.job.titles.length > 0) {
      spec.job_titles = advancedFilters.job.titles
    }
    if (advancedFilters.job?.levels && advancedFilters.job.levels.length > 0) {
      spec.seniority_levels = advancedFilters.job.levels
    }
    if (advancedFilters.skills?.skillItems && advancedFilters.skills.skillItems.length > 0) {
      spec.required_skills = (advancedFilters.skills.skillItems as Array<{ name: string }>).map(s => s.name)
    }
    if (advancedFilters.languages?.languages && advancedFilters.languages.languages.length > 0) {
      spec.languages = advancedFilters.languages.languages
    }
    if (advancedFilters.general?.minExperience) spec.years_experience_min = advancedFilters.general.minExperience
    if (advancedFilters.general?.maxExperience) spec.years_experience_max = advancedFilters.general.maxExperience

    return spec
  }, [parsedEntities, advancedFilters])

  const generateArchetypeName = useCallback(() => {
    const parts: string[] = []
    if (parsedEntities.job_title) parts.push(parsedEntities.job_title)
    if (parsedEntities.seniority) parts.push(parsedEntities.seniority)
    if (parsedEntities.location) parts.push(parsedEntities.location)
    if (parsedEntities.skills && parsedEntities.skills.length > 0) {
      parts.push(parsedEntities.skills.slice(0, 2).join('/'))
    }
    return parts.length > 0 ? parts.slice(0, 3).join(' - ') : undefined
  }, [parsedEntities])

  // ── CRUD ───────────────────────────────────────────────────────────────

  const createArchetypeFromJob = useCallback(async (jobId: string) => {
    setIsCreatingArchetype(true)
    try {
      const res = await fetch(`/api/backend-proxy/search/archetypes/from-job/${jobId}/`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setArchetypes(prev => [...prev, data])
        setSelectedJobForArchetype(null)
      }
    } catch (error) {
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [])

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
        emoji: "🎯",
      }
      const res = await fetch('/api/backend-proxy/search/archetypes/from-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (res.ok) {
        const data = await res.json()
        const newArchetype = data.archetype || data
        setArchetypes(prev => [...prev, newArchetype])
        toast.success("Arquétipo salvo!", { description: `"${newArchetype.name || generatedName || 'Novo arquétipo'}" foi criado a partir da sua busca.` })
      } else {
        const error = await res.json()
        const _rid = error.request_id ? ` (ID: ${error.request_id})` : ""
        toast.error("Erro ao salvar arquétipo", { description: `${error.detail || error.error || "Não foi possível salvar o arquétipo."}${_rid}` })
      }
    } catch {
      toast.error("Erro ao salvar arquétipo", { description: "Ocorreu um erro de conexão. Tente novamente." })
    } finally {
      setIsCreatingFromSearch(false)
    }
  }, [hasParsedEntities, buildSearchSpec, generateArchetypeName, naturalSearchValue])

  const createArchetypeFromDescription = useCallback(async (description: string) => {
    if (!description.trim()) return
    setIsCreatingArchetype(true)
    try {
      const generatedName = generateArchetypeName()
      if (hasParsedEntities()) {
        const searchSpec = buildSearchSpec()
        const payload = { search_spec: searchSpec, name: generatedName, description, emoji: "🎯" }
        const res = await fetch('/api/backend-proxy/search/archetypes/from-search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (res.ok) {
          const data = await res.json()
          const newArchetype = data.archetype || data
          setArchetypes(prev => [...prev, newArchetype])
          setNewArchetypeDescription("")
          toast.success("Arquétipo criado", { description: `"${newArchetype.name || generatedName || 'Novo arquétipo'}" foi criado com sucesso.` })
        } else {
          const error = await res.json()
          const _rid = error.request_id ? ` (ID: ${error.request_id})` : ""
          toast.error("Erro ao criar arquétipo", { description: `${error.detail || error.error || "Não foi possível criar o arquétipo."}${_rid}` })
        }
      } else {
        const payload = { description, name: generatedName, emoji: "🎯" }
        const res = await fetch('/api/backend-proxy/search/archetypes/from-description/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (res.ok) {
          const data = await res.json()
          const newArchetype = data.archetype || data
          setArchetypes(prev => [...prev, newArchetype])
          setNewArchetypeDescription("")
          toast.success("Arquétipo criado", { description: `"${newArchetype.name || generatedName || 'Novo arquétipo'}" foi criado com sucesso.` })
        } else {
          const error = await res.json()
          const _rid = error.request_id ? ` (ID: ${error.request_id})` : ""
          toast.error("Erro ao criar arquétipo", { description: `${error.detail || error.error || "Não foi possível criar o arquétipo."}${_rid}` })
        }
      }
    } catch {
      toast.error("Erro ao criar arquétipo", { description: "Ocorreu um erro de conexão. Tente novamente." })
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [generateArchetypeName, hasParsedEntities, buildSearchSpec])

  const openEditArchetype = useCallback((arch: ArchetypeData, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingArchetype(arch)
    setEditArchetypeName(arch.name || "")
    const query = (arch as ArchetypeData & { query?: string }).query || (arch.criteria as Record<string, unknown> | undefined)?.query as string || ""
    setEditArchetypeQuery(query)
    setEditArchetypeDescription(arch.description || "")
    const emoji = (arch as ArchetypeData & { emoji?: string }).emoji || (arch.criteria as Record<string, unknown> | undefined)?.emoji as string || "🎯"
    setEditArchetypeEmoji(emoji)
    const tags: string[] = []
    const criteria = (arch.criteria || {}) as Record<string, unknown>
    if (criteria.job_title) tags.push(criteria.job_title as string)
    if (criteria.location) tags.push(criteria.location as string)
    if (criteria.seniority) tags.push(criteria.seniority as string)
    if (criteria.industry) tags.push(criteria.industry as string)
    if (criteria.skills && Array.isArray(criteria.skills)) tags.push(...(criteria.skills as string[]))
    setEditArchetypeTags(tags)
    setNewTagInput("")
  }, [])

  const closeEditArchetype = useCallback(() => {
    setEditingArchetype(null)
    setEditArchetypeName("")
    setEditArchetypeQuery("")
    setEditArchetypeDescription("")
    setEditArchetypeEmoji("")
    setEditArchetypeTags([])
    setNewTagInput("")
  }, [])

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
          tags: editArchetypeTags.length > 0 ? editArchetypeTags : null,
        }),
      })
      if (res.ok) {
        const updated = await res.json()
        setArchetypes(prev => prev.map(a => a.id === editingArchetype.id ? { ...a, ...updated } : a))
        closeEditArchetype()
        toast.success("Arquétipo atualizado", { description: `"${editArchetypeName}" foi salvo com sucesso.` })
      } else {
        const error = await res.json()
        const _rid = error.request_id ? ` (ID: ${error.request_id})` : ""
        toast.error("Erro ao atualizar arquétipo", { description: `${error.detail || error.error || "Não foi possível salvar as alterações."}${_rid}` })
      }
    } catch {
      toast.error("Erro ao atualizar arquétipo", { description: "Ocorreu um erro de conexão. Tente novamente." })
    } finally {
      setIsSavingArchetype(false)
    }
  }, [editingArchetype, editArchetypeName, editArchetypeQuery, editArchetypeDescription, editArchetypeEmoji, editArchetypeTags, closeEditArchetype])

  const openDeleteArchetypeDialog = useCallback((arch: ArchetypeData, e: React.MouseEvent) => {
    e.stopPropagation()
    setArchetypeToDelete({ id: arch.id, name: arch.name })
    setShowDeleteArchetypeDialog(true)
  }, [])

  const confirmDeleteArchetype = useCallback(async () => {
    if (!archetypeToDelete) return
    const { id: archId, name: archName } = archetypeToDelete
    setIsDeletingArchetype(archId)
    setShowDeleteArchetypeDialog(false)
    try {
      const res = await fetch(`/api/backend-proxy/search/archetypes/${archId}/`, { method: 'DELETE' })
      if (res.ok) {
        setArchetypes(prev => prev.filter(a => a.id !== archId))
        toast.success("Arquétipo excluído", { description: `"${archName}" foi removido com sucesso.` })
      } else {
        const error = await res.json()
        const _rid = error.request_id ? ` (ID: ${error.request_id})` : ""
        toast.error("Erro ao excluir arquétipo", { description: `${error.detail || error.error || "Não foi possível excluir o arquétipo."}${_rid}` })
      }
    } catch {
      toast.error("Erro ao excluir arquétipo", { description: "Ocorreu um erro de conexão. Tente novamente." })
    } finally {
      setIsDeletingArchetype(null)
      setArchetypeToDelete(null)
    }
  }, [archetypeToDelete])

  return {
    archetypes,
    closedJobsForArchetype,
    archetypeSearchFilter,
    setArchetypeSearchFilter,
    isCreatingArchetype,
    isCreatingFromSearch,
    newArchetypeDescription,
    setNewArchetypeDescription,
    selectedJobForArchetype,
    setSelectedJobForArchetype,
    editingArchetype,
    editArchetypeName,
    setEditArchetypeName,
    editArchetypeQuery,
    setEditArchetypeQuery,
    editArchetypeDescription,
    setEditArchetypeDescription,
    editArchetypeEmoji,
    setEditArchetypeEmoji,
    editArchetypeTags,
    setEditArchetypeTags,
    newTagInput,
    setNewTagInput,
    isSavingArchetype,
    isDeletingArchetype,
    showDeleteArchetypeDialog,
    setShowDeleteArchetypeDialog,
    archetypeToDelete,
    showSaveArchetypeModal,
    setShowSaveArchetypeModal,
    filteredArchetypes,
    hasParsedEntities,
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
