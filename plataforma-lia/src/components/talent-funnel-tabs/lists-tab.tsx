"use client"

import { useState, useEffect, useMemo } from "react"
import { liaApi, CandidateList, CandidateListDetail } from "@/services/lia-api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import {
  List, Plus, Search, MoreHorizontal, Edit2, Trash2, Users,
  Calendar, FolderOpen, Briefcase, X, Check, Loader2, ChevronRight, UserPlus,
  Link2, ThumbsUp, ThumbsDown, HelpCircle, Clock, Eye, Copy, Send, XCircle, Share2
} from "lucide-react"
import { SharedSearchDetailsModal } from "@/components/modals/shared-search-details-modal"
import { AddToJobModal } from "@/components/modals/add-to-job-modal"
import { ShareSearchModal } from "@/components/modals/share-search-modal"

export interface SharedSearch {
  id: string
  share_type: 'search' | 'list'
  title: string
  candidate_count: number
  recipient_email: string
  recipient_name?: string | null
  share_url: string
  status: 'active' | 'expired' | 'revoked'
  first_accessed_at?: string | null
  created_at: string
  expires_at?: string | null
  feedback_counts: {
    approved: number
    rejected: number
    maybe: number
    pending: number
    new_count: number
  }
}
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

const LIST_COLORS = [
  { value: 'var(--gray-600)', name: 'Cyan' },
  { value: 'var(--gray-400)', name: 'Cinza' },
  { value: 'var(--status-success)', name: 'Verde' },
  { value: 'var(--status-warning)', name: 'Amarelo' },
  { value: 'var(--status-error)', name: 'Vermelho' },
  { value: 'var(--wedo-purple)', name: 'Roxo' },
  { value: 'var(--wedo-magenta)', name: 'Rosa' },
  { value: 'var(--wedo-blue)', name: 'Azul' },
]

interface ListsTabProps {
  onListSelect: (listId: string) => void
  onAddToJobs: (listId: string) => void
  onGoToSearch?: () => void
  onAddCandidateToList?: (listId: string, listName: string) => void
  onViewSharedDetails?: (id: string) => void
}

