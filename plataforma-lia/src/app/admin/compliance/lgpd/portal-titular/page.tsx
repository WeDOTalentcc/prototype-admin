"use client"

import React, { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { UserCircle, ChevronLeft, Eye, Edit, Trash2, ArrowRightLeft, XCircle, Shield, ExternalLink, Settings, Copy, Check, AlertCircle, Clock, FileSearch, CheckCircle2, Loader2, Mail, MoreHorizontal, Search, RefreshCw, User, Phone, UserCheck, Play, Ban } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { 
  dataSubjectRequestsService,
  DataSubjectRequest,
  DataSubjectRequestStats,
  DataSubjectRequestType,
  DataSubjectRequestStatus 
} from "@/services/admin/data-subject-requests-service"

const dsrRights = [
  { id: 1, right: 'Confirmação de Existência', description: 'Confirmar se dados pessoais estão sendo tratados', status: 'implemented', icon: FileSearch },
  { id: 2, right: 'Acesso aos Dados', description: 'Obter cópia dos dados pessoais tratados', status: 'implemented', icon: Eye },
  { id: 3, right: 'Correção de Dados', description: 'Corrigir dados incompletos ou desatualizados', status: 'implemented', icon: Edit },
  { id: 4, right: 'Anonimização ou Bloqueio', description: 'Anonimizar ou bloquear dados excessivos', status: 'implemented', icon: Shield },
  { id: 5, right: 'Eliminação de Dados', description: 'Solicitar exclusão de dados pessoais', status: 'implemented', icon: Trash2 },
  { id: 6, right: 'Portabilidade', description: 'Transferir dados para outro fornecedor', status: 'implemented', icon: ArrowRightLeft },
  { id: 7, right: 'Revogação de Consentimento', description: 'Revogar consentimento previamente dado', status: 'implemented', icon: XCircle },
]

const REQUEST_TYPE_LABELS: Record<DataSubjectRequestType, { label: string, icon: typeof Eye }> = {
  'access': { label: 'Acesso', icon: Eye },
  'correction': { label: 'Correção', icon: Edit },
  'deletion': { label: 'Exclusão', icon: Trash2 },
  'portability': { label: 'Portabilidade', icon: ArrowRightLeft },
  'objection': { label: 'Objeção', icon: XCircle },
  'restriction': { label: 'Restrição', icon: Shield },
  'explanation': { label: 'Explicação', icon: FileSearch },
}

const STATUS_LABELS: Record<DataSubjectRequestStatus, { label: string, color: string }> = {
  'pending': { label: 'Pendente', color: 'amber' },
  'in_review': { label: 'Em Revisão', color: 'blue' },
  'processing': { label: 'Processando', color: 'blue' },
  'completed': { label: 'Concluído', color: 'emerald' },
  'rejected': { label: 'Rejeitado', color: 'red' },
  'cancelled': { label: 'Cancelado', color: 'gray' },
}

export default function PortalTitularPage() {
  const [portalUrl, setPortalUrl] = useState("https://privacidade.wedotalent.com.br")
  const [copied, setCopied] = useState(false)
  const [loading, setLoading] = useState(true)
  const [requests, setRequests] = useState<DataSubjectRequest[]>([])
  const [stats, setStats] = useState<DataSubjectRequestStats | null>(null)
  const [totalRequests, setTotalRequests] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [typeFilter, setTypeFilter] = useState<string>("all")
  const [selectedRequest, setSelectedRequest] = useState<DataSubjectRequest | null>(null)
  const [detailsModalOpen, setDetailsModalOpen] = useState(false)
  const [actionModalOpen, setActionModalOpen] = useState(false)
  const [actionType, setActionType] = useState<'complete' | 'reject' | null>(null)
  const [actionResponse, setActionResponse] = useState("")
  const [actionReason, setActionReason] = useState("")
  const [actionLoading, setActionLoading] = useState(false)

  const pageSize = 10

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [statsData, requestsData] = await Promise.all([
        dataSubjectRequestsService.getStats(),
        dataSubjectRequestsService.getRequests({
          status: statusFilter !== 'all' ? statusFilter : undefined,
          requestType: typeFilter !== 'all' ? typeFilter : undefined,
          search: searchTerm || undefined,
          limit: pageSize,
          offset: (currentPage - 1) * pageSize,
        })
      ])
      setStats(statsData)
      setRequests(requestsData.requests)
      setTotalRequests(requestsData.total)
    } catch (error) {
    } finally {
      setLoading(false)
    }
  }, [statusFilter, typeFilter, searchTerm, currentPage])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleCopy = () => {
    navigator.clipboard.writeText(portalUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'implemented':
        return (
          <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Implementado
          </Badge>
        )
      case 'in_progress':
        return (
          <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">
            <Loader2 className="w-3 h-3 mr-1" />
            Em Desenvolvimento
          </Badge>
        )
      case 'planned':
        return (
 <Badge className="text-gray-600 dark:text-gray-400 hover:bg-gray-100">
            <Clock className="w-3 h-3 mr-1" />
            Planejado
          </Badge>
        )
      default:
        return <Badge>{status}</Badge>
    }
  }

  const implementedCount = dsrRights.filter(r => r.status === 'implemented').length
  const inProgressCount = dsrRights.filter(r => r.status === 'in_progress').length

  const getTypeLabel = (type: DataSubjectRequestType) => {
    return REQUEST_TYPE_LABELS[type] || { label: type, icon: FileSearch }
  }

  const getRequestStatusBadge = (status: DataSubjectRequestStatus) => {
    const config = STATUS_LABELS[status]
    if (!config) return <Badge>{status}</Badge>

    const colorClasses: Record<string, string> = {
      'amber': 'bg-status-warning/15 text-status-warning hover:bg-status-warning/15',
 'blue': 'text-gray-600 dark:text-gray-400 hover:bg-gray-100',
      'emerald': 'bg-status-success/15 text-status-success hover:bg-status-success/15',
      'red': 'bg-status-error/15 text-status-error hover:bg-status-error/15',
      'gray': 'bg-gray-100 text-gray-800 dark:text-gray-200 hover:bg-gray-100',
    }

    return <Badge className={colorClasses[config.color]}>{config.label}</Badge>
  }

  const getSlaStatusBadge = (request: DataSubjectRequest) => {
    if (request.status === 'completed' || request.status === 'rejected' || request.status === 'cancelled') {
      return null
    }

    const daysUntil = request.daysUntilDeadline ?? 0
    
    if (request.isOverdue || daysUntil < 0) {
      return (
        <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">
          <AlertCircle className="w-3 h-3 mr-1" />
          Atrasado
        </Badge>
      )
    }
    
    if (daysUntil <= 3) {
      return (
        <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">
          <Clock className="w-3 h-3 mr-1" />
          {daysUntil}d restantes
        </Badge>
      )
    }

    return (
      <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">
        <CheckCircle2 className="w-3 h-3 mr-1" />
        {daysUntil}d restantes
      </Badge>
    )
  }

  const handleViewDetails = async (request: DataSubjectRequest) => {
    setSelectedRequest(request)
    setDetailsModalOpen(true)
  }

  const handleVerifyIdentity = async (request: DataSubjectRequest) => {
    try {
      await dataSubjectRequestsService.verifyIdentity(request.id)
      loadData()
    } catch (error) {
    }
  }

  const handleProcess = async (request: DataSubjectRequest) => {
    try {
      await dataSubjectRequestsService.processRequest(request.id)
      loadData()
    } catch (error) {
    }
  }

  const handleOpenActionModal = (request: DataSubjectRequest, type: 'complete' | 'reject') => {
    setSelectedRequest(request)
    setActionType(type)
    setActionResponse("")
    setActionReason("")
    setActionModalOpen(true)
  }

  const handleSubmitAction = async () => {
    if (!selectedRequest || !actionType) return

    setActionLoading(true)
    try {
      if (actionType === 'complete') {
        await dataSubjectRequestsService.completeRequest(selectedRequest.id, {
          response: actionResponse,
        })
      } else {
        await dataSubjectRequestsService.rejectRequest(selectedRequest.id, {
          reason: actionReason,
        })
      }
      setActionModalOpen(false)
      loadData()
    } catch (error) {
    } finally {
      setActionLoading(false)
    }
  }

  const totalPages = Math.ceil(totalRequests / pageSize)

  const accessCount = stats?.byType?.access || 0
  const deletionCount = stats?.byType?.deletion || 0
  const portabilityCount = stats?.byType?.portability || 0
  const correctionCount = (stats?.byType?.correction || 0)

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center gap-2 mb-4">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/admin/compliance/lgpd">
              <ChevronLeft className="w-4 h-4 mr-1" />
              Voltar
            </Link>
          </Button>
        </div>

        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center"
              style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
            >
              <UserCircle className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold"
                style={{ 
                  color: 'var(--eleven-text-primary)',
                  
                }}
              >
                Portal Self-Service (Art. 18)
              </h1>
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Portal para exercício de direitos dos titulares de dados
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadData} disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>
            <Button variant="outline" asChild>
              <Link href="/privacidade" target="_blank">
                <ExternalLink className="w-4 h-4 mr-2" />
                Acessar Portal
              </Link>
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                  <FileSearch className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
                <div>
                  <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                    {loading ? '-' : stats?.totalRequests || 0}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>DSRs Recebidos</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)' }}>
                  <Loader2 className="w-5 h-5 text-status-warning" />
                </div>
                <div>
                  <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                    {loading ? '-' : (stats?.pendingRequests || 0) + (stats?.inProgressRequests || 0)}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Em Andamento</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                  <CheckCircle2 className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                    {loading ? '-' : stats?.completedRequests || 0}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Concluídos</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                  <Clock className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
                <div>
                  <p className="text-2xl font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                    {loading ? '-' : `${stats?.avgResponseTime?.toFixed(1) || 0} dias`}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Tempo Médio</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {stats && stats.overdueRequests > 0 && (
          <Card className="mb-6" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', borderColor: 'rgba(239, 68, 68, 0.5)', backgroundColor: 'rgba(239, 68, 68, 0.08)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-status-error" />
                <div>
                  <p className="text-sm font-medium text-status-error">
                    {stats.overdueRequests} solicitação(ões) com prazo excedido
                  </p>
                  <p className="text-xs text-status-error">
                    Atenda imediatamente para evitar penalidades. Prazo legal: 15 dias (Art. 18, §3º da LGPD).
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                      Solicitações de Direitos (DSRs)
                    </CardTitle>
                    <CardDescription>
                      {totalRequests} solicitações encontradas
                    </CardDescription>
                  </div>
                </div>
                <div className="flex gap-3 mt-4">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input
                      placeholder="Buscar por nome ou email..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos os status</SelectItem>
                      <SelectItem value="pending">Pendente</SelectItem>
                      <SelectItem value="in_review">Em Revisão</SelectItem>
                      <SelectItem value="processing">Processando</SelectItem>
                      <SelectItem value="completed">Concluído</SelectItem>
                      <SelectItem value="rejected">Rejeitado</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={typeFilter} onValueChange={setTypeFilter}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Tipo" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos os tipos</SelectItem>
                      <SelectItem value="access">Acesso</SelectItem>
                      <SelectItem value="correction">Correção</SelectItem>
                      <SelectItem value="deletion">Exclusão</SelectItem>
                      <SelectItem value="portability">Portabilidade</SelectItem>
                      <SelectItem value="explanation">Explicação</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-gray-600 dark:text-gray-400" />
                  </div>
                ) : requests.length === 0 ? (
                  <div className="text-center py-12">
                    <FileSearch className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      Nenhuma solicitação encontrada
                    </p>
                  </div>
                ) : (
                  <>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Tipo</TableHead>
                          <TableHead>Solicitante</TableHead>
                          <TableHead>Data</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>SLA</TableHead>
                          <TableHead className="w-[50px]"></TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {requests.map((request) => {
                          const typeInfo = getTypeLabel(request.requestType)
                          const Icon = typeInfo.icon
                          return (
                            <TableRow key={request.id} className="hover:bg-gray-50">
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <div className="w-8 h-8 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                                    <Icon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                  </div>
                                  <span className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{typeInfo.label}</span>
                                </div>
                              </TableCell>
                              <TableCell>
                                <div>
                                  <p style={{ color: 'var(--eleven-text-primary)' }}>{request.requesterName}</p>
                                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>{request.requesterEmail}</p>
                                </div>
                              </TableCell>
                              <TableCell>
                                <span style={{ color: 'var(--eleven-text-secondary)' }}>
                                  {new Date(request.createdAt).toLocaleDateString('pt-BR')}
                                </span>
                              </TableCell>
                              <TableCell>{getRequestStatusBadge(request.status)}</TableCell>
                              <TableCell>{getSlaStatusBadge(request)}</TableCell>
                              <TableCell>
                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="sm">
                                      <MoreHorizontal className="w-4 h-4" />
                                    </Button>
                                  </DropdownMenuTrigger>
                                  <DropdownMenuContent align="end">
                                    <DropdownMenuItem onClick={() => handleViewDetails(request)}>
                                      <Eye className="w-4 h-4 mr-2" />
                                      Ver detalhes
                                    </DropdownMenuItem>
                                    {request.status === 'pending' && (
                                      <DropdownMenuItem onClick={() => handleVerifyIdentity(request)}>
                                        <UserCheck className="w-4 h-4 mr-2" />
                                        Verificar identidade
                                      </DropdownMenuItem>
                                    )}
                                    {request.status === 'in_review' && (
                                      <DropdownMenuItem onClick={() => handleProcess(request)}>
                                        <Play className="w-4 h-4 mr-2" />
                                        Iniciar processamento
                                      </DropdownMenuItem>
                                    )}
                                    {request.status === 'processing' && (
                                      <>
                                        <DropdownMenuSeparator />
                                        <DropdownMenuItem onClick={() => handleOpenActionModal(request, 'complete')}>
                                          <CheckCircle2 className="w-4 h-4 mr-2" />
                                          Concluir solicitação
                                        </DropdownMenuItem>
                                        <DropdownMenuItem onClick={() => handleOpenActionModal(request, 'reject')}>
                                          <Ban className="w-4 h-4 mr-2" />
                                          Rejeitar solicitação
                                        </DropdownMenuItem>
                                      </>
                                    )}
                                  </DropdownMenuContent>
                                </DropdownMenu>
                              </TableCell>
                            </TableRow>
                          )
                        })}
                      </TableBody>
                    </Table>
                    
                    {totalPages > 1 && (
                      <div className="flex items-center justify-between mt-4 pt-4 border-t">
                        <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          Página {currentPage} de {totalPages}
                        </p>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                          >
                            Anterior
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                            disabled={currentPage === totalPages}
                          >
                            Próximo
                          </Button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>

            <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                      Direitos Suportados
                    </CardTitle>
                    <CardDescription>
                      Status de implementação de cada direito do Art. 18
                    </CardDescription>
                  </div>
                  <div className="flex gap-2 text-xs">
                    <Badge variant="outline" className="bg-status-success/10 border-status-success/30 text-status-success">
                      {implementedCount} Implementados
                    </Badge>
                    {inProgressCount > 0 && (
                      <Badge variant="outline" className="bg-status-warning/10 border-status-warning/30 text-status-warning">
                        {inProgressCount} Em Desenvolvimento
                      </Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {dsrRights.map((direito) => {
                    const Icon = direito.icon
                    return (
                      <div 
                        key={direito.id}
                        className="flex items-center gap-3 p-3 rounded-md hover:bg-gray-50 transition-colors"
                        style={{ backgroundColor: 'var(--eleven-bg-secondary)' }}
                      >
                        <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                          <Icon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                            {direito.right}
                          </p>
                          <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                            {direito.description}
                          </p>
                        </div>
                        {getStatusBadge(direito.status)}
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardHeader>
                <CardTitle className="text-base font-medium flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                  <Settings className="w-4 h-4" />
                  Configuração do Portal
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="portal-url">URL Pública do Portal</Label>
                  <div className="flex gap-2">
                    <Input
                      id="portal-url"
                      value={portalUrl}
                      onChange={(e) => setPortalUrl(e.target.value)}
                      className="flex-1"
                    />
                    <Button variant="outline" size="icon" onClick={handleCopy}>
                      {copied ? <Check className="w-4 h-4 text-status-success" /> : <Copy className="w-4 h-4" />}
                    </Button>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    URL onde o portal será acessível publicamente
                  </p>
                </div>

                <div className="pt-4 border-t" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                  <Button className="w-full" variant="outline" asChild>
                    <Link href="/privacidade" target="_blank">
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Visualizar Portal
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardHeader>
                <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                  Métricas de Desempenho
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-secondary)' }}>
                    <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Taxa de Conclusão</span>
                    <span className="font-semibold text-status-success">
                      {stats && stats.totalRequests > 0 
                        ? `${Math.round((stats.completedRequests / stats.totalRequests) * 100)}%`
                        : '0%'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-secondary)' }}>
                    <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>SLA Compliance</span>
                    <span className={`font-semibold ${(stats?.slaComplianceRate || 0) >= 90 ? 'text-status-success' : (stats?.slaComplianceRate || 0) >= 70 ? 'text-status-warning' : 'text-status-error'}`}>
                      {stats?.slaComplianceRate?.toFixed(0) || 0}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-secondary)' }}>
                    <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Atrasados</span>
                    <span className={`font-semibold ${(stats?.overdueRequests || 0) === 0 ? 'text-status-success' : 'text-status-error'}`}>
                      {stats?.overdueRequests || 0}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
              <CardHeader>
                <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                  Por Tipo de Solicitação
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-secondary)' }}>
                    <div className="flex items-center gap-2">
                      <Eye className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Acesso</span>
                    </div>
                    <Badge variant="outline">{accessCount}</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-secondary)' }}>
                    <div className="flex items-center gap-2">
                      <Edit className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Retificação</span>
                    </div>
                    <Badge variant="outline">{correctionCount}</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-secondary)' }}>
                    <div className="flex items-center gap-2">
                      <Trash2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Exclusão</span>
                    </div>
                    <Badge variant="outline">{deletionCount}</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-secondary)' }}>
                    <div className="flex items-center gap-2">
                      <ArrowRightLeft className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Portabilidade</span>
                    </div>
                    <Badge variant="outline">{portabilityCount}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', borderColor: 'rgba(96, 190, 209, 0.3)', backgroundColor: 'rgba(96, 190, 209, 0.02)' }}>
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-gray-600 dark:text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                      Prazo Legal: 15 Dias
                    </p>
                    <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>
                      As solicitações devem ser atendidas em até 15 dias contados da data do requerimento 
                      do titular, conforme Art. 18, §3º da LGPD.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <Dialog open={detailsModalOpen} onOpenChange={setDetailsModalOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Detalhes da Solicitação</DialogTitle>
            <DialogDescription>
              Informações completas sobre a solicitação de direito
            </DialogDescription>
          </DialogHeader>
          {selectedRequest && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Tipo</Label>
                  <div className="flex items-center gap-2">
                    {(() => {
                      const typeInfo = getTypeLabel(selectedRequest.requestType)
                      const Icon = typeInfo.icon
                      return (
                        <>
                          <Icon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                          <span className="font-medium">{typeInfo.label}</span>
                        </>
                      )
                    })()}
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Status</Label>
                  <div>{getRequestStatusBadge(selectedRequest.status)}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Solicitante</Label>
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-gray-400" />
                    <span>{selectedRequest.requesterName}</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Email</Label>
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-gray-400" />
                    <span>{selectedRequest.requesterEmail}</span>
                  </div>
                </div>
              </div>

              {selectedRequest.requesterCpf && (
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">CPF</Label>
                  <p>{selectedRequest.requesterCpf}</p>
                </div>
              )}

              {selectedRequest.requesterPhone && (
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Telefone</Label>
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-gray-400" />
                    <span>{selectedRequest.requesterPhone}</span>
                  </div>
                </div>
              )}

              {selectedRequest.description && (
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Descrição</Label>
                  <p className="text-sm bg-gray-50 p-3 rounded-md">{selectedRequest.description}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Data da Solicitação</Label>
                  <p>{new Date(selectedRequest.createdAt).toLocaleString('pt-BR')}</p>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Prazo</Label>
                  <p>{new Date(selectedRequest.deadlineAt).toLocaleDateString('pt-BR')}</p>
                </div>
              </div>

              {selectedRequest.identityVerified && (
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Identidade Verificada</Label>
                  <div className="flex items-center gap-2">
                    <UserCheck className="w-4 h-4 text-status-success" />
                    <span className="text-status-success">
                      Verificada em {new Date(selectedRequest.identityVerifiedAt!).toLocaleString('pt-BR')}
                    </span>
                  </div>
                </div>
              )}

              {selectedRequest.response && (
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Resposta</Label>
                  <p className="text-sm bg-status-success/10 p-3 rounded-md border border-status-success/30">
                    {selectedRequest.response}
                  </p>
                </div>
              )}

              {selectedRequest.rejectionReason && (
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Motivo da Rejeição</Label>
                  <p className="text-sm bg-status-error/10 p-3 rounded-md border border-status-error/30">
                    {selectedRequest.rejectionReason}
                  </p>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDetailsModalOpen(false)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={actionModalOpen} onOpenChange={setActionModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {actionType === 'complete' ? 'Concluir Solicitação' : 'Rejeitar Solicitação'}
            </DialogTitle>
            <DialogDescription>
              {actionType === 'complete' 
                ? 'Forneça uma resposta para o titular sobre sua solicitação.'
                : 'Informe o motivo da rejeição da solicitação.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {actionType === 'complete' ? (
              <div className="space-y-2">
                <Label htmlFor="response">Resposta ao Titular</Label>
                <Textarea
                  id="response"
                  value={actionResponse}
                  onChange={(e) => setActionResponse(e.target.value)}
                  placeholder="Descreva as ações tomadas e as informações relevantes para o titular..."
                  rows={5}
                />
              </div>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="reason">Motivo da Rejeição</Label>
                <Textarea
                  id="reason"
                  value={actionReason}
                  onChange={(e) => setActionReason(e.target.value)}
                  placeholder="Explique por que a solicitação está sendo rejeitada..."
                  rows={5}
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setActionModalOpen(false)} disabled={actionLoading}>
              Cancelar
            </Button>
            <Button 
              onClick={handleSubmitAction} 
              disabled={actionLoading || (actionType === 'complete' ? !actionResponse : !actionReason)}
              className={actionType === 'reject' ? 'bg-status-error hover:bg-status-error' : ''}
            >
              {actionLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {actionType === 'complete' ? 'Concluir' : 'Rejeitar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
