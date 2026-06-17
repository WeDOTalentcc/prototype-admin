"use client"

import { useState, useCallback, useEffect } from "react"
import { toast } from "sonner"
import type { ArchetypeData, BackendEntities } from "@/hooks/ui/usePromptState"
import { extractTagsFromArchetypeCriteria } from "@/hooks/ui/promptStateCriteriaUtils"

export interface UsePromptArchetypeStateParams {
  naturalSearchValue: string
  parsedEntities: BackendEntities
  hasParsedEntities: () => boolean
  buildSearchSpec: () => Record<string, unknown>
  generateArchetypeName: () => string
}

export interface UsePromptArchetypeStateReturn {
  archetypes: ArchetypeData[]
  setArchetypes: React.Dispatch<React.SetStateAction<ArchetypeData[]>>
  closedJobsForArchetype: Record<string, unknown>[]
  archetypeSearchFilter: string
  setArchetypeSearchFilter: (v: string) => void
  isCreatingArchetype: boolean
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
  isCreatingFromSearch: boolean
  filteredArchetypes: ArchetypeData[]
  createArchetypeFromJob: (jobId: string) => Promise<void>
  createArchetypeFromActiveSearch: () => Promise<void>
  createArchetypeFromDescription: (description: string) => Promise<void>
  openEditArchetype: (arch: ArchetypeData, e: React.MouseEvent) => void
  closeEditArchetype: () => void
  saveArchetype: () => Promise<void>
  openDeleteArchetypeDialog: (arch: ArchetypeData, e: React.MouseEvent) => void
  confirmDeleteArchetype: () => Promise<void>
  handleArchetypeSaved: (newArchetype: ArchetypeData) => void
}

