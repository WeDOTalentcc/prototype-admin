"use client"

import { useState, useEffect, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/hooks/use-toast"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
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
} from "lucide-react"
import { cn } from "@/lib/utils"
import { liaApi, SharedSearchDetail, CandidateSnapshot, CandidateFeedback } from "@/services/lia-api"

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
  const { toast } = useToast()
  const [sharedSearch, setSharedSearch] = useState<SharedSearchDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState<FilterType>('all')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (open && sharedSearchId) {
      loadDetails()
    }
  }, [open, sharedSearchId])

  useEffect(() => {
    if (!open) {
      setSharedSearch(null)
      setLoading(true)
      setActiveFilter('all')
      setSelectedIds(new Set())
    }
  }, [open])

  const loadDetails = async () => {
    try {
      setLoading(true)
      const data = await liaApi.getSharedSearchDetail(sharedSearchId)
      setSharedSearch(data)
    } catch (error) {
      console.error('Failed to load shared search details:', error)
      toast({
        title: "Erro ao carregar detalhes",
        description: "Não foi possível carregar os detalhes do compartilhamento.",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

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
      toast({
        title: "Selecione candidatos",
        description: "Selecione pelo menos um candidato para criar a lista.",
        variant: "destructive"
      })
      return
    }
    onCreateList?.(Array.from(selectedIds))
  }

  const handleAddToJob = () => {
    if (selectedIds.size === 0) {
      toast({
        title: "Selecione candidatos",
        description: "Selecione pelo menos um candidato para adicionar à vaga.",
        variant: "destructive"
      })
      return
    }
    onAddToJob?.(Array.from(selectedIds))
  }

  const handleCreateJob = () => {
    if (selectedIds.size === 0) {
      toast({
        title: "Selecione candidatos",
        description: "Selecione pelo menos um candidato para criar a vaga.",
        variant: "destructive"
      })
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
        return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-micro">Ativo</Badge>
      case 'expired':
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-micro">Expirado</Badge>
      case 'revoked':
        return <Badge className="bg-zinc-600/50 text-zinc-400 border-zinc-500/30 text-micro">Revogado</Badge>
    }
  }

  const getDecisionBadge = (feedback?: CandidateFeedback) => {
    if (!feedback) {
      return (
        <Badge className="bg-zinc-600/50 text-zinc-400 border-zinc-500/30 text-micro gap-1">
          <Clock className="w-3 h-3" />
          Pendente
        </Badge>
      )
    }
    switch (feedback.decision) {
      case 'approved':
        return (
          <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-micro gap-1">
            <ThumbsUp className="w-3 h-3" />
            Interessado
          </Badge>
        )
      case 'maybe':
        return (
          <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 text-micro gap-1">
            <HelpCircle className="w-3 h-3" />
            Talvez
          </Badge>
        )
      case 'rejected':
        return (
          <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-micro gap-1">
            <ThumbsDown className="w-3 h-3" />
            Não Interessado
          </Badge>
        )
    }
  }

  const recipient = sharedSearch?.recipients?.[0]

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent 
        className="max-w-3xl bg-zinc-900 border-zinc-700 text-white p-0 gap-0 max-h-[90vh] flex flex-col"
        style={{ fontFamily: '"Open Sans", sans-serif' }}
      >
        <DialogHeader className="px-5 py-4 border-b border-zinc-700 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <DialogTitle className="text-base font-semibold text-white flex items-center gap-2">
                {sharedSearch?.share_type === 'search' ? (
                  <Search className="w-5 h-5 text-gray-400" />
                ) : (
                  <List className="w-5 h-5 text-gray-400" />
                )}
                {sharedSearch?.title || 'Carregando...'}
              </DialogTitle>
              {sharedSearch && (
                <>
                  <Badge className="bg-zinc-700 text-zinc-300 border-zinc-600 text-micro">
                    {sharedSearch.share_type === 'search' ? 'Busca' : 'Lista'}
                  </Badge>
                  {getStatusBadge(sharedSearch.status)}
                </>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="h-8 w-8 text-zinc-400 hover:text-white hover:bg-zinc-700"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-zinc-500" />
          </div>
        ) : sharedSearch ? (
          <>
            <div className="flex-1 overflow-y-auto">
              <div className="p-5 space-y-5">
                <div className="bg-zinc-800 rounded-md p-4 border border-zinc-700">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-zinc-400 text-xs mb-1">Compartilhado com</p>
                      <p className="text-white font-medium text-xs">
                        {recipient?.name || recipient?.email || '-'}
                      </p>
                      {recipient?.name && (
                        <p className="text-zinc-500 text-micro">{recipient.email}</p>
                      )}
                    </div>
                    <div>
                      <p className="text-zinc-400 text-xs mb-1 flex items-center gap-1">
                        <Eye className="w-3 h-3" /> Primeiro Acesso
                      </p>
                      <p className="text-white font-medium text-xs">
                        {formatDate(recipient?.first_accessed_at)}
                      </p>
                      <p className="text-zinc-500 text-micro">
                        {recipient?.total_views || 0} visualizações
                      </p>
                    </div>
                    <div>
                      <p className="text-zinc-400 text-xs mb-1 flex items-center gap-1">
                        <Calendar className="w-3 h-3" /> Expira em
                      </p>
                      <p className="text-white font-medium text-xs">
                        {sharedSearch.expires_at ? formatDate(sharedSearch.expires_at) : 'Sem prazo'}
                      </p>
                    </div>
                    <div>
                      <p className="text-zinc-400 text-xs mb-1">Progresso</p>
                      <div className="flex items-center gap-2">
                        <Progress value={progressPercent} className="h-2 flex-1 bg-zinc-700" />
                        <span className="text-xs text-zinc-300 whitespace-nowrap">
                          {totalEvaluated}/{totalCandidates}
                        </span>
                      </div>
                      <p className="text-zinc-500 text-micro mt-0.5">candidatos avaliados</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-3">
                  <div className="bg-zinc-800 rounded-md p-4 border border-zinc-700 text-center">
                    <div className="text-2xl mb-1">👍</div>
                    <p className="text-2xl font-bold text-emerald-400">{feedbackCounts.approved}</p>
                    <p className="text-xs text-zinc-400">Interessados</p>
                  </div>
                  <div className="bg-zinc-800 rounded-md p-4 border border-zinc-700 text-center">
                    <div className="text-2xl mb-1">🤔</div>
                    <p className="text-2xl font-bold text-amber-400">{feedbackCounts.maybe}</p>
                    <p className="text-xs text-zinc-400">Talvez</p>
                  </div>
                  <div className="bg-zinc-800 rounded-md p-4 border border-zinc-700 text-center">
                    <div className="text-2xl mb-1">👎</div>
                    <p className="text-2xl font-bold text-red-400">{feedbackCounts.rejected}</p>
                    <p className="text-xs text-zinc-400">Não Interessados</p>
                  </div>
                  <div className="bg-zinc-800 rounded-md p-4 border border-zinc-700 text-center">
                    <div className="text-2xl mb-1">⏳</div>
                    <p className="text-2xl font-bold text-zinc-400">{feedbackCounts.pending}</p>
                    <p className="text-xs text-zinc-400">Pendentes</p>
                  </div>
                </div>

                <Tabs value={activeFilter} onValueChange={(v) => setActiveFilter(v as FilterType)}>
                  <TabsList className="bg-zinc-800 border border-zinc-700 p-1 h-auto">
                    <TabsTrigger 
                      value="all" 
                      className="text-xs px-3 py-1.5 data-[state=active]:bg-zinc-700 data-[state=active]:text-white"
                    >
                      Todos
                      <Badge className="ml-1.5 text-micro px-1.5 py-0 bg-zinc-600 text-zinc-300">
                        {totalCandidates}
                      </Badge>
                    </TabsTrigger>
                    <TabsTrigger 
                      value="approved" 
                      className="text-xs px-3 py-1.5 data-[state=active]:bg-zinc-700 data-[state=active]:text-white"
                    >
                      Interessados
                      <Badge className="ml-1.5 text-micro px-1.5 py-0 bg-emerald-500/20 text-emerald-400">
                        {feedbackCounts.approved}
                      </Badge>
                    </TabsTrigger>
                    <TabsTrigger 
                      value="maybe" 
                      className="text-xs px-3 py-1.5 data-[state=active]:bg-zinc-700 data-[state=active]:text-white"
                    >
                      Talvez
                      <Badge className="ml-1.5 text-micro px-1.5 py-0 bg-amber-500/20 text-amber-400">
                        {feedbackCounts.maybe}
                      </Badge>
                    </TabsTrigger>
                    <TabsTrigger 
                      value="rejected" 
                      className="text-xs px-3 py-1.5 data-[state=active]:bg-zinc-700 data-[state=active]:text-white"
                    >
                      Não
                      <Badge className="ml-1.5 text-micro px-1.5 py-0 bg-red-500/20 text-red-400">
                        {feedbackCounts.rejected}
                      </Badge>
                    </TabsTrigger>
                    <TabsTrigger 
                      value="pending" 
                      className="text-xs px-3 py-1.5 data-[state=active]:bg-zinc-700 data-[state=active]:text-white"
                    >
                      Pendentes
                      <Badge className="ml-1.5 text-micro px-1.5 py-0 bg-zinc-600 text-zinc-400">
                        {feedbackCounts.pending}
                      </Badge>
                    </TabsTrigger>
                  </TabsList>
                </Tabs>

                <div className="space-y-2">
                  {approvedIds.length > 0 && (
                    <div className="flex items-center gap-2 px-1 py-2 border-b border-zinc-700">
                      <Checkbox
                        id="select-all-approved"
                        checked={allApprovedSelected}
                        onCheckedChange={toggleAllApproved}
                        className="border-zinc-500 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                      />
                      <label 
                        htmlFor="select-all-approved" 
                        className="text-xs text-zinc-300 cursor-pointer"
                      >
                        Selecionar todos aprovados ({approvedIds.length})
                      </label>
                    </div>
                  )}

                  {filteredCandidates.length === 0 ? (
                    <div className="text-center py-10 text-zinc-500 text-sm">
                      Nenhum candidato encontrado neste filtro
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {filteredCandidates.map(candidate => (
                        <div 
                          key={candidate.id}
                          className={cn(
                            "bg-zinc-800 rounded-md p-3 border border-zinc-700 flex items-start gap-3",
                            "hover:border-zinc-600 transition-colors"
                          )}
                        >
                          <Checkbox
                            checked={selectedIds.has(candidate.id)}
                            onCheckedChange={() => toggleCandidate(candidate.id)}
                            className="mt-1 border-zinc-500 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <p className="text-white font-medium text-xs">{candidate.name}</p>
                                <p className="text-zinc-400 text-xs">
                                  {candidate.title}
                                  {candidate.company && ` • ${candidate.company}`}
                                </p>
                                {candidate.location && (
                                  <p className="text-zinc-500 text-micro mt-0.5">{candidate.location}</p>
                                )}
                              </div>
                              <div className="flex-shrink-0">
                                {getDecisionBadge(candidate.feedback)}
                              </div>
                            </div>
                            
                            {candidate.feedback && (
                              <div className="mt-2 pt-2 border-t border-zinc-700/50">
                                {candidate.feedback.rating && (
                                  <div className="flex items-center gap-1 mb-1">
                                    {[...Array(5)].map((_, i) => (
                                      <Star
                                        key={i}
                                        className={cn(
                                          "w-3 h-3",
                                          i < candidate.feedback!.rating!
                                            ? "text-amber-400 fill-amber-400"
                                            : "text-zinc-600"
                                        )}
                                      />
                                    ))}
                                  </div>
                                )}
                                {candidate.feedback.comment && (
                                  <p className="text-zinc-400 text-xs italic">
                                    "{candidate.feedback.comment}"
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

            <div className="flex-shrink-0 px-5 py-4 border-t border-zinc-700 bg-zinc-800/50">
              <div className="flex items-center justify-between">
                <p className="text-xs text-zinc-300">
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
                    className="text-xs h-8 bg-transparent border-zinc-600 text-zinc-300 hover:bg-zinc-700 hover:text-white disabled:opacity-50"
                  >
                    <ListPlus className="w-3.5 h-3.5 mr-1.5" />
                    Criar Lista
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleAddToJob}
                    disabled={selectedIds.size === 0}
                    className="text-xs h-8 bg-transparent border-zinc-600 text-zinc-300 hover:bg-zinc-700 hover:text-white disabled:opacity-50"
                  >
                    <Plus className="w-3.5 h-3.5 mr-1.5" />
                    Adicionar à Vaga
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleCreateJob}
                    disabled={selectedIds.size === 0}
                    className="text-xs h-8 text-white disabled:opacity-50 bg-gray-900 hover:bg-gray-800"
                  >
                    <Briefcase className="w-3.5 h-3.5 mr-1.5" />
                    Criar Vaga
                  </Button>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center py-20 text-zinc-500">
            Erro ao carregar detalhes
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