export function ListsTab({ onListSelect, onAddToJobs, onGoToSearch, onAddCandidateToList, onViewSharedDetails }: ListsTabProps) {
  const { toast } = useToast()
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
  const [selectedSharedId, setSelectedSharedId] = useState<string | null>(null)

  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [selectedSharedSearch, setSelectedSharedSearch] = useState<string | null>(null)
  const [showAddToJobModal, setShowAddToJobModal] = useState(false)
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([])
  const [selectedCandidateNames, setSelectedCandidateNames] = useState<string[]>([])
  const [feedbackComments, setFeedbackComments] = useState<Map<string, string>>(new Map())

  const [showShareModal, setShowShareModal] = useState(false)
  const [shareListData, setShareListData] = useState<{ id: string; name: string; candidateCount: number } | null>(null)

  const loadLists = async () => {
    try {
      setLoading(true)
      const response = await liaApi.getCandidateLists({ limit: 100 })
      setLists(response.items || [])
    } catch (error) {
      toast({
        title: "Erro ao carregar listas",
        description: "Não foi possível carregar as listas de candidatos.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const loadSharedSearches = async () => {
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
  }

  useEffect(() => {
    loadLists()
    loadSharedSearches()
  }, [])

  const filteredLists = useMemo(() => {
    if (!searchTerm) return lists
    const term = searchTerm.toLowerCase()
    return lists.filter(list =>
      list.name.toLowerCase().includes(term) ||
      (list.description?.toLowerCase().includes(term))
    )
  }, [lists, searchTerm])

  const openCreateModal = () => {
    setEditingList(null)
    setFormName('')
    setFormDescription('')
    setFormColor(LIST_COLORS[0].value)
    setShowCreateModal(true)
  }

  const openEditModal = (list: CandidateList) => {
    setEditingList(list)
    setFormName(list.name)
    setFormDescription(list.description || '')
    setFormColor(list.color || LIST_COLORS[0].value)
    setShowCreateModal(true)
  }

  const closeModal = () => {
    setShowCreateModal(false)
    setEditingList(null)
    setFormName('')
    setFormDescription('')
    setFormColor(LIST_COLORS[0].value)
  }

  const handleSave = async () => {
    if (!formName.trim()) {
      toast({
        title: "Nome obrigatório",
        description: "Por favor, informe um nome para a lista.",
        variant: "destructive",
      })
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
        toast({
          title: "Lista atualizada",
          description: `A lista "${formName}" foi atualizada com sucesso.`,
        })
      } else {
        await liaApi.createCandidateList({
          name: formName.trim(),
          description: formDescription.trim() || undefined,
          color: formColor,
        })
        toast({
          title: "Lista criada",
          description: `A lista "${formName}" foi criada com sucesso.`,
        })
      }
      closeModal()
      loadLists()
    } catch (error) {
      toast({
        title: "Erro ao salvar",
        description: "Não foi possível salvar a lista. Tente novamente.",
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!listToDelete) return

    setDeleting(true)
    try {
      await liaApi.deleteCandidateList(listToDelete.id)
      toast({
        title: "Lista excluída",
        description: `A lista "${listToDelete.name}" foi excluída.`,
      })
      setListToDelete(null)
      loadLists()
    } catch (error) {
      toast({
        title: "Erro ao excluir",
        description: "Não foi possível excluir a lista. Tente novamente.",
        variant: "destructive",
      })
    } finally {
      setDeleting(false)
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Não disponível'
    const date = new Date(dateString)
    return date.toLocaleDateString('pt-BR', { 
      day: '2-digit', 
      month: 'short',
      year: 'numeric'
    })
  }

  const truncateText = (text: string, maxLength: number = 80) => {
    if (!text) return ''
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength).trim() + '...'
  }

  const totalCandidates = lists.reduce((acc, list) => acc + (list.candidate_count || 0), 0)

  const openAddCandidateModal = (list: CandidateList) => {
    if (onAddCandidateToList) {
      onAddCandidateToList(list.id, list.name)
    }
  }

  const totalNewFeedbacks = sharedSearches.reduce((acc, s) => acc + (s.feedback_counts?.new_count || 0), 0)

  const getStatusBadge = (status: 'active' | 'expired' | 'revoked') => {
    switch (status) {
      case 'active':
        return <Badge className="bg-status-success/15 text-status-success border-status-success/30 text-micro">Ativo</Badge>
      case 'expired':
        return <Badge className="bg-status-error/15 text-status-error border-status-error/30 text-micro">Expirado</Badge>
      case 'revoked':
        return <Badge className="bg-gray-100 lia-text-base border-lia-border-subtle text-micro">Revogado</Badge>
    }
  }

  const handleCopyLink = async (shareUrl: string) => {
    try {
      await navigator.clipboard.writeText(shareUrl)
      toast({
        title: "Link copiado",
        description: "O link foi copiado para a área de transferência.",
      })
    } catch (error) {
      toast({
        title: "Erro ao copiar",
        description: "Não foi possível copiar o link.",
        variant: "destructive",
      })
    }
  }

  const handleResendInvite = async (id: string) => {
    try {
      const response = await fetch(`/api/backend-proxy/shared-searches/${id}/resend`, {
        method: 'POST',
      })
      if (response.ok) {
        toast({
          title: "Convite reenviado",
          description: "O convite foi reenviado com sucesso.",
        })
      } else {
        throw new Error('Failed to resend')
      }
    } catch (error) {
      toast({
        title: "Erro ao reenviar",
        description: "Não foi possível reenviar o convite.",
        variant: "destructive",
      })
    }
  }

  const handleRevokeShare = async (id: string) => {
    try {
      const response = await fetch(`/api/backend-proxy/shared-searches/${id}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        toast({
          title: "Compartilhamento encerrado",
          description: "O acesso foi revogado com sucesso.",
        })
        loadSharedSearches()
      } else {
        throw new Error('Failed to revoke')
      }
    } catch (error) {
      toast({
        title: "Erro ao encerrar",
        description: "Não foi possível encerrar o compartilhamento.",
        variant: "destructive",
      })
    }
  }

  const handleViewDetails = (id: string) => {
    setSelectedSharedSearch(id)
    setShowDetailsModal(true)
  }

  const handleCreateListFromShared = async (candidateIds: string[]) => {
    try {
      const response = await liaApi.createCandidateList({
        name: `Nova lista (${candidateIds.length} candidatos)`,
        description: 'Criada a partir de compartilhamento',
      })
      if (response?.id) {
        await liaApi.addCandidatesToList(response.id, candidateIds)
        toast({
          title: "Lista criada",
          description: `Lista criada com ${candidateIds.length} candidato(s).`,
        })
        loadLists()
        setShowDetailsModal(false)
      }
    } catch (error) {
      toast({
        title: "Erro ao criar lista",
        description: "Não foi possível criar a lista. Tente novamente.",
        variant: "destructive",
      })
    }
  }

  const handleAddToJobFromShared = (candidateIds: string[]) => {
    setSelectedCandidateIds(candidateIds)
    setShowAddToJobModal(true)
  }

  const handleCreateJobFromShared = (candidateIds: string[]) => {
    setSelectedCandidateIds(candidateIds)
    toast({
      title: "Criar nova vaga",
      description: `Redirecionando para criar vaga com ${candidateIds.length} candidato(s)...`,
    })
    window.location.href = `/jobs/new?candidates=${candidateIds.join(',')}`
  }

  const handleShareList = (list: CandidateList) => {
    setShareListData({
      id: list.id,
      name: list.name,
      candidateCount: list.candidate_count || 0,
    })
    setShowShareModal(true)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-lg font-semibold text-lia-text-primary font-['Open_Sans',sans-serif] flex items-center gap-2">
            <List className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            Listas de Candidatos
          </h2>
          <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mt-0.5">
            {lists.length} {lists.length === 1 ? 'lista' : 'listas'} • {totalCandidates} {totalCandidates === 1 ? 'candidato' : 'candidatos'} no total
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
            <Input
              placeholder="Buscar listas..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 w-64 h-8 text-xs"
            />
          </div>

          <Button
            onClick={openCreateModal}
            size="sm"
            className="h-8 text-xs gap-1.5 bg-gray-900 hover:bg-gray-800 text-white"
          >
            <Plus className="w-3.5 h-3.5" />
            Nova Lista
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-lia-text-secondary dark:text-lia-text-tertiary" />
          <span className="ml-2 text-sm text-lia-text-primary dark:text-lia-text-primary">Carregando listas...</span>
        </div>
      ) : filteredLists.length > 0 ? (
        <div className="space-y-2">
          {filteredLists.map((list) => (
            <div
              key={list.id}
              onClick={() => onListSelect(list.id)}
              className="group relative flex items-center gap-4 p-4 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-secondary hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <div 
                className="flex-shrink-0 w-10 h-10 rounded-md flex items-center justify-center relative bg-gray-100"
              >
                <List className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                <div
                  className="absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-white"
                  style={{backgroundColor: list.color || 'var(--gray-400)'}}
                />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-sm font-medium text-lia-text-primary truncate transition-colors">
                    {list.name}
                  </p>
                </div>
                {list.description && (
                  <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary truncate">
                    {truncateText(list.description, 60)}
                  </p>
                )}
              </div>

              <div className="flex-shrink-0 flex flex-col items-center justify-center px-4 border-l border-r border-lia-border-subtle dark:border-lia-border-subtle">
                <span className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                  {list.candidate_count || 0}
                </span>
                <span className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary uppercase tracking-wide">
                  {(list.candidate_count || 0) === 1 ? 'candidato' : 'candidatos'}
                </span>
              </div>

              <div className="flex-shrink-0 flex items-center gap-1.5 text-xs text-lia-text-secondary dark:text-lia-text-tertiary min-w-[100px]">
                <Calendar className="w-3.5 h-3.5" />
                <span>{formatDate(list.updated_at || list.created_at)}</span>
              </div>

              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 hover:bg-gray-100"
                  onClick={(e) => { e.stopPropagation(); openAddCandidateModal(list) }}
                  title="Adicionar candidatos"
                >
                  <UserPlus className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 hover:bg-gray-100"
                  onClick={(e) => { e.stopPropagation(); handleShareList(list) }}
                  title="Compartilhar lista"
                >
                  <Share2 className="w-4 h-4 lia-text-base" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 hover:bg-gray-100"
                  onClick={(e) => { e.stopPropagation(); openEditModal(list) }}
                  title="Editar lista"
                >
                  <Edit2 className="w-4 h-4 lia-text-base" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 hover:bg-gray-100"
                  onClick={(e) => { e.stopPropagation(); onAddToJobs(list.id) }}
                  title="Adicionar a vagas"
                >
                  <Briefcase className="w-4 h-4 lia-text-base" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 hover:text-status-error hover:bg-status-error/10"
                  onClick={(e) => { e.stopPropagation(); setListToDelete(list) }}
                  title="Excluir lista"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                    >
                      <MoreHorizontal className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuItem onClick={(e) => { e.stopPropagation(); openAddCandidateModal(list) }}>
                      <UserPlus className="w-4 h-4 mr-2" />
                      Adicionar candidatos
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onListSelect(list.id) }}>
                      <Users className="w-4 h-4 mr-2" />
                      Ver candidatos
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onAddToJobs(list.id) }}>
                      <Briefcase className="w-4 h-4 mr-2" />
                      Adicionar a vagas
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleShareList(list) }}>
                      <Share2 className="w-4 h-4 mr-2" />
                      Compartilhar lista
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={(e) => { e.stopPropagation(); openEditModal(list) }}>
                      <Edit2 className="w-4 h-4 mr-2" />
                      Editar lista
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={(e) => { e.stopPropagation(); setListToDelete(list) }}
                      className="text-status-error focus:text-status-error focus:bg-status-error/10"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Excluir lista
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              <ChevronRight className="w-5 h-5 lia-text-muted group-hover:lia-text-base transition-colors flex-shrink-0" />
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 px-4">
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center mb-4 bg-gray-100"
          >
            <FolderOpen className="w-8 h-8 text-lia-text-tertiary dark:text-lia-text-tertiary" />
          </div>
          <h3 className="text-lg font-medium text-lia-text-primary mb-2 font-['Open_Sans',sans-serif]">
            {searchTerm ? 'Nenhuma lista encontrada' : 'Nenhuma lista criada'}
          </h3>
          <p className="text-sm text-lia-text-primary dark:text-lia-text-primary text-center max-w-md mb-6">
            {searchTerm
              ? `Não encontramos listas com o termo "${searchTerm}". Tente outro termo ou crie uma nova lista.`
              : 'Crie sua primeira lista para organizar candidatos de forma eficiente. Você pode agrupar candidatos por vaga, perfil ou qualquer critério.'}
          </p>
          {!searchTerm && (
            <Button
              onClick={openCreateModal}
              className="gap-2 bg-gray-900 hover:bg-gray-800 text-white"
            >
              <Plus className="w-4 h-4" />
              Criar primeira lista
            </Button>
          )}
        </div>
      )}

      {/* Compartilhados Section */}
      <div className="mt-8 pt-6 border-t border-lia-border-subtle dark:border-lia-border-subtle">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
            <Link2 className="w-4 h-4 lia-text-base" />
            Compartilhados
            {totalNewFeedbacks > 0 && (
              <Badge className="bg-gray-100 lia-text-base border-lia-border-subtle text-micro ml-2">
                {totalNewFeedbacks} {totalNewFeedbacks === 1 ? 'novo' : 'novos'} ●
              </Badge>
            )}
          </h3>
        </div>

        {loadingShared ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin lia-text-secondary" />
            <span className="ml-2 text-xs lia-text-base">Carregando compartilhamentos...</span>
          </div>
        ) : sharedSearches.length > 0 ? (
          <div className="space-y-2">
            {sharedSearches.map((shared) => (
              <div
                key={shared.id}
                className="group relative p-4 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-secondary hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0 w-10 h-10 rounded-md flex items-center justify-center bg-gray-100 dark:bg-lia-bg-secondary">
                      <Link2 className="w-5 h-5 lia-text-base" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-lia-text-primary">
                          {shared.title}
                        </p>
                        {getStatusBadge(shared.status)}
                      </div>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        {shared.share_type === 'search' ? 'Busca' : 'Lista'} • {shared.candidate_count} {shared.candidate_count === 1 ? 'candidato' : 'candidatos'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 mb-3">
                  <p className="text-xs text-lia-text-secondary dark:text-lia-text-secondary">
                    <span className="font-medium">Destinatário:</span> {shared.recipient_name || shared.recipient_email}
                  </p>
                  <p className="text-xs flex items-center gap-1">
                    {shared.first_accessed_at ? (
                      <>
                        <Eye className="w-3 h-3 text-status-success" />
                        <span className="text-status-success">Acessado</span>
                      </>
                    ) : (
                      <>
                        <Clock className="w-3 h-3 lia-text-secondary" />
                        <span className="lia-text-secondary">Não acessou ainda</span>
                      </>
                    )}
                  </p>
                </div>

                <div className={`flex items-center gap-3 text-xs ${shared.feedback_counts?.new_count > 0 ? 'lia-text-strong font-medium' : 'lia-text-base'}`}>
                  <span className="font-medium">Feedbacks:</span>
                  <span className="flex items-center gap-1">
                    <ThumbsUp className="w-3 h-3" />
                    {shared.feedback_counts?.approved || 0}
                  </span>
                  <span className="flex items-center gap-1">
                    <ThumbsDown className="w-3 h-3" />
                    {shared.feedback_counts?.rejected || 0}
                  </span>
                  <span className="flex items-center gap-1">
                    <HelpCircle className="w-3 h-3" />
                    {shared.feedback_counts?.maybe || 0}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {shared.feedback_counts?.pending || 0}
                  </span>
                </div>

                <div className="flex items-center gap-2 mt-4 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-xs gap-1"
                    onClick={() => handleViewDetails(shared.id)}
                  >
                    <Eye className="w-3 h-3" />
                    Ver Detalhes
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-xs gap-1"
                    onClick={() => handleCopyLink(shared.share_url)}
                  >
                    <Copy className="w-3 h-3" />
                    Copiar Link
                  </Button>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-44">
                      <DropdownMenuItem onClick={() => handleResendInvite(shared.id)}>
                        <Send className="w-4 h-4 mr-2" />
                        Reenviar Convite
                      </DropdownMenuItem>
                      {shared.status === 'active' && (
                        <DropdownMenuItem
                          onClick={() => handleRevokeShare(shared.id)}
                          className="text-status-error focus:text-status-error focus:bg-status-error/10"
                        >
                          <XCircle className="w-4 h-4 mr-2" />
                          Encerrar
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 px-4 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md border border-dashed border-lia-border-subtle dark:border-lia-border-subtle">
            <div className="w-12 h-12 rounded-full flex items-center justify-center mb-3 bg-gray-100 dark:bg-lia-bg-secondary">
              <Link2 className="w-6 h-6 text-lia-text-disabled" />
            </div>
            <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary text-center max-w-sm">
              Nenhum compartilhamento. Compartilhe buscas ou listas com gestores para receber feedback.
            </p>
          </div>
        )}
      </div>

      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Open_Sans',sans-serif]">
              {editingList ? 'Editar Lista' : 'Nova Lista'}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                Nome da lista <span className="text-status-error">*</span>
              </label>
              <Input
                placeholder="Ex: Candidatos para entrevista"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                className="h-9"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                Descrição
              </label>
              <Textarea
                placeholder="Descreva o propósito desta lista..."
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                rows={3}
                className="resize-none"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                Cor
              </label>
              <div className="flex flex-wrap gap-2">
                {LIST_COLORS.map((color) => (
                  <button
                    key={color.value}
                    type="button"
                    onClick={() => setFormColor(color.value)}
                    className={`w-8 h-8 rounded-full flex items-center justify-center transition-[width,height] ${
 formColor === color.value
                        ? 'ring-2 ring-offset-2 ring-gray-400'
                        : 'hover:scale-110'
                    }`}
                    style={{backgroundColor: color.value}}
                    title={color.name}
                  >
                    {formColor === color.value && (
                      <Check className="w-4 h-4 text-white" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={closeModal}
              disabled={saving}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleSave}
              disabled={saving || !formName.trim()}
              className="bg-gray-900 hover:bg-gray-800 text-white"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Salvando...
                </>
              ) : editingList ? (
                'Salvar alterações'
              ) : (
                'Criar lista'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!listToDelete} onOpenChange={(open: boolean) => !open && setListToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="font-['Open_Sans',sans-serif]">
              Excluir lista?
            </AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir a lista <strong>"{listToDelete?.name}"</strong>?
              {listToDelete && listToDelete.candidate_count > 0 && (
                <span className="block mt-2 text-status-warning">
                  Esta lista contém {listToDelete.candidate_count} {listToDelete.candidate_count === 1 ? 'candidato' : 'candidatos'}.
                  Os candidatos não serão excluídos, apenas a associação com esta lista.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-status-error hover:bg-status-error"
            >
              {deleting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Excluindo...
                </>
              ) : (
                'Excluir'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* SharedSearch Details Modal */}
      <SharedSearchDetailsModal
        open={showDetailsModal}
        onClose={() => setShowDetailsModal(false)}
        sharedSearchId={selectedSharedSearch || ''}
        onCreateList={handleCreateListFromShared}
        onAddToJob={handleAddToJobFromShared}
        onCreateJob={handleCreateJobFromShared}
      />

      {/* Add to Job Modal */}
      <AddToJobModal
        open={showAddToJobModal}
        onClose={() => setShowAddToJobModal(false)}
        candidateIds={selectedCandidateIds}
        candidateNames={selectedCandidateNames}
        feedbackComments={feedbackComments}
        sharedSearchId={selectedSharedSearch || undefined}
        onSuccess={() => {
          setShowAddToJobModal(false)
          loadSharedSearches()
          toast({ title: "Candidatos adicionados com sucesso!" })
        }}
      />

      {/* Share List Modal */}
      {shareListData && (
        <ShareSearchModal
          open={showShareModal}
          onClose={() => {
            setShowShareModal(false)
            setShareListData(null)
          }}
          shareType="list"
          title={shareListData.name}
          candidateIds={[]}
          candidateCount={shareListData.candidateCount}
          sourceListId={shareListData.id}
          onSuccess={() => {
            setShowShareModal(false)
            setShareListData(null)
            loadSharedSearches()
          }}
        />
      )}
    </div>
  )
}
