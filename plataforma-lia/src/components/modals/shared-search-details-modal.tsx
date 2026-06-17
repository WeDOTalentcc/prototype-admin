"use client"

import { useState, useEffect, useMemo, useCallback } from"react"
import { Button } from"@/components/ui/button"
import { Chip } from"@/components/ui/chip"
import { Checkbox } from"@/components/ui/checkbox"
import { Progress } from"@/components/ui/progress"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from"@/components/ui/dialog"
import { Tabs, TabsList, TabsTrigger } from"@/components/ui/tabs"
import { 
  X, 
  Loader2, 
  Users, 
  Search, 
  List,
  Eye,
  Calendar,
  Clock,
  ThumbsUp,
  ThumbsDown,
  HelpCircle,
  Star,
  Plus,
  Briefcase,
  ListPlus
} from"lucide-react"
import { cn } from"@/lib/utils"
import { liaApi, SharedSearchDetail, CandidateSnapshot, CandidateFeedback } from"@/services/lia-api"
import { toast } from"sonner"

interface SharedSearchDetailsModalProps {
  open: boolean
  onClose: () => void
  sharedSearchId: string
  onCreateList?: (candidateIds: string[]) => void
  onAddToJob?: (candidateIds: string[]) => void
  onCreateJob?: (candidateIds: string[]) => void
}

type FilterType = 'all' | 'approved' | 'maybe' | 'rejected' | 'pending'

