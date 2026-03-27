"use client"

import React, { useState, useMemo, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { DateRangePicker } from "@/components/ui/date-range-picker"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import {
  ScrollText,
  Filter,
  Download,
  Shield,
  ArrowLeft,
  Search,
  RefreshCw,
  LogIn,
  Eye,
  Settings,
  Brain,
  ChevronLeft,
  ChevronRight,
  Clock,
  User,
  Building2,
  Globe,
  Calendar,
  Database,
  X,
  AlertTriangle,
  Loader2,
  DollarSign,
  Users,
  Cog,
} from "lucide-react"
import { useAuditLogs, AuditLog, RetentionPolicy } from "@/hooks/admin/useAuditLogs"

type ActionCategoryUI = 'authentication' | 'data_access' | 'configuration' | 'ai_decision' | 'financial' | 'user_management' | 'system'

interface DateRange {
  start_date: string
  end_date: string
}

const CATEGORY_CONFIG: Record<ActionCategoryUI, { label: string; icon: React.ElementType; color: string }> = {
  authentication: {
    label: 'Autenticação',
    icon: LogIn,
    color: 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400',
  },
  data_access: {
    label: 'Acesso a Dados',
    icon: Eye,
    color: 'bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success',
  },
  configuration: {
    label: 'Configurações',
    icon: Settings,
    color: 'bg-status-warning/10 text-status-warning dark:bg-status-warning/20 dark:text-status-warning',
  },
  ai_decision: {
    label: 'Decisões IA',
    icon: Brain,
    color: 'bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple',
  },
  financial: {
    label: 'Financeiro',
    icon: DollarSign,
    color: 'bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success',
  },
  user_management: {
    label: 'Gestão de Usuários',
    icon: Users,
    color: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-400',
  },
  system: {
    label: 'Sistema',
    icon: Cog,
    color: 'bg-gray-50 text-gray-800 dark:bg-gray-900/20 dark:text-gray-200',
  },
}

const ACTION_LABELS: Record<string, string> = {
  login: 'Login',
  logout: 'Logout',
  login_failed: 'Login Falhou',
  'user.login': 'Login',
  'user.logout': 'Logout',
  'user.login_failed': 'Login Falhou',
  view_candidate: 'Visualizou Candidato',
  export_candidates: 'Exportou Candidatos',
  download_cv: 'Download CV',
  export_report: 'Exportou Relatório',
  update_policy: 'Atualizou Política',
  update_settings: 'Atualizou Configurações',
  ai_screening: 'Triagem IA',
  ai_ranking: 'Ranking IA',
}

const ITEMS_PER_PAGE = 10

export default function AuditLogsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<ActionCategoryUI | 'all'>('all')
  const [selectedClient, setSelectedClient] = useState<string>('all')
  const [dateRange, setDateRange] = useState<DateRange>({ start_date: '', end_date: '' })
  const [currentPage, setCurrentPage] = useState(1)
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([
    { id: 'all', name: 'Todos os Clientes' },
  ])

  const {
    logs,
    stats,
    retentionPolicies,
    totalLogs,
    isLoading,
    isExporting,
    refetch,
    fetchLogs,
    exportLogs,
    seedRetentionPolicies,
  } = useAuditLogs()

  useEffect(() => {
    if (stats && stats.uniqueClients > 0) {
      const uniqueClients = logs.reduce((acc, log) => {
        if (log.clientId && log.clientName && !acc.find(c => c.id === log.clientId)) {
          acc.push({ id: log.clientId, name: log.clientName })
        }
        return acc
      }, [] as Array<{ id: string; name: string }>)
      
      setClients([{ id: 'all', name: 'Todos os Clientes' }, ...uniqueClients])
    }
  }, [logs, stats])

  const handleFilterChange = useCallback(() => {
    const filters = {
      dateFrom: dateRange.start_date || undefined,
      dateTo: dateRange.end_date ? `${dateRange.end_date}T23:59:59Z` : undefined,
      clientId: selectedClient !== 'all' ? selectedClient : undefined,
      actionCategory: selectedCategory !== 'all' ? selectedCategory : undefined,
      search: searchQuery || undefined,
    }
    fetchLogs(filters, currentPage, ITEMS_PER_PAGE)
  }, [dateRange, selectedClient, selectedCategory, searchQuery, currentPage, fetchLogs])

  useEffect(() => {
    handleFilterChange()
  }, [currentPage])

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      const matchesSearch = !searchQuery ||
        (log.userEmail?.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (log.action?.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (log.resourceType?.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (log.clientName?.toLowerCase().includes(searchQuery.toLowerCase()))

      const matchesCategory = selectedCategory === 'all' || log.actionCategory === selectedCategory

      const matchesClient = selectedClient === 'all' || log.clientId === selectedClient

      const matchesDateRange = !dateRange.start_date || !dateRange.end_date || (
        log.timestamp && 
        new Date(log.timestamp) >= new Date(dateRange.start_date) &&
        new Date(log.timestamp) <= new Date(dateRange.end_date + 'T23:59:59Z')
      )

      return matchesSearch && matchesCategory && matchesClient && matchesDateRange
    })
  }, [logs, searchQuery, selectedCategory, selectedClient, dateRange])

  const paginatedLogs = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
    return filteredLogs.slice(startIndex, startIndex + ITEMS_PER_PAGE)
  }, [filteredLogs, currentPage])

  const totalPages = Math.ceil(totalLogs / ITEMS_PER_PAGE) || Math.ceil(filteredLogs.length / ITEMS_PER_PAGE)

  const categoryStats = useMemo(() => {
    if (stats?.logsByCategory) {
      return {
        authentication: stats.logsByCategory.authentication || 0,
        data_access: stats.logsByCategory.data_access || 0,
        configuration: stats.logsByCategory.configuration || 0,
        ai_decision: stats.logsByCategory.ai_decision || 0,
        financial: stats.logsByCategory.financial || 0,
        user_management: stats.logsByCategory.user_management || 0,
        system: stats.logsByCategory.system || 0,
      }
    }
    return {
      authentication: logs.filter(l => l.actionCategory === 'authentication').length,
      data_access: logs.filter(l => l.actionCategory === 'data_access').length,
      configuration: logs.filter(l => l.actionCategory === 'configuration').length,
      ai_decision: logs.filter(l => l.actionCategory === 'ai_decision').length,
      financial: logs.filter(l => l.actionCategory === 'financial').length,
      user_management: logs.filter(l => l.actionCategory === 'user_management').length,
      system: logs.filter(l => l.actionCategory === 'system').length,
    }
  }, [stats, logs])

  const failedActions = useMemo(() => {
    if (stats?.failedActionsCount !== undefined) {
      return stats.failedActionsCount
    }
    return logs.filter(l => l.status === 'failed').length
  }, [stats, logs])

  const formatDateTime = (timestamp: string | null) => {
    if (!timestamp) return '-'
    return new Date(timestamp).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const handleExportCSV = async () => {
    try {
      const filters = {
        dateFrom: dateRange.start_date || undefined,
        dateTo: dateRange.end_date || undefined,
        clientId: selectedClient !== 'all' ? selectedClient : undefined,
        actionCategory: selectedCategory !== 'all' ? selectedCategory : undefined,
      }
      await exportLogs(filters)
      toast.success(`Logs de auditoria exportados com sucesso`)
    } catch {
      toast.error('Erro ao exportar logs')
    }
  }

  const handleRefresh = async () => {
    toast.info('Atualizando logs...')
    await refetch()
    toast.success('Logs atualizados')
  }

  const handleSeedPolicies = async () => {
    const result = await seedRetentionPolicies()
    if (result.success) {
      toast.success(result.message)
    } else {
      toast.error(result.message)
    }
  }

  const clearFilters = () => {
    setSearchQuery('')
    setSelectedCategory('all')
    setSelectedClient('all')
    setDateRange({ start_date: '', end_date: '' })
    setCurrentPage(1)
    refetch()
  }

  const hasActiveFilters = searchQuery || selectedCategory !== 'all' || selectedClient !== 'all' || dateRange.start_date

  const getPolicyByCategory = (category: string): RetentionPolicy | undefined => {
    return retentionPolicies.find(p => p.category === category)
  }

  const formatNextPurgeDate = (retentionMonths: number): string => {
    const date = new Date()
    date.setMonth(date.getMonth() + retentionMonths)
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
  }

  const mainCategories: ActionCategoryUI[] = ['authentication', 'data_access', 'configuration', 'ai_decision']

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => window.history.back()}
              className="text-gray-600"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Voltar
            </Button>
            <div>
              <div className="flex items-center gap-2">
                <ScrollText className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                <h1 className="text-2xl font-semibold text-gray-950 dark:text-gray-50">
                  Auditoria & Logs
                </h1>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Logs consolidados de auditoria para conformidade SOX/ISO
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={isLoading}
              className="gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>
            <Button
              onClick={handleExportCSV}
              disabled={isExporting || filteredLogs.length === 0}
              className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
            >
              <Download className="w-4 h-4" />
              {isExporting ? 'Exportando...' : 'Exportar CSV'}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {mainCategories.map((key) => {
            const config = CATEGORY_CONFIG[key]
            const Icon = config.icon
            const count = categoryStats[key]
            return (
              <Card
                key={key}
                className={`cursor-pointer transition-all hover:${
                  selectedCategory === key ? 'ring-2 ring-gray-900/20' : ''
                }`}
                onClick={() => {
                  setSelectedCategory(selectedCategory === key ? 'all' : key)
                  setCurrentPage(1)
                }}
              >
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-md ${config.color}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                        {config.label}
                      </p>
                      <p className="text-2xl font-semibold text-gray-950 dark:text-gray-50">
                        {count}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        <Card className="mb-6">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <Filter className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                Filtros
              </CardTitle>
              {hasActiveFilters && (
                <Button variant="ghost" size="sm" onClick={clearFilters} className="text-gray-500 gap-1">
                  <X className="w-4 h-4" />
                  Limpar
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Buscar por usuário, ação, recurso..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value)
                    setCurrentPage(1)
                  }}
                  className="pl-10"
                />
              </div>
              <DateRangePicker
                value={dateRange}
                onChange={(range) => {
                  setDateRange(range)
                  setCurrentPage(1)
                }}
                placeholder="Período"
              />
              <Select
                value={selectedClient}
                onValueChange={(value) => {
                  setSelectedClient(value)
                  setCurrentPage(1)
                }}
              >
                <SelectTrigger className="w-[200px]">
                  <Building2 className="w-4 h-4 mr-2 text-gray-400" />
                  <SelectValue placeholder="Cliente" />
                </SelectTrigger>
                <SelectContent>
                  {clients.map((client) => (
                    <SelectItem key={client.id} value={client.id}>
                      {client.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={selectedCategory}
                onValueChange={(value) => {
                  setSelectedCategory(value as ActionCategoryUI | 'all')
                  setCurrentPage(1)
                }}
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Categoria" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas as Categorias</SelectItem>
                  {Object.entries(CATEGORY_CONFIG).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium">
                Registros de Auditoria
              </CardTitle>
              <Badge variant="secondary">
                {totalLogs || filteredLogs.length} {(totalLogs || filteredLogs.length) === 1 ? 'registro' : 'registros'}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="py-12 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-gray-600 dark:text-gray-400" />
              </div>
            ) : paginatedLogs.length === 0 ? (
              <div className="py-12 text-center">
                <ScrollText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-950 dark:text-gray-50 mb-2">
                  Nenhum registro encontrado
                </h3>
                <p className="text-gray-500">
                  Tente ajustar os filtros de busca
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                      <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Timestamp
                        </div>
                      </th>
                      <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                        <div className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          Usuário
                        </div>
                      </th>
                      <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                        <div className="flex items-center gap-1">
                          <Building2 className="w-3 h-3" />
                          Cliente
                        </div>
                      </th>
                      <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                        Ação
                      </th>
                      <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                        Recurso
                      </th>
                      <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                        <div className="flex items-center gap-1">
                          <Globe className="w-3 h-3" />
                          IP
                        </div>
                      </th>
                      <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {paginatedLogs.map((log) => {
                      const categoryConfig = CATEGORY_CONFIG[log.actionCategory as ActionCategoryUI] || CATEGORY_CONFIG.system
                      const CategoryIcon = categoryConfig.icon

                      return (
                        <tr
                          key={log.id}
                          className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                        >
                          <td className="px-6 py-4">
                            <span className="text-sm text-gray-950 dark:text-gray-50">
                              {formatDateTime(log.timestamp)}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div>
                              <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                                {log.userId || '-'}
                              </p>
                              <p className="text-xs text-gray-500">{log.userEmail || '-'}</p>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-sm text-gray-800 dark:text-gray-200">
                              {log.clientName || '-'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <div className={`p-1 rounded ${categoryConfig.color}`}>
                                <CategoryIcon className="w-3 h-3" />
                              </div>
                              <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                                {ACTION_LABELS[log.action] || log.action}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div>
                              <p className="text-sm text-gray-800 dark:text-gray-200">
                                {log.resourceType || '-'}
                              </p>
                              {log.details && Object.keys(log.details).length > 0 && (
                                <p className="text-xs text-gray-500 mt-1 max-w-xs truncate">
                                  {JSON.stringify(log.details)}
                                </p>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-sm font-mono text-gray-600 dark:text-gray-400">
                              {log.ipAddress || '-'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            {log.status === 'success' ? (
                              <Badge variant="success">Sucesso</Badge>
                            ) : log.status === 'failed' ? (
                              <Badge variant="destructive">Falhou</Badge>
                            ) : (
                              <Badge variant="secondary">{log.status}</Badge>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500">
                  Mostrando {((currentPage - 1) * ITEMS_PER_PAGE) + 1} a {Math.min(currentPage * ITEMS_PER_PAGE, totalLogs || filteredLogs.length)} de {totalLogs || filteredLogs.length}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <span className="text-sm text-gray-800 dark:text-gray-200 px-2">
                    Página {currentPage} de {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                  >
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                  <Shield className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  Política de Retenção de Dados
                </CardTitle>
                {retentionPolicies.length === 0 && (
                  <Button variant="outline" size="sm" onClick={handleSeedPolicies}>
                    Inicializar Políticas
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {retentionPolicies.length > 0 ? (
                  retentionPolicies.slice(0, 3).map((policy) => {
                    const config = CATEGORY_CONFIG[policy.category as ActionCategoryUI] || CATEGORY_CONFIG.system
                    const Icon = config.icon
                    return (
                      <div key={policy.id} className={`flex items-start gap-3 p-3 rounded-md ${config.color.split(' ')[0]}`}>
                        <Icon className={`w-5 h-5 mt-0.5 ${config.color.split(' ').slice(1).join(' ')}`} />
                        <div>
                          <p className={`text-sm font-medium ${config.color.split(' ').slice(1, 3).join(' ')}`}>
                            {policy.description || CATEGORY_CONFIG[policy.category as ActionCategoryUI]?.label || policy.category}
                            {policy.isSoxRequired && ' (SOX Compliance)'}
                          </p>
                          <p className={`text-xs mt-1 ${config.color.split(' ').slice(1).join(' ')}`}>
                            Retenção: <strong>{policy.retentionMonths} meses ({Math.floor(policy.retentionMonths / 12)} anos)</strong>
                          </p>
                          <p className={`text-xs ${config.color.split(' ').slice(1).join(' ')}`}>
                            Próxima purga agendada: {formatNextPurgeDate(policy.retentionMonths)}
                          </p>
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <>
                    <div className="flex items-start gap-3 p-3 bg-gray-100 dark:bg-gray-800 rounded-md">
                      <Database className="w-5 h-5 text-gray-600 dark:text-gray-400 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                          Logs de Auditoria (SOX Compliance)
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                          Retenção: <strong>7 anos (84 meses)</strong>
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          Próxima purga agendada: {formatNextPurgeDate(84)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                      <Eye className="w-5 h-5 text-status-success dark:text-status-success mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-status-success dark:text-status-success">
                          Logs de Acesso a Dados
                        </p>
                        <p className="text-xs text-status-success dark:text-status-success mt-1">
                          Retenção: <strong>24 meses</strong>
                        </p>
                        <p className="text-xs text-status-success dark:text-status-success">
                          Próxima purga agendada: {formatNextPurgeDate(24)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md">
                      <Brain className="w-5 h-5 text-wedo-purple dark:text-wedo-purple mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-wedo-purple dark:text-wedo-purple">
                          Decisões de IA (Explainability)
                        </p>
                        <p className="text-xs text-wedo-purple dark:text-wedo-purple mt-1">
                          Retenção: <strong>36 meses</strong>
                        </p>
                        <p className="text-xs text-wedo-purple dark:text-wedo-purple">
                          Próxima purga agendada: {formatNextPurgeDate(36)}
                        </p>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                Estatísticas de Auditoria
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                  <div className="flex items-center gap-2">
                    <ScrollText className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-800 dark:text-gray-200">Total de Registros</span>
                  </div>
                  <span className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                    {(stats?.totalLogs || totalLogs || 0).toLocaleString()}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-status-warning" />
                    <span className="text-sm text-gray-800 dark:text-gray-200">Ações com Falha</span>
                  </div>
                  <span className="text-lg font-semibold text-status-warning">{failedActions}</span>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                  <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4 text-wedo-purple" />
                    <span className="text-sm text-gray-800 dark:text-gray-200">Decisões IA Auditáveis</span>
                  </div>
                  <span className="text-lg font-semibold text-wedo-purple">
                    {stats?.aiDecisionsCount || categoryStats.ai_decision}
                  </span>
                </div>

                <div className="pt-2">
                  <Button
                    variant="outline"
                    className="w-full gap-2"
                    onClick={() => window.location.href = '/admin/clientes?tab=observabilidade'}
                  >
                    <Eye className="w-4 h-4" />
                    Ver Observabilidade de IA
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
