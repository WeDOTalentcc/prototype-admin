"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { 
  CheckCircle, XCircle, Clock, AlertCircle, 
  Mail, User, Calendar, FileText, RefreshCw,
  Filter, Search, Eye
} from "lucide-react"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface ApprovalRequest {
  id: string
  company_id: string
  request_type: string
  requester_id: string | null
  requester_name: string
  requester_email: string
  target_id: string | null
  target_type: string | null
  target_name: string
  target_description: string | null
  target_data: Record<string, unknown>
  approver_id: string | null
  approver_name: string
  approver_email: string
  approval_level: number
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  priority: string
  due_date: string | null
  approval_notes: string | null
  rejection_reason: string | null
  email_sent: boolean
  resolved_at: string | null
  created_at: string
  updated_at: string
}

const REQUEST_TYPE_LABELS: Record<string, string> = {
  vacancy_approval: 'Aprovação de Vaga',
  candidate_hire: 'Aprovação de Contratação',
  offer_approval: 'Aprovação de Proposta',
  budget_approval: 'Aprovação de Orçamento',
  custom: 'Aprovação Personalizada'
}

const STATUS_CONFIG: Record<string, { label: string, color: string, icon: React.ComponentType<any> }> = {
  pending: { label: 'Pendente', color: 'bg-status-warning/15 text-status-warning', icon: Clock },
  approved: { label: 'Aprovado', color: 'bg-status-success/15 text-status-success', icon: CheckCircle },
  rejected: { label: 'Rejeitado', color: 'bg-status-error/15 text-status-error', icon: XCircle },
  cancelled: { label: 'Cancelado', color: 'bg-gray-100 text-gray-500', icon: AlertCircle }
}