export function SharedSearchDetailsModal({
  open,
  onClose,
  sharedSearchId,
  onCreateList,
  onAddToJob,
  onCreateJob
}: SharedSearchDetailsModalProps) {
const [sharedSearch, setSharedSearch] = useState<SharedSearchDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState<FilterType>('all')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const loadDetails = useCallback(async () => {
    try {
      setLoading(true)
      const data = await liaApi.getSharedSearchDetail(sharedSearchId)
      setSharedSearch(data)
    } catch (error) {
      toast.error("Erro ao carregar detalhes", { description:"Não foi possível carregar os detalhes do compartilhamento." })
    } finally {
      setLoading(false)
    }
  }, [sharedSearchId])

  useEffect(() => {
    if (open && sharedSearchId) {
      loadDetails()
    }
  }, [open, sharedSearchId, loadDetails])

  useEffect(() => {
    if (!open) {
      setSharedSearch(null)
      setLoading(true)
      setActiveFilter('all')
      setSelectedIds(new Set())
    }
  }, [open])
  const feedbackMap = useMemo(() => {
    if (!sharedSearch) return new Map<string, CandidateFeedback>()
    const map = new Map<string, CandidateFeedback>()
    sharedSearch.feedbacks.forEach(fb => {
      map.set(fb.candidate_id, fb)
    })
    return map
  }, [sharedSearch])

  const candidatesWithFeedback = useMemo(() => {
    if (!sharedSearch) return []
    return sharedSearch.candidates.map(c => ({
      ...c,
      feedback: feedbackMap.get(c.id) || c.feedback
    }))
  }, [sharedSearch, feedbackMap])

  const feedbackCounts = useMemo(() => {
    const counts = { approved: 0, maybe: 0, rejected: 0, pending: 0 }
    candidatesWithFeedback.forEach(c => {
      if (c.feedback) {
        if (c.feedback.decision === 'approved') counts.approved++
        else if (c.feedback.decision === 'maybe') counts.maybe++
        else if (c.feedback.decision === 'rejected') counts.rejected++
      } else {
        counts.pending++
      }
    })
    return counts
  }, [candidatesWithFeedback])

  const filteredCandidates = useMemo(() => {
    if (activeFilter === 'all') return candidatesWithFeedback
    return candidatesWithFeedback.filter(c => {
      if (activeFilter === 'pending') return !c.feedback
      return c.feedback?.decision === activeFilter
    })
  }, [candidatesWithFeedback, activeFilter])

  const totalEvaluated = feedbackCounts.approved + feedbackCounts.maybe + feedbackCounts.rejected
  const totalCandidates = sharedSearch?.candidate_count || 0
  const progressPercent = totalCandidates > 0 ? (totalEvaluated / totalCandidates) * 100 : 0

  const approvedIds = useMemo(() => {
    return candidatesWithFeedback
      .filter(c => c.feedback?.decision === 'approved')
      .map(c => c.id)
  }, [candidatesWithFeedback])

  const allApprovedSelected = approvedIds.length > 0 && approvedIds.every(id => selectedIds.has(id))

  const toggleCandidate = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const toggleAllApproved = () => {
    if (allApprovedSelected) {
      setSelectedIds(prev => {
        const next = new Set(prev)
        approvedIds.forEach(id => next.delete(id))
        return next
      })
    } else {
      setSelectedIds(prev => {
        const next = new Set(prev)
        approvedIds.forEach(id => next.add(id))
        return next
      })
    }
  }

  const handleCreateList = () => {
    if (selectedIds.size === 0) {
      toast.error("Selecione candidatos", { description:"Selecione pelo menos um candidato para criar a lista." })
      return
    }
    onCreateList?.(Array.from(selectedIds))
  }

  const handleAddToJob = () => {
    if (selectedIds.size === 0) {
      toast.error("Selecione candidatos", { description:"Selecione pelo menos um candidato para adicionar à vaga." })
      return
    }
    onAddToJob?.(Array.from(selectedIds))
  }

  const handleCreateJob = () => {
    if (selectedIds.size === 0) {
      toast.error("Selecione candidatos", { description:"Selecione pelo menos um candidato para criar a vaga." })
      return
    }
    onCreateJob?.(Array.from(selectedIds))
  }

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    })
  }

  const getStatusBadge = (status: 'active' | 'expired' | 'revoked') => {
    switch (status) {
      case 'active':
        return <Chip variant="success">Ativo</Chip>
      case 'expired':
        return <Chip variant="danger">Expirado</Chip>
      case 'revoked':
        return <Chip variant="neutral" muted>Revogado</Chip>
    }
  }

  const getDecisionBadge = (feedback?: CandidateFeedback) => {
    if (!feedback) {
      return (
        <Chip variant="neutral" muted>
          <Clock className="w-3 h-3" />
          Pendente
        </Chip>
      )
    }
    switch (feedback.decision) {
      case 'approved':
        return (
          <Chip variant="success">
            <ThumbsUp className="w-3 h-3" />
            Interessado
          </Chip>
        )
      case 'maybe':
        return (
          <Chip variant="warning">
            <HelpCircle className="w-3 h-3" />
            Talvez
          </Chip>
        )
      case 'rejected':
        return (
          <Chip variant="danger">
            <ThumbsDown className="w-3 h-3" />
            Não Interessado
          </Chip>
        )
    }
  }

  const recipient = sharedSearch?.recipients?.[0]

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent 
        data-testid="shared-search-details-modal"
        className="max-w-3xl bg-lia-bg-overlay border-lia-border-default text-white p-0 gap-0 max-h-[90vh] flex flex-col"
       
      >
        <DialogHeader className="px-5 py-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <DialogTitle className="text-base font-semibold text-white flex items-center gap-2">
                {sharedSearch?.share_type === 'search' ? (
                  <Search className="w-5 h-5 text-lia-text-muted" />
                ) : (
                  <List className="w-5 h-5 text-lia-text-muted" />
                )}
                {sharedSearch?.title || 'Carregando...'}
              </DialogTitle>
              {sharedSearch && (
                <>
                  <Chip variant="neutral" muted density="compact">
                    {sharedSearch.share_type === 'search' ? 'Busca' : 'Lista'}
                  </Chip>
                  {getStatusBadge(sharedSearch.status)}
                </>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-8 w-8 text-lia-text-tertiary hover:text-white hover:bg-lia-bg-tertiary"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-20" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
          </div>
        ) : sharedSearch ? (
          <>
            <div className="flex-1 overflow-y-auto">
              <div className="p-5 space-y-5">
                <div className="bg-lia-bg-tertiary dark:bg-lia-btn-primary-bg rounded-xl p-4 border border-lia-border-default">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-lia-text-tertiary text-xs mb-1">Compartilhado com</p>
                      <p className="text-white font-medium text-xs">
                        {recipient?.name || recipient?.email || '-'}
                      </p>
                      {recipient?.name && (
                        <p className="text-lia-text-secondary text-micro">{recipient.email}</p>
                      )}
                    </div>
                    <div>
                      <p className="text-lia-text-tertiary text-xs mb-1 flex items-center gap-1">
                        <Eye className="w-3 h-3" /> Primeiro Acesso
                      </p>
                      <p className="text-white font-medium text-xs">
                        {formatDate(recipient?.first_accessed_at)}
                      </p>
                      <p className="text-lia-text-secondary text-micro">
                        {recipient?.total_views || 0} visualizações
                      </p>
                    </div>
                    <div>
                      <p className="text-lia-text-tertiary text-xs mb-1 flex items-center gap-1">
                        <Calendar className="w-3 h-3" /> Expira em
                      </p>
                      <p className="text-white font-medium text-xs">
                        {sharedSearch.expires_at ? formatDate(sharedSearch.expires_at) : 'Sem prazo'}
                      </p>
                    </div>
                    <div>
                      <p className="text-lia-text-tertiary text-xs mb-1">Progresso</p>
                      <div className="flex items-center gap-2">
                        <Progress value={progressPercent} className="h-2 flex-1 bg-lia-bg-tertiary" />
                        <span className="text-xs text-lia-text-muted whitespace-nowrap">
                          {totalEvaluated}/{totalCandidates}
                        </span>
                      </div>
                      <p className="text-lia-text-secondary text-micro mt-0.5" aria-live="polite" aria-atomic="true">candidatos avaliados</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-3">
                  <div className="bg-lia-bg-tertiary dark:bg-lia-btn-primary-bg rounded-xl p-4 border border-lia-border-default text-center">
                    <div className="text-2xl mb-1">👍</div>
                    <p className="text-2xl font-semibold text-status-success">{feedbackCounts.approved}</p>
                    <p className="text-xs text-lia-text-tertiary">Interessados</p>
                  </div>
                  <div className="bg-lia-bg-tertiary dark:bg-lia-btn-primary-bg rounded-xl p-4 border border-lia-border-default text-center">
                    <div className="text-2xl mb-1">🤔</div>
                    <p className="text-2xl font-semibold text-status-warning">{feedbackCounts.maybe}</p>
                    <p className="text-xs text-lia-text-tertiary">Talvez</p>
                  </div>
                  <div className="bg-lia-bg-tertiary dark:bg-lia-btn-primary-bg rounded-xl p-4 border border-lia-border-default text-center">
                    <div className="text-2xl mb-1">👎</div>
                    <p className="text-2xl font-semibold text-status-error">{feedbackCounts.rejected}</p>
                    <p className="text-xs text-lia-text-tertiary">Não Interessados</p>
                  </div>
                  <div className="bg-lia-bg-tertiary dark:bg-lia-btn-primary-bg rounded-xl p-4 border border-lia-border-default text-center">
                    <div className="text-2xl mb-1">⏳</div>
                    <p className="text-2xl font-semibold text-lia-text-tertiary">{feedbackCounts.pending}</p>
                    <p className="text-xs text-lia-text-tertiary">Pendentes</p>
                  </div>
                </div>

                <Tabs value={activeFilter} onValueChange={(v) => setActiveFilter(v as FilterType)}>
                  <TabsList className="bg-lia-bg-tertiary dark:bg-lia-btn-primary-bg border border-lia-border-default p-1 h-auto">
                    <TabsTrigger 
                      value="all" 
                      className="text-xs px-3 py-1.5 data-[state=active]:bg-lia-bg-tertiary data-[state=active]:text-white"
                    >
                      Todos
                      <Chip variant="neutral" muted density="compact" className="ml-1.5">
                        {totalCandidates}
                      </Chip>
                    </TabsTrigger>
                    <TabsTrigger 
                      value="approved" 
                      className="text-xs px-3 py-1.5 data-[state=active]:bg-lia-bg-tertiary data-[state=active]:text-white"
                    >
                      Interessados
                      <Chip variant="success" density="compact" className="ml-1.5">
                        {feedbackCounts.approved}
                      </Chip>
                    </TabsTrigger>
                    <TabsTrigger 
                      value="maybe" 
                      className="text-xs px-3 py-1.5 data-[state=active]:bg-lia-bg-tertiary data-[state=active]:text-white"
                    >
                      Talvez
                      <Chip variant="warning" density="compact" className="ml-1.5">
                        {feedbackCounts.maybe}
                      </Chip>
                    </TabsTrigger>
                    <TabsTrigger 
                      value="rejected" 
                      className="text-xs px-3 py-1.5 data-[state=active]:bg-lia-bg-tertiary data-[state=active]:text-white"
                    >
                      Não
                      <Chip variant="danger" density="compact" className="ml-1.5">
                        {feedbackCounts.rejected}
                      </Chip>
                    </TabsTrigger>
                    <TabsTrigger 
                      value="pending" 
                      className="text-xs px-3 py-1.5 data-[state=active]:bg-lia-bg-tertiary data-[state=active]:text-white"
                    >
                      Pendentes
                      <Chip variant="neutral" muted density="compact" className="ml-1.5">
                        {feedbackCounts.pending}
                      </Chip>
                    </TabsTrigger>
                  </TabsList>
                </Tabs>

                <div className="space-y-2">
                  {approvedIds.length > 0 && (
                    <div className="flex items-center gap-2 px-1 py-2">
                      <Checkbox
                        id="select-all-approved"
                        checked={allApprovedSelected}
                        onCheckedChange={toggleAllApproved}
                        className="border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                      />
                      <label 
                        htmlFor="select-all-approved" 
                        className="text-xs text-lia-text-muted cursor-pointer"
                      >
                        Selecionar todos aprovados ({approvedIds.length})
                      </label>
                    </div>
                  )}

                  {filteredCandidates.length === 0 ? (
                    <div className="text-center py-10 text-lia-text-secondary text-sm">
                      Nenhum candidato encontrado neste filtro
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {filteredCandidates.map(candidate => (
                        <div 
                          key={candidate.id}
                          className={cn("bg-lia-bg-tertiary dark:bg-lia-btn-primary-bg rounded-md p-3 border border-lia-border-default flex items-start gap-3","hover:border-lia-border-default transition-colors motion-reduce:transition-none"
                          )}
                        >
                          <Checkbox
                            checked={selectedIds.has(candidate.id)}
                            onCheckedChange={() => toggleCandidate(candidate.id)}
                            className="mt-1 border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <p className="text-white font-medium text-xs">{candidate.name}</p>
                                <p className="text-lia-text-tertiary text-xs">
                                  {candidate.title}
                                  {candidate.company && ` • ${candidate.company}`}
                                </p>
                                {candidate.location && (
                                  <p className="text-lia-text-secondary text-micro mt-0.5">{candidate.location}</p>
                                )}
                              </div>
                              <div className="flex-shrink-0">
                                {getDecisionBadge(candidate.feedback)}
                              </div>
                            </div>
                            
                            {candidate.feedback && (
                              <div className="mt-2 pt-2 border-t border-lia-border-default/50">
                                {candidate.feedback.rating && (
                                  <div className="flex items-center gap-1 mb-1">
                                    {[...Array(5)].map((_, i) => (
                                      <Star
                                        key={i}
                                        className={cn("w-3 h-3",
                                          i < candidate.feedback!.rating!
                                            ?"text-status-warning fill-amber-400"
                                            :"text-lia-text-secondary"
                                        )}
                                      />
                                    ))}
                                  </div>
                                )}
                                {candidate.feedback.comment && (
                                  <p className="text-lia-text-tertiary text-xs italic">"{candidate.feedback.comment}"
                                  </p>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="flex-shrink-0 px-5 py-4 border-t border-lia-border-default bg-lia-bg-tertiary dark:bg-lia-btn-primary-bg/50">
              <div className="flex items-center justify-between">
                <p className="text-xs text-lia-text-muted">
                  <span className="font-semibold text-white">
                    {selectedIds.size}
                  </span>
                  {' '}candidato{selectedIds.size !== 1 ? 's' : ''} selecionado{selectedIds.size !== 1 ? 's' : ''}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCreateList}
                    disabled={selectedIds.size === 0}
                    className="text-xs h-8 bg-transparent border-lia-border-default text-lia-text-disabled hover:bg-lia-bg-tertiary hover:text-white disabled:opacity-50"
                  >
                    <ListPlus className="w-3.5 h-3.5 mr-1.5" />
                    Criar Lista
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleAddToJob}
                    disabled={selectedIds.size === 0}
                    className="text-xs h-8 bg-transparent border-lia-border-default text-lia-text-disabled hover:bg-lia-bg-tertiary hover:text-white disabled:opacity-50"
                  >
                    <Plus className="w-3.5 h-3.5 mr-1.5" />
                    Adicionar à Vaga
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleCreateJob}
                    disabled={selectedIds.size === 0}
                    className="text-xs h-8 text-white disabled:opacity-50 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover"
                  >
                    <Briefcase className="w-3.5 h-3.5 mr-1.5" />
                    Criar Vaga
                  </Button>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center py-20 text-lia-text-secondary">
            Erro ao carregar detalhes
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