export function usePromptArchetypeState({
  naturalSearchValue,
  parsedEntities,
  hasParsedEntities,
  buildSearchSpec,
  generateArchetypeName,
}: UsePromptArchetypeStateParams): UsePromptArchetypeStateReturn {
  const [archetypes, setArchetypes] = useState<ArchetypeData[]>([])
  const [closedJobsForArchetype, setClosedJobsForArchetype] = useState<Record<string, unknown>[]>([])
  const [archetypeSearchFilter, setArchetypeSearchFilter] = useState("")
  const [isCreatingArchetype, setIsCreatingArchetype] = useState(false)
  const [newArchetypeDescription, setNewArchetypeDescription] = useState("")
  const [selectedJobForArchetype, setSelectedJobForArchetype] = useState<string | null>(null)

  const [editingArchetype, setEditingArchetype] = useState<ArchetypeData | null>(null)
  const [editArchetypeName, setEditArchetypeName] = useState("")
  const [editArchetypeQuery, setEditArchetypeQuery] = useState("")
  const [editArchetypeDescription, setEditArchetypeDescription] = useState("")
  const [editArchetypeEmoji, setEditArchetypeEmoji] = useState("")
  const [editArchetypeTags, setEditArchetypeTags] = useState<string[]>([])
  const [newTagInput, setNewTagInput] = useState("")
  const [isSavingArchetype, setIsSavingArchetype] = useState(false)
  const [isDeletingArchetype, setIsDeletingArchetype] = useState<string | null>(null)
  const [showDeleteArchetypeDialog, setShowDeleteArchetypeDialog] = useState(false)
  const [archetypeToDelete, setArchetypeToDelete] = useState<{ id: string; name: string } | null>(null)
  const [showSaveArchetypeModal, setShowSaveArchetypeModal] = useState(false)
  const [isCreatingFromSearch, setIsCreatingFromSearch] = useState(false)

  useEffect(() => {
    const loadArchetypesAndJobs = async () => {
      try {
        const [archetypesRes, jobsRes] = await Promise.all([
          fetch('/api/backend-proxy/search/archetypes/'),
          fetch('/api/backend-proxy/search/archetypes/suggestions/closed-jobs/?limit=5')
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
        console.error("[usePromptArchetypeState] Error:", error)
      }
    }
    loadArchetypesAndJobs()
  }, [])

  const filteredArchetypes = archetypes.filter(a => {
    if (!archetypeSearchFilter.trim()) return true
    const filter = archetypeSearchFilter.toLowerCase()
    return (a.name || '').toLowerCase().includes(filter) ||
      (a.department || '').toLowerCase().includes(filter) ||
      (a.hired_candidate?.name || '').toLowerCase().includes(filter)
  })

  const createArchetypeFromJob = useCallback(async (jobId: string) => {
    setIsCreatingArchetype(true)
    try {
      const res = await fetch(`/api/backend-proxy/search/archetypes/from-job/${jobId}/`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setArchetypes(prev => [...prev, data])
        setSelectedJobForArchetype(null)
      }
    } catch {
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
      const payload = { search_spec: searchSpec, name: generatedName, description: naturalSearchValue || "Arquétipo criado a partir de busca", emoji: "🎯" }
      const res = await fetch('/api/backend-proxy/search/archetypes/from-search', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
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
      const url = hasParsedEntities()
        ? '/api/backend-proxy/search/archetypes/from-search'
        : '/api/backend-proxy/search/archetypes/from-description/'
      const payload = hasParsedEntities()
        ? { search_spec: buildSearchSpec(), name: generatedName, description, emoji: "🎯" }
        : { description, name: generatedName, emoji: "🎯" }
      const res = await fetch(url, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
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
    } catch {
      toast.error("Erro ao criar arquétipo", { description: "Ocorreu um erro de conexão. Tente novamente." })
    } finally {
      setIsCreatingArchetype(false)
    }
  }, [generateArchetypeName, hasParsedEntities, buildSearchSpec])

  const openEditArchetype = useCallback((arch: ArchetypeData, e: React.MouseEvent) => {
    e.stopPropagation()
    const archExt = arch as ArchetypeData & { query?: string; emoji?: string }
    setEditingArchetype(arch)
    setEditArchetypeName(arch.name || "")
    setEditArchetypeQuery(String(archExt.query || arch.criteria?.query || ""))
    setEditArchetypeDescription(arch.description || "")
    setEditArchetypeEmoji(String(archExt.emoji || arch.criteria?.emoji || "🎯"))
    setEditArchetypeTags(extractTagsFromArchetypeCriteria(arch.criteria || {}))
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
          name: editArchetypeName.trim(), query: editArchetypeQuery.trim(),
          description: editArchetypeDescription.trim() || null, emoji: editArchetypeEmoji || "🎯",
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
    const archId = archetypeToDelete.id
    const archName = archetypeToDelete.name
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

  const handleArchetypeSaved = useCallback((newArchetype: ArchetypeData) => {
    setArchetypes(prev => [...prev, newArchetype])
    toast.success("Arquétipo salvo", { description: `"${newArchetype.name}" foi adicionado aos seus arquétipos.` })
  }, [])

  return {
    archetypes, setArchetypes,
    closedJobsForArchetype,
    archetypeSearchFilter, setArchetypeSearchFilter,
    isCreatingArchetype,
    newArchetypeDescription, setNewArchetypeDescription,
    selectedJobForArchetype, setSelectedJobForArchetype,
    editingArchetype,
    editArchetypeName, setEditArchetypeName,
    editArchetypeQuery, setEditArchetypeQuery,
    editArchetypeDescription, setEditArchetypeDescription,
    editArchetypeEmoji, setEditArchetypeEmoji,
    editArchetypeTags, setEditArchetypeTags,
    newTagInput, setNewTagInput,
    isSavingArchetype,
    isDeletingArchetype,
    showDeleteArchetypeDialog, setShowDeleteArchetypeDialog,
    archetypeToDelete,
    showSaveArchetypeModal, setShowSaveArchetypeModal,
    isCreatingFromSearch,
    filteredArchetypes,
    createArchetypeFromJob,
    createArchetypeFromActiveSearch,
    createArchetypeFromDescription,
    openEditArchetype,
    closeEditArchetype,
    saveArchetype,
    openDeleteArchetypeDialog,
    confirmDeleteArchetype,
    handleArchetypeSaved,
  }
}
