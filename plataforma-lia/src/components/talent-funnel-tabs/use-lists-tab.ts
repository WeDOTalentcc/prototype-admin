"use client"

import { useState, useEffect, useMemo, useCallback } from "react"
import { liaApi, CandidateList } from "@/services/lia-api"
import { toast } from "sonner"
import { navigateToNewJobFromCandidates } from "@/lib/navigation/job-navigation"
import { SharedSearch } from "./lists-tab-types"

export const LIST_COLORS = [
  { value: 'var(--lia-text-secondary)', name: 'Cyan' },
  { value: 'var(--lia-text-tertiary)', name: 'Cinza' },
  { value: 'var(--status-success)', name: 'Verde' },
  { value: 'var(--status-warning)', name: 'Amarelo' },
  { value: 'var(--status-error)', name: 'Vermelho' },
  { value: 'var(--wedo-purple)', name: 'Roxo' },
  { value: 'var(--wedo-magenta)', name: 'Rosa' },
  { value: 'var(--wedo-blue)', name: 'Azul' },
]

export function useListsTab() {
  const [lists, setLists] = useState<CandidateList[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingList, setEditingList] = useState<CandidateList | null>(null)
  const [listToDelete, setListToDelete] = useState<CandidateList | null>(null)

  const [formName, setFormName] = useState('')
  const [formDescription, setFormDescription] = useState('')
  const [formColor, setFormColor] = useState(LIST_COLORS[0].value)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const [sharedSearches, setSharedSearches] = useState<SharedSearch[]>([])
  const [loadingShared, setLoadingShared] = useState(true)

  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [selectedSharedSearch, setSelectedSharedSearch] = useState<string | null>(null)
  const [showAddToJobModal, setShowAddToJobModal] = useState(false)
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([])
  const [selectedCandidateNames, setSelectedCandidateNames] = useState<string[]>([])
  const [feedbackComments, setFeedbackComments] = useState<Map<string, string>>(new Map())

  const [showShareModal, setShowShareModal] = useState(false)
  const [shareListData, setShareListData] = useState<{ id: string; name: string; candidateCount: number } | null>(null)

  const loadLists = useCallback(async (retries = 2) => {
    try {
      setLoading(true)
      const response = await liaApi.getCandidateLists({ limit: 100 })
      setLists(response.items || [])
    } catch (error) {
      if (retries > 0) {
        await new Promise(r => setTimeout(r, 2000))
        return loadLists(retries - 1)
      }
      toast.error("Erro ao carregar listas", { description: "Não foi possível carregar as listas de candidatos." })
    } finally {
      setLoading(false)
    }
  }, [])

  const loadSharedSearches = useCallback(async () => {
    try {
      setLoadingShared(true)
      const response = await fetch('/api/backend-proxy/shared-searches')
      if (response.ok) {
        const data = await response.json()
        setSharedSearches(data.items || data || [])
      }
    } catch (error) {
    } finally {
      setLoadingShared(false)
    }
  }, [])

  useEffect(() => {
    loadLists()
    loadSharedSearches()
  }, [loadLists, loadSharedSearches])

  const filteredLists = useMemo(() => {
    if (!searchTerm) return lists
    const term = searchTerm.toLowerCase()
    return lists.filter(list =>
      list.name.toLowerCase().includes(term) ||
      (list.description?.toLowerCase().includes(term))
    )
  }, [lists, searchTerm])

  const openCreateModal = useCallback(() => {
    setEditingList(null)
    setFormName('')
    setFormDescription('')
    setFormColor(LIST_COLORS[0].value)
    setShowCreateModal(true)
  }, [])

  const openEditModal = useCallback((list: CandidateList) => {
    setEditingList(list)
    setFormName(list.name)
    setFormDescription(list.description || '')
    setFormColor(list.color || LIST_COLORS[0].value)
    setShowCreateModal(true)
  }, [])

  const closeModal = useCallback(() => {
    setShowCreateModal(false)
    setEditingList(null)
    setFormName('')
    setFormDescription('')
    setFormColor(LIST_COLORS[0].value)
  }, [])

  const handleSave = useCallback(async () => {
    if (!formName.trim()) {
      toast.error("Nome obrigatório", { description: "Por favor, informe um nome para a lista." })
      return
    }

    setSaving(true)
    try {
      if (editingList) {
        await liaApi.updateCandidateList(editingList.id, {
          name: formName.trim(),
          description: formDescription.trim() || undefined,
          color: formColor,
        })
        toast.success("Lista atualizada", { description: `A lista "${formName}" foi atualizada com sucesso.` })
      } else {
        await liaApi.createCandidateList({
          name: formName.trim(),
          description: formDescription.trim() || undefined,
          color: formColor,
        })
        toast.success("Lista criada", { description: `A lista "${formName}" foi criada com sucesso.` })
      }
      closeModal()
      loadLists()
    } catch (error) {
      toast.error("Erro ao salvar", { description: "Não foi possível salvar a lista. Tente novamente." })
    } finally {
      setSaving(false)
    }
  }, [formName, formDescription, formColor, editingList, closeModal, loadLists])

  const handleDelete = useCallback(async () => {
    if (!listToDelete) return

    setDeleting(true)
    try {
      await liaApi.deleteCandidateList(listToDelete.id)
      toast.success("Lista excluída", { description: `A lista "${listToDelete.name}" foi excluída.` })
      setListToDelete(null)
      loadLists()
    } catch (error) {
      toast.error("Erro ao excluir", { description: "Não foi possível excluir a lista. Tente novamente." })
    } finally {
      setDeleting(false)
    }
  }, [listToDelete, loadLists])

  const totalCandidates = lists.reduce((acc, list) => acc + (list.candidate_count || 0), 0)
  const totalNewFeedbacks = sharedSearches.reduce((acc, s) => acc + (s.feedback_counts?.new_count || 0), 0)

  const handleCopyLink = useCallback(async (shareUrl: string) => {
    try {
      await navigator.clipboard.writeText(shareUrl)
      toast.success("Link copiado", { description: "O link foi copiado para a área de transferência." })
    } catch (error) {
      toast.error("Erro ao copiar", { description: "Não foi possível copiar o link." })
    }
  }, [])

  const handleResendInvite = useCallback(async (id: string) => {
    try {
      const response = await fetch(`/api/backend-proxy/shared-searches/${id}/resend`, {
        method: 'POST',
      })
      if (response.ok) {
        toast.success("Convite reenviado", { description: "O convite foi reenviado com sucesso." })
      } else {
        throw new Error('Failed to resend')
      }
    } catch (error) {
      toast.error("Erro ao reenviar", { description: "Não foi possível reenviar o convite." })
    }
  }, [])

  const handleRevokeShare = useCallback(async (id: string) => {
    try {
      const response = await fetch(`/api/backend-proxy/shared-searches/${id}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        toast.success("Compartilhamento encerrado", { description: "O acesso foi revogado com sucesso." })
        loadSharedSearches()
      } else {
        throw new Error('Failed to revoke')
      }
    } catch (error) {
      toast.error("Erro ao encerrar", { description: "Não foi possível encerrar o compartilhamento." })
    }
  }, [loadSharedSearches])

  const handleViewDetails = useCallback((id: string) => {
    setSelectedSharedSearch(id)
    setShowDetailsModal(true)
  }, [])

  const handleCreateListFromShared = useCallback(async (candidateIds: string[]) => {
    try {
      const response = await liaApi.createCandidateList({
        name: `Nova lista (${candidateIds.length} candidatos)`,
        description: 'Criada a partir de compartilhamento',
      })
      if (response?.id) {
        await liaApi.addCandidatesToList(response.id, candidateIds)
        toast.success("Lista criada", { description: `Lista criada com ${candidateIds.length} candidato(s).` })
        loadLists()
        setShowDetailsModal(false)
      }
    } catch (error) {
      toast.error("Erro ao criar lista", { description: "Não foi possível criar a lista. Tente novamente." })
    }
  }, [loadLists])

  const handleAddToJobFromShared = useCallback((candidateIds: string[]) => {
    setSelectedCandidateIds(candidateIds)
    setShowAddToJobModal(true)
  }, [])

  const handleCreateJobFromShared = useCallback((candidateIds: string[]) => {
    setSelectedCandidateIds(candidateIds)
    // Routed through canonical helper (post-mortem 2026-04-29): the
    // /jobs/new route was deleted; helper surfaces a guidance toast so
    // user knows how to proceed (chat with LIA + selected candidates).
    navigateToNewJobFromCandidates(candidateIds)
  }, [])

  const handleShareList = useCallback((list: CandidateList) => {
    setShareListData({
      id: list.id,
      name: list.name,
      candidateCount: list.candidate_count || 0,
    })
    setShowShareModal(true)
  }, [])

  return {
    lists,
    loading,
    searchTerm,
    setSearchTerm,
    showCreateModal,
    setShowCreateModal,
    editingList,
    listToDelete,
    setListToDelete,
    formName,
    setFormName,
    formDescription,
    setFormDescription,
    formColor,
    setFormColor,
    saving,
    deleting,
    sharedSearches,
    loadingShared,
    showDetailsModal,
    setShowDetailsModal,
    selectedSharedSearch,
    showAddToJobModal,
    setShowAddToJobModal,
    selectedCandidateIds,
    selectedCandidateNames,
    feedbackComments,
    showShareModal,
    setShowShareModal,
    shareListData,
    setShareListData,
    filteredLists,
    totalCandidates,
    totalNewFeedbacks,
    openCreateModal,
    openEditModal,
    closeModal,
    handleSave,
    handleDelete,
    handleCopyLink,
    handleResendInvite,
    handleRevokeShare,
    handleViewDetails,
    handleCreateListFromShared,
    handleAddToJobFromShared,
    handleCreateJobFromShared,
    handleShareList,
    loadSharedSearches,
  }
}
