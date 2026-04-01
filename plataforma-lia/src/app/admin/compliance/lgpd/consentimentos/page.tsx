"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { 
  CheckSquare, ChevronLeft, Filter, Search, TrendingUp, Clock, XCircle, Plus, FileText, 
  RefreshCw, Download, Ban, History, BarChart3, ListChecks, Eye, AlertCircle, Loader2
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  consentManagementService, 
  ConsentVersion, 
  ConsentEvent, 
  ConsentStats, 
  SubjectHistory,
  ConsentType,
  ApiClientError
} from "@/services/admin/consent-management-service"
import { ConsentVersionsTable } from "./ConsentVersionsTable"

const CONSENT_TYPE_LABELS: Record<string, string> = {
  personal_data: 'Dados Pessoais',
  marketing: 'Comunicações Marketing',
  sensitive_data: 'Dados Sensíveis',
  data_sharing: 'Compartilhamento com Clientes',
  cookies: 'Cookies',
  analytics: 'Analytics',
  third_party: 'Terceiros',
}

const EVENT_TYPE_LABELS: Record<string, string> = {
  granted: 'Concessão',
  revoked: 'Revogação',
  expired: 'Expirado',
  renewed: 'Renovação',
}

export default function ConsentimentosPage() {
  const [activeTab, setActiveTab] = useState("versions")
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("todos")
  const [eventTypeFilter, setEventTypeFilter] = useState("todos")
  const [consentTypeFilter, setConsentTypeFilter] = useState("todos")

  const [versions, setVersions] = useState<ConsentVersion[]>([])
  const [events, setEvents] = useState<ConsentEvent[]>([])
  const [stats, setStats] = useState<ConsentStats | null>(null)
  const [subjectHistory, setSubjectHistory] = useState<SubjectHistory | null>(null)

  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingVersions, setIsLoadingVersions] = useState(false)
  const [isLoadingEvents, setIsLoadingEvents] = useState(false)
  const [isLoadingStats, setIsLoadingStats] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

  const [isCreateVersionModalOpen, setIsCreateVersionModalOpen] = useState(false)
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<ConsentVersion | null>(null)

  const [newVersionForm, setNewVersionForm] = useState({
    consentType: '' as ConsentType | '',
    title: '',
    content: '',
    summary: '',
    validityMonths: 12,
  })

  const [historySearchTerm, setHistorySearchTerm] = useState('')

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (activeTab === 'versions') {
      loadVersions()
    } else if (activeTab === 'events') {
      loadEvents()
    } else if (activeTab === 'stats') {
      loadStats()
    }
  }, [activeTab, consentTypeFilter, eventTypeFilter])

  const loadInitialData = async () => {
    setIsLoading(true)
    try {
      await Promise.all([loadVersions(), loadStats()])
    } finally {
      setIsLoading(false)
    }
  }

  const loadVersions = async () => {
    setIsLoadingVersions(true)
    try {
      const response = await consentManagementService.getVersions({
        consentType: consentTypeFilter !== 'todos' ? consentTypeFilter : undefined,
        limit: 100,
      })
      setVersions(response.versions)
    } catch (error) {
    } finally {
      setIsLoadingVersions(false)
    }
  }

  const loadEvents = async () => {
    setIsLoadingEvents(true)
    try {
      const response = await consentManagementService.getEvents({
        consentType: consentTypeFilter !== 'todos' ? consentTypeFilter : undefined,
        eventType: eventTypeFilter !== 'todos' ? eventTypeFilter : undefined,
        limit: 100,
      })
      setEvents(response.events)
    } catch (error) {
    } finally {
      setIsLoadingEvents(false)
    }
  }

  const loadStats = async () => {
    setIsLoadingStats(true)
    try {
      const data = await consentManagementService.getStats()
      setStats(data)
    } catch (error) {
    } finally {
      setIsLoadingStats(false)
    }
  }

  const loadSubjectHistory = async (subjectIdentifier: string) => {
    setIsLoadingHistory(true)
    try {
      const data = await consentManagementService.getSubjectHistory(subjectIdentifier)
      setSubjectHistory(data)
      setIsHistoryModalOpen(true)
    } catch (error) {
    } finally {
      setIsLoadingHistory(false)
    }
  }

  const handleCreateVersion = async () => {
    if (!newVersionForm.consentType || !newVersionForm.title || !newVersionForm.content) {
      return
    }

    try {
      await consentManagementService.createVersion({
        consentType: newVersionForm.consentType as ConsentType,
        title: newVersionForm.title,
        content: newVersionForm.content,
        summary: newVersionForm.summary || undefined,
        validityMonths: newVersionForm.validityMonths,
      })
      setIsCreateVersionModalOpen(false)
      setNewVersionForm({ consentType: '', title: '', content: '', summary: '', validityMonths: 12 })
      loadVersions()
      loadStats()
    } catch (error) {
    }
  }

  const handleRevokeConsent = async (event: ConsentEvent) => {
    if (!confirm(`Confirma a revogação do consentimento de ${event.subjectName || event.subjectEmail || event.subjectIdentifier}?`)) {
      return
    }

    try {
      await consentManagementService.revokeConsent({
        subjectIdentifier: event.subjectIdentifier,
        consentType: event.consentType,
        reason: 'Revogação administrativa',
      })
      loadEvents()
      loadStats()
    } catch (error) {
    }
  }

  const getEventStatusBadge = (eventType: string) => {
    switch (eventType) {
      case 'granted':
        return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Concedido</Badge>
      case 'revoked':
        return <Badge className="bg-wedo-purple/15 text-wedo-purple hover:bg-wedo-purple/15">Revogado</Badge>
      case 'expired':
        return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">Expirado</Badge>
      case 'renewed':
 return <Badge className="lia-text-900 dark:lia-text-50 hover:bg-gray-100">Renovado</Badge>
      default:
        return <Badge>{eventType}</Badge>
    }
  }

  const filteredVersions = versions.filter(v => {
    const matchesSearch = v.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (CONSENT_TYPE_LABELS[v.consentType] || v.consentType).toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  const filteredEvents = events.filter(e => {
    const matchesSearch = 
      (e.subjectName || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (e.subjectEmail || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.subjectIdentifier.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesSearch
  })

  const totalActive = stats?.activeConsents || 0
  const totalPending = stats?.pendingRenewal || 0
  const totalExpired = stats?.expired || 0
  const totalRevoked = stats?.revoked || 0
  const taxaConsentimento = stats?.consentRate || 0

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
              className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30"
            >
              <CheckSquare className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold lia-text-800 dark:text-lia-text-primary"
                
              >
                Gestão de Consentimentos
              </h1>
              <p className="text-sm lia-text-400 dark:lia-text-500" >
                Ciclo de vida de consentimentos de titulares
              </p>
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => { loadVersions(); loadEvents(); loadStats(); }}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Atualizar
            </Button>
            <Button onClick={() => setIsCreateVersionModalOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Nova Versão de Termo
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30">
                  <TrendingUp className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                </div>
                <div>
                  <p className="text-2xl font-semibold lia-text-800 dark:text-lia-text-primary" >
                    {isLoading ? '...' : `${Math.round(taxaConsentimento)}%`}
                  </p>
                  <p className="text-xs lia-text-400 dark:lia-text-500" >Taxa de Consentimento</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-green-500/10">
                  <CheckSquare className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-2xl font-semibold lia-text-800 dark:text-lia-text-primary" >
                    {isLoading ? '...' : totalActive.toLocaleString('pt-BR')}
                  </p>
                  <p className="text-xs lia-text-400 dark:lia-text-500" >Consentimentos Ativos</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-amber-500/10">
                  <RefreshCw className="w-5 h-5 text-status-warning" />
                </div>
                <div>
                  <p className="text-2xl font-semibold lia-text-800 dark:text-lia-text-primary" >
                    {isLoading ? '...' : totalPending}
                  </p>
                  <p className="text-xs lia-text-400 dark:lia-text-500" >Pendentes de Renovação</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-red-500/10">
                  <XCircle className="w-5 h-5 text-status-error" />
                </div>
                <div>
                  <p className="text-2xl font-semibold lia-text-800 dark:text-lia-text-primary" >
                    {isLoading ? '...' : totalExpired}
                  </p>
                  <p className="text-xs lia-text-400 dark:lia-text-500" >Expirados</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-wedo-purple/10">
                  <Ban className="w-5 h-5 text-wedo-purple" />
                </div>
                <div>
                  <p className="text-2xl font-semibold lia-text-800 dark:text-lia-text-primary" >
                    {isLoading ? '...' : totalRevoked}
                  </p>
                  <p className="text-xs lia-text-400 dark:lia-text-500" >Revogados</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="versions" className="flex items-center gap-2">
              <ListChecks className="w-4 h-4" />
              Versões de Termos
            </TabsTrigger>
            <TabsTrigger value="events" className="flex items-center gap-2">
              <History className="w-4 h-4" />
              Eventos
            </TabsTrigger>
            <TabsTrigger value="stats" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Estatísticas
            </TabsTrigger>
          </TabsList>

          <TabsContent value="versions">
            <Card >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary" >
                    Versões de Termos de Consentimento
                  </CardTitle>
                  <div className="flex items-center gap-3">
                    <div className="relative w-64">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 lia-text-400 dark:lia-text-500"  />
                      <Input
                        placeholder="Buscar termo..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-9"
                      />
                    </div>
                    <Select value={consentTypeFilter} onValueChange={setConsentTypeFilter}>
                      <SelectTrigger className="w-48">
                        <Filter className="w-4 h-4 mr-2" />
                        <SelectValue placeholder="Tipo" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="todos">Todos os Tipos</SelectItem>
                        {Object.entries(CONSENT_TYPE_LABELS).map(([key, label]) => (
                          <SelectItem key={key} value={key}>{label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {isLoadingVersions ? (
                  <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
                    <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none lia-text-600 dark:text-lia-text-tertiary" />
                    <span className="ml-2 lia-text-500 dark:text-lia-text-tertiary" >Carregando...</span>
                  </div>
                ) : filteredVersions.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12">
                    <AlertCircle className="w-12 h-12 lia-text-300 mb-4" />
                    <p className="lia-text-500 dark:text-lia-text-tertiary" >Nenhuma versão de termo encontrada</p>
                    <Button variant="outline" className="mt-4" onClick={() => setIsCreateVersionModalOpen(true)}>
                      <Plus className="w-4 h-4 mr-2" />
                      Criar Primeira Versão
                    </Button>
                  </div>
                ) : (
                  <ConsentVersionsTable
                    versions={filteredVersions}
                    onNewVersion={(version) => {
                      setSelectedVersion(version)
                      setNewVersionForm({
                        consentType: version.consentType,
                        title: version.title,
                        content: version.content,
                        summary: version.summary || '',
                        validityMonths: version.validityMonths,
                      })
                      setIsCreateVersionModalOpen(true)
                    }}
                  />
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="events">
            <Card >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div>
                    <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary" >
                      Eventos de Consentimento
                    </CardTitle>
                    <CardDescription>Registro de concessões, revogações e expirações</CardDescription>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="relative w-64">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 lia-text-400 dark:lia-text-500"  />
                      <Input
                        placeholder="Buscar titular..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-9"
                      />
                    </div>
                    <Select value={eventTypeFilter} onValueChange={setEventTypeFilter}>
                      <SelectTrigger className="w-40">
                        <SelectValue placeholder="Evento" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="todos">Todos Eventos</SelectItem>
                        <SelectItem value="granted">Concessão</SelectItem>
                        <SelectItem value="revoked">Revogação</SelectItem>
                        <SelectItem value="expired">Expirado</SelectItem>
                        <SelectItem value="renewed">Renovação</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={consentTypeFilter} onValueChange={setConsentTypeFilter}>
                      <SelectTrigger className="w-48">
                        <SelectValue placeholder="Tipo" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="todos">Todos os Tipos</SelectItem>
                        {Object.entries(CONSENT_TYPE_LABELS).map(([key, label]) => (
                          <SelectItem key={key} value={key}>{label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {isLoadingEvents ? (
                  <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
                    <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none lia-text-600 dark:text-lia-text-tertiary" />
                    <span className="ml-2 lia-text-500 dark:text-lia-text-tertiary" >Carregando...</span>
                  </div>
                ) : filteredEvents.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12">
                    <AlertCircle className="w-12 h-12 lia-text-300 mb-4" />
                    <p className="lia-text-500 dark:text-lia-text-tertiary"  aria-live="polite" aria-atomic="true">Nenhum evento de consentimento encontrado</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Titular</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Tipo de Consentimento</TableHead>
                        <TableHead>Versão</TableHead>
                        <TableHead>Evento</TableHead>
                        <TableHead>Data</TableHead>
                        <TableHead>IP/Dispositivo</TableHead>
                        <TableHead className="text-right">Ações</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredEvents.map((event) => (
                        <TableRow key={event.id} className="hover:bg-gray-50">
                          <TableCell>
                            <span className="font-medium lia-text-800 dark:text-lia-text-primary" >
                              {event.subjectName || event.subjectIdentifier}
                            </span>
                          </TableCell>
                          <TableCell>
                            <span className="lia-text-500 dark:text-lia-text-tertiary" >
                              {event.subjectEmail || '-'}
                            </span>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="text-xs">
                              {CONSENT_TYPE_LABELS[event.consentType] || event.consentType}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-center">
                            <Badge variant="secondary" className="text-xs">v{event.version}</Badge>
                          </TableCell>
                          <TableCell>{getEventStatusBadge(event.eventType)}</TableCell>
                          <TableCell>
                            <span className="lia-text-500 dark:text-lia-text-tertiary" >
                              {new Date(event.createdAt).toLocaleDateString('pt-BR', {
                                day: '2-digit',
                                month: '2-digit',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </span>
                          </TableCell>
                          <TableCell>
                            <div className="text-xs lia-text-400 dark:lia-text-500" >
                              <div>{event.ipAddress || '-'}</div>
                              <div className="truncate max-w-32">{event.userAgent || '-'}</div>
                            </div>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => loadSubjectHistory(event.subjectIdentifier)}
                                disabled={isLoadingHistory}
                              >
                                <Eye className="w-3 h-3 mr-1" />
                                Histórico
                              </Button>
                              {event.eventType === 'granted' && (
                                <Button 
                                  variant="ghost" 
                                  size="sm" 
                                  className="text-status-error hover:text-status-error hover:bg-status-error/10"
                                  onClick={() => handleRevokeConsent(event)}
                                >
                                  <Ban className="w-3 h-3 mr-1" />
                                  Revogar
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="stats">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card >
                <CardHeader>
                  <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary" >
                    Taxa de Consentimento por Tipo
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {isLoadingStats ? (
                    <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
                      <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none lia-text-600 dark:text-lia-text-tertiary" />
                    </div>
                  ) : stats && Object.keys(stats.byType).length > 0 ? (
                    <div className="space-y-4">
                      {Object.entries(stats.byType).map(([type, data]) => (
                        <div key={type} className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium lia-text-800 dark:text-lia-text-primary" >
                              {CONSENT_TYPE_LABELS[type] || type}
                            </span>
                            <span className="text-sm font-semibold lia-text-800 dark:text-lia-text-primary" >
                              {Math.round(data.rate)}%
                            </span>
                          </div>
                          <Progress value={data.rate} className="h-2" />
                          <div className="flex items-center justify-between text-xs lia-text-400 dark:lia-text-500" >
                            <span>{data.active} ativos</span>
                            <span>{data.pending} pendentes</span>
                            <span>{data.revoked} revogados</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-8">
                      <AlertCircle className="w-10 h-10 lia-text-300 mb-3" />
                      <p className="text-sm lia-text-500 dark:text-lia-text-tertiary" >
                        Nenhuma estatística disponível
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card >
                <CardHeader>
                  <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary" >
                    Atividade Recente
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {isLoadingStats ? (
                    <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
                      <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none lia-text-600 dark:text-lia-text-tertiary" />
                    </div>
                  ) : stats ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-3 rounded-md bg-status-success/10">
                        <div className="flex items-center gap-3">
                          <CheckSquare className="w-5 h-5 text-status-success" />
                          <span className="text-sm lia-text-800 dark:text-lia-text-primary" >
                            Consentimentos Hoje
                          </span>
                        </div>
                        <span className="text-lg font-semibold text-status-success">
                          {stats.recentActivity.grantsToday}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-md bg-wedo-purple/10">
                        <div className="flex items-center gap-3">
                          <Ban className="w-5 h-5 text-wedo-purple" />
                          <span className="text-sm lia-text-800 dark:text-lia-text-primary" >
                            Revogações Hoje
                          </span>
                        </div>
                        <span className="text-lg font-semibold text-wedo-purple">
                          {stats.recentActivity.revokesToday}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-md bg-status-warning/10">
                        <div className="flex items-center gap-3">
                          <Clock className="w-5 h-5 text-status-warning" />
                          <span className="text-sm lia-text-800 dark:text-lia-text-primary" >
                            Expirando Esta Semana
                          </span>
                        </div>
                        <span className="text-lg font-semibold text-status-warning">
                          {stats.recentActivity.expiringThisWeek}
                        </span>
                      </div>
                    </div>
                  ) : null}
                </CardContent>
              </Card>

              <Card className="md:col-span-2" >
                <CardHeader>
                  <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary" >
                    Resumo Geral
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 rounded-md bg-gray-50">
                      <p className="text-3xl font-bold lia-text-800 dark:text-lia-text-primary" >
                        {stats?.totalVersions || 0}
                      </p>
                      <p className="text-sm lia-text-400 dark:lia-text-500" >
                        Versões de Termos
                      </p>
                    </div>
                    <div className="text-center p-4 rounded-md bg-gray-50">
                      <p className="text-3xl font-bold lia-text-800 dark:text-lia-text-primary" >
                        {stats?.totalConsents || 0}
                      </p>
                      <p className="text-sm lia-text-400 dark:lia-text-500" >
                        Total de Consentimentos
                      </p>
                    </div>
                    <div className="text-center p-4 rounded-md bg-gray-50">
                      <p className="text-3xl font-bold text-status-success">
                        {stats?.activeVersions || 0}
                      </p>
                      <p className="text-sm lia-text-400 dark:lia-text-500" >
                        Versões Ativas
                      </p>
                    </div>
                    <div className="text-center p-4 rounded-md bg-gray-50">
                      <p className="text-3xl font-bold lia-text-900 dark:lia-text-50">
                        {Math.round(stats?.consentRate || 0)}%
                      </p>
                      <p className="text-sm lia-text-400 dark:lia-text-500" >
                        Taxa de Aceite
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        <Dialog open={isCreateVersionModalOpen} onOpenChange={(open) => {
          if (!open) {
            setIsCreateVersionModalOpen(false)
            setSelectedVersion(null)
            setNewVersionForm({ consentType: '', title: '', content: '', summary: '', validityMonths: 12 })
          }
        }}>
          <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {selectedVersion ? 'Criar Nova Versão do Termo' : 'Criar Novo Tipo de Consentimento'}
              </DialogTitle>
              <DialogDescription>
                {selectedVersion 
                  ? `Criar nova versão do termo "${CONSENT_TYPE_LABELS[selectedVersion.consentType] || selectedVersion.consentType}"`
                  : 'Defina um novo tipo de consentimento para coleta de dados.'
                }
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              {selectedVersion && (
                <div className="p-3 rounded-md bg-status-warning/10 border border-status-warning/30">
                  <p className="text-xs text-status-warning">
                    <strong>Atenção:</strong> Ao criar uma nova versão, todos os titulares com consentimento ativo 
                    serão notificados para aceitar o novo termo.
                  </p>
                </div>
              )}
              
              {!selectedVersion && (
                <div className="grid gap-2">
                  <Label htmlFor="consent-type">Tipo de Consentimento</Label>
                  <Select 
                    value={newVersionForm.consentType} 
                    onValueChange={(v) => setNewVersionForm(prev => ({ ...prev, consentType: v as ConsentType }))}
                  >
                    <SelectTrigger id="consent-type">
                      <SelectValue placeholder="Selecione o tipo" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(CONSENT_TYPE_LABELS).map(([key, label]) => (
                        <SelectItem key={key} value={key}>{label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              
              <div className="grid gap-2">
                <Label htmlFor="title">Título do Termo</Label>
                <Input 
                  id="title" 
                  placeholder="Ex: Termo de Consentimento para Coleta de Dados Pessoais"
                  value={newVersionForm.title}
                  onChange={(e) => setNewVersionForm(prev => ({ ...prev, title: e.target.value }))}
                />
              </div>
              
              <div className="grid gap-2">
                <Label htmlFor="summary">Resumo (opcional)</Label>
                <Input 
                  id="summary" 
                  placeholder="Breve descrição do propósito deste termo"
                  value={newVersionForm.summary}
                  onChange={(e) => setNewVersionForm(prev => ({ ...prev, summary: e.target.value }))}
                />
              </div>
              
              <div className="grid gap-2">
                <Label htmlFor="content">Conteúdo do Termo (HTML)</Label>
                <Textarea 
                  id="content" 
                  placeholder="<p>Digite aqui o conteúdo completo do termo de consentimento...</p>"
                  value={newVersionForm.content}
                  onChange={(e) => setNewVersionForm(prev => ({ ...prev, content: e.target.value }))}
                  className="min-h-chart-sm font-mono text-sm"
                />
              </div>
              
              <div className="grid gap-2">
                <Label htmlFor="validity">Validade (meses)</Label>
                <Input 
                  id="validity" 
                  type="number" 
                  value={newVersionForm.validityMonths}
                  onChange={(e) => setNewVersionForm(prev => ({ ...prev, validityMonths: parseInt(e.target.value) || 12 }))}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => {
                setIsCreateVersionModalOpen(false)
                setSelectedVersion(null)
                setNewVersionForm({ consentType: '', title: '', content: '', summary: '', validityMonths: 12 })
              }}>
                Cancelar
              </Button>
              <Button 
                type="submit" 
                onClick={handleCreateVersion}
                disabled={!newVersionForm.title || !newVersionForm.content || (!selectedVersion && !newVersionForm.consentType)}
              >
                {selectedVersion ? 'Publicar Nova Versão' : 'Criar Tipo'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={isHistoryModalOpen} onOpenChange={setIsHistoryModalOpen}>
          <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Histórico do Titular</DialogTitle>
              <DialogDescription>
                {subjectHistory && (
                  <span>
                    {subjectHistory.subjectName || subjectHistory.subjectEmail || subjectHistory.subjectIdentifier}
                  </span>
                )}
              </DialogDescription>
            </DialogHeader>
            {subjectHistory ? (
              <div className="space-y-4">
                {subjectHistory.currentConsents.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-2 lia-text-800 dark:text-lia-text-primary" >
                      Consentimentos Atuais
                    </h4>
                    <div className="space-y-2">
                      {subjectHistory.currentConsents.map((consent, index) => (
                        <div key={`${consent.consentType}-${index}`} className="flex items-center justify-between p-3 rounded-md bg-gray-50">
                          <div>
                            <span className="font-medium lia-text-800 dark:text-lia-text-primary" >
                              {CONSENT_TYPE_LABELS[consent.consentType] || consent.consentType}
                            </span>
                            <span className="text-xs ml-2 lia-text-400 dark:lia-text-500" >
                              v{consent.version}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className={
                              consent.status === 'active' 
                                ? 'bg-status-success/15 text-status-success' 
                                : consent.status === 'revoked'
                                ? 'bg-wedo-purple/15 text-wedo-purple'
                                : 'bg-status-error/15 text-status-error'
                            }>
                              {consent.status === 'active' ? 'Ativo' : consent.status === 'revoked' ? 'Revogado' : 'Expirado'}
                            </Badge>
                            <span className="text-xs lia-text-400 dark:lia-text-500" >
                              até {new Date(consent.expiresAt).toLocaleDateString('pt-BR')}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div>
                  <h4 className="text-sm font-medium mb-2 lia-text-800 dark:text-lia-text-primary" >
                    Histórico de Eventos
                  </h4>
                  <div className="space-y-2">
                    {subjectHistory.events.map((event) => (
                      <div key={event.id} className="flex items-center justify-between p-3 rounded-md border">
                        <div className="flex items-center gap-3">
                          {getEventStatusBadge(event.eventType)}
                          <div>
                            <span className="text-sm lia-text-800 dark:text-lia-text-primary" >
                              {CONSENT_TYPE_LABELS[event.consentType] || event.consentType}
                            </span>
                            <span className="text-xs ml-2 lia-text-400 dark:lia-text-500" >
                              v{event.version}
                            </span>
                          </div>
                        </div>
                        <span className="text-xs lia-text-400 dark:lia-text-500" >
                          {new Date(event.createdAt).toLocaleDateString('pt-BR', {
                            day: '2-digit',
                            month: '2-digit',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none lia-text-600 dark:text-lia-text-tertiary" />
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsHistoryModalOpen(false)}>
                Fechar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