const PRIORITY_CONFIG: Record<string, { label: string, color: string }> = {
  low: { label: 'Baixa', color: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400' },
  normal: { label: 'Normal', color: 'bg-gray-50 text-gray-600' },
  high: { label: 'Alta', color: 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300' },
  urgent: { label: 'Urgente', color: 'bg-status-error/10 text-status-error' }
}

interface ApprovalsHubProps {
  companyId: string
  currentUserEmail?: string
}

export function ApprovalsHub({ companyId, currentUserEmail = 'admin@example.com' }: ApprovalsHubProps) {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedApproval, setSelectedApproval] = useState<ApprovalRequest | null>(null)
  const [isDetailsOpen, setIsDetailsOpen] = useState(false)
  const [isActionDialogOpen, setIsActionDialogOpen] = useState(false)
  const [actionType, setActionType] = useState<'approve' | 'reject'>('approve')
  const [actionNotes, setActionNotes] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const fetchApprovals = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ company_id: companyId })
      if (statusFilter !== 'all') {
        params.append('status', statusFilter)
      }
      
      const response = await fetch(`/api/backend-proxy/approvals?${params.toString()}`)
      if (!response.ok) throw new Error('Failed to fetch approvals')
      const data = await response.json()
      setApprovals(data)
    } catch (err) {
      setError('Erro ao carregar aprovações')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchApprovals()
  }, [statusFilter, companyId])

  const handleApprove = async () => {
    if (!selectedApproval) return
    setIsSubmitting(true)
    try {
      const response = await fetch(
        `/api/backend-proxy/approvals/${selectedApproval.id}/approve?company_id=${encodeURIComponent(companyId)}&approved_by=${encodeURIComponent(currentUserEmail)}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ approval_notes: actionNotes })
        }
      )
      if (!response.ok) throw new Error('Failed to approve')
      setIsActionDialogOpen(false)
      setActionNotes('')
      setSelectedApproval(null)
      fetchApprovals()
    } catch (err) {
      setError('Erro ao aprovar solicitação')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleReject = async () => {
    if (!selectedApproval) return
    setIsSubmitting(true)
    try {
      const response = await fetch(
        `/api/backend-proxy/approvals/${selectedApproval.id}/reject?company_id=${encodeURIComponent(companyId)}&rejected_by=${encodeURIComponent(currentUserEmail)}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rejection_reason: actionNotes })
        }
      )
      if (!response.ok) throw new Error('Failed to reject')
      setIsActionDialogOpen(false)
      setActionNotes('')
      setSelectedApproval(null)
      fetchApprovals()
    } catch (err) {
      setError('Erro ao rejeitar solicitação')
    } finally {
      setIsSubmitting(false)
    }
  }

  const canApproveOrReject = (approval: ApprovalRequest): boolean => {
    return approval.approver_email.toLowerCase() === currentUserEmail.toLowerCase()
  }

  const openActionDialog = (approval: ApprovalRequest, type: 'approve' | 'reject') => {
    setSelectedApproval(approval)
    setActionType(type)
    setActionNotes('')
    setIsActionDialogOpen(true)
  }

  const openDetails = (approval: ApprovalRequest) => {
    setSelectedApproval(approval)
    setIsDetailsOpen(true)
  }

  const filteredApprovals = approvals.filter(approval => {
    if (searchTerm) {
      const search = searchTerm.toLowerCase()
      return (
        approval.target_name.toLowerCase().includes(search) ||
        approval.requester_name.toLowerCase().includes(search) ||
        approval.approver_name.toLowerCase().includes(search)
      )
    }
    return true
  })

  const pendingCount = approvals.filter(a => a.status === 'pending').length

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base-ui font-semibold font-['Open_Sans',sans-serif] text-gray-800 dark:text-gray-100">Aprovações</h2>
          <p className="text-xs text-gray-500">
            Gerencie solicitações de aprovação de vagas, contratações e propostas
          </p>
        </div>
        <div className="flex items-center gap-2">
          {pendingCount > 0 && (
            <Badge className="bg-status-warning/15 text-status-warning text-micro px-2 py-0.5">
              {pendingCount} pendente{pendingCount > 1 ? 's' : ''}
            </Badge>
          )}
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchApprovals}
            disabled={isLoading}
            className="text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>
      </div>

      <Card className="border border-gray-100">
        <CardHeader className="border-b border-gray-100 py-2">
          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
              <Input
                placeholder="Buscar por item, solicitante ou aprovador..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 py-1.5 px-2 text-xs border-gray-200"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-3.5 h-3.5 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="border border-gray-200 dark:border-gray-600 rounded-full px-2 py-1.5 text-xs bg-white dark:bg-gray-800 dark:text-gray-100"
              >
                <option value="all">Todos os status</option>
                <option value="pending">Pendentes</option>
                <option value="approved">Aprovados</option>
                <option value="rejected">Rejeitados</option>
                <option value="cancelled">Cancelados</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-10">
              <RefreshCw className="w-4 h-4 animate-spin text-gray-400" />
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <AlertCircle className="w-8 h-8 text-status-error mb-3" />
              <p className="text-xs text-gray-600">{error}</p>
              <Button variant="outline" onClick={fetchApprovals} className="mt-3 text-xs">
                Tentar novamente
              </Button>
            </div>
          ) : filteredApprovals.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <CheckCircle className="w-8 h-8 text-status-success mb-3" />
              <p className="text-xs text-gray-600">Nenhuma aprovação encontrada</p>
              <p className="text-xs text-gray-400 mt-1">
                {statusFilter === 'pending' 
                  ? 'Não há aprovações pendentes no momento' 
                  : 'Tente ajustar os filtros de busca'}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {filteredApprovals.map((approval) => {
                const statusConfig = STATUS_CONFIG[approval.status]
                const priorityConfig = PRIORITY_CONFIG[approval.priority] || PRIORITY_CONFIG.normal
                const StatusIcon = statusConfig.icon
                
                return (
                  <div 
                    key={approval.id} 
                    className="p-3 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-1.5 rounded-md ${statusConfig.color}`}>
                        <StatusIcon className="w-4 h-4" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <h4 className="text-xs font-medium text-gray-800 truncate">
                              {approval.target_name}
                            </h4>
                            <p className="text-xs text-gray-500 mt-0.5">
                              {REQUEST_TYPE_LABELS[approval.request_type] || approval.request_type}
                            </p>
                          </div>
                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            <Badge className={`${statusConfig.color} text-micro px-2 py-0.5`}>
                              {statusConfig.label}
                            </Badge>
                            <Badge className={`${priorityConfig.color} text-micro px-2 py-0.5`}>
                              {priorityConfig.label}
                            </Badge>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                          <div className="flex items-center gap-1">
                            <User className="w-3.5 h-3.5" />
                            <span>Solicitante: {approval.requester_name}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Mail className="w-3.5 h-3.5" />
                            <span>Aprovador: {approval.approver_name}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" />
                            <span>{formatDate(approval.created_at)}</span>
                          </div>
                        </div>
                        
                        {approval.target_description && (
                          <p className="text-xs text-gray-400 mt-1.5 line-clamp-2">
                            {approval.target_description}
                          </p>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openDetails(approval)}
                          className="h-7 w-7 p-0"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </Button>
                        
                        {approval.status === 'pending' && canApproveOrReject(approval) && (
                          <>
                            <Button
                              size="sm"
                              className="bg-status-success hover:bg-status-success text-white text-xs h-7 px-2"
                              onClick={() => openActionDialog(approval, 'approve')}
                            >
                              <CheckCircle className="w-3.5 h-3.5 mr-1" />
                              Aprovar
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="border-status-error/30 text-status-error hover:bg-status-error/10 text-xs h-7 px-2"
                              onClick={() => openActionDialog(approval, 'reject')}
                            >
                              <XCircle className="w-3.5 h-3.5 mr-1" />
                              Rejeitar
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-base-ui font-semibold font-['Open_Sans',sans-serif] text-gray-800 dark:text-gray-100">Detalhes da Solicitação</DialogTitle>
          </DialogHeader>
          {selectedApproval && (
            <div className="space-y-3">
              <div>
                <label className="text-micro font-medium text-gray-600">Item</label>
                <p className="text-xs text-gray-800 mt-0.5">{selectedApproval.target_name}</p>
              </div>
              <div>
                <label className="text-micro font-medium text-gray-600">Tipo</label>
                <p className="text-xs text-gray-800 mt-0.5">
                  {REQUEST_TYPE_LABELS[selectedApproval.request_type] || selectedApproval.request_type}
                </p>
              </div>
              {selectedApproval.target_description && (
                <div>
                  <label className="text-micro font-medium text-gray-600">Descrição</label>
                  <p className="text-xs text-gray-800 mt-0.5">{selectedApproval.target_description}</p>
                </div>
              )}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-micro font-medium text-gray-600">Solicitante</label>
                  <p className="text-xs text-gray-800 mt-0.5">{selectedApproval.requester_name}</p>
                  <p className="text-xs text-gray-500">{selectedApproval.requester_email}</p>
                </div>
                <div>
                  <label className="text-micro font-medium text-gray-600">Aprovador</label>
                  <p className="text-xs text-gray-800 mt-0.5">{selectedApproval.approver_name}</p>
                  <p className="text-xs text-gray-500">{selectedApproval.approver_email}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-micro font-medium text-gray-600">Status</label>
                  <Badge className={`${STATUS_CONFIG[selectedApproval.status].color} text-micro px-2 py-0.5 mt-0.5`}>
                    {STATUS_CONFIG[selectedApproval.status].label}
                  </Badge>
                </div>
                <div>
                  <label className="text-micro font-medium text-gray-600">Criado em</label>
                  <p className="text-xs text-gray-800 mt-0.5">{formatDate(selectedApproval.created_at)}</p>
                </div>
              </div>
              {selectedApproval.resolved_at && (
                <div>
                  <label className="text-micro font-medium text-gray-600">Resolvido em</label>
                  <p className="text-xs text-gray-800 mt-0.5">{formatDate(selectedApproval.resolved_at)}</p>
                </div>
              )}
              {selectedApproval.approval_notes && (
                <div>
                  <label className="text-micro font-medium text-gray-600">Observações</label>
                  <p className="text-xs text-gray-800 mt-0.5">{selectedApproval.approval_notes}</p>
                </div>
              )}
              {selectedApproval.rejection_reason && (
                <div>
                  <label className="text-micro font-medium text-gray-600">Motivo da Rejeição</label>
                  <p className="text-xs text-status-error mt-0.5">{selectedApproval.rejection_reason}</p>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDetailsOpen(false)} className="text-xs">
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isActionDialogOpen} onOpenChange={setIsActionDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-base-ui font-semibold font-['Open_Sans',sans-serif] text-gray-800 dark:text-gray-100">
              {actionType === 'approve' ? 'Aprovar Solicitação' : 'Rejeitar Solicitação'}
            </DialogTitle>
            <DialogDescription className="text-xs">
              {selectedApproval?.target_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <label className="text-xs font-medium text-gray-600 block mb-1.5">
                {actionType === 'approve' ? 'Observações (opcional)' : 'Motivo da rejeição'}
              </label>
              <Textarea
                value={actionNotes}
                onChange={(e) => setActionNotes(e.target.value)}
                placeholder={
                  actionType === 'approve' 
                    ? 'Adicione observações sobre a aprovação...' 
                    : 'Explique o motivo da rejeição...'
                }
                rows={4}
                className="border-gray-200 text-xs py-1.5 px-2"
              />
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setIsActionDialogOpen(false)}
              disabled={isSubmitting}
              className="text-xs"
            >
              Cancelar
            </Button>
            <Button
              onClick={actionType === 'approve' ? handleApprove : handleReject}
              disabled={isSubmitting}
              className={`text-xs ${
                actionType === 'approve' 
                  ? 'bg-status-success hover:bg-status-success' 
                  : 'bg-status-error hover:bg-status-error'
              }`}
            >
              {isSubmitting ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin mr-1.5" />
              ) : actionType === 'approve' ? (
                <CheckCircle className="w-3.5 h-3.5 mr-1.5" />
              ) : (
                <XCircle className="w-3.5 h-3.5 mr-1.5" />
              )}
              {actionType === 'approve' ? 'Confirmar Aprovação' : 'Confirmar Rejeição'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default ApprovalsHub
