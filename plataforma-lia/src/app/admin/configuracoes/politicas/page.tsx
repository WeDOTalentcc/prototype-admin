"use client"

import React, { useState, useMemo, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"
import {
  Shield,
  Lock,
  Clock,
  Database,
  ArrowLeft,
  Edit,
  Save,
  X,
  History,
  Search,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Brain,
  FileText,
  Users,
  Key,
  Timer,
  HardDrive,
  Zap,
  Eye,
  Settings,
  Loader2,
} from "lucide-react"
import { useGlobalPolicies, Policy, PolicyCategory, PolicyHistoryEntry } from "@/hooks/admin/useGlobalPolicies"
import { useAuth } from "@/components/auth-context"

const SECTOR_OPTIONS = [
  { value: "tech", label: "Tecnologia" },
  { value: "varejo", label: "Varejo" },
  { value: "logistica", label: "Logística" },
  { value: "financeiro", label: "Financeiro" },
  { value: "saude", label: "Saúde" },
  { value: "rpo", label: "RPO / Consultoria" },
] as const

type SectorValue = (typeof SECTOR_OPTIONS)[number]["value"]

const CATEGORY_CONFIG: Record<PolicyCategory, { label: string; icon: React.ElementType; color: string; description: string }> = {
  data_retention: {
    label: 'Retenção de Dados',
    icon: Database,
    color: 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400',
    description: 'Políticas de armazenamento e exclusão de dados conforme LGPD e SOX',
  },
  ai_usage: {
    label: 'Limites de IA',
    icon: Brain,
    color: 'bg-wedo-purple/10 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple',
    description: 'Controle de uso de tokens e rate limits por cliente',
  },
  security: {
    label: 'Segurança',
    icon: Lock,
    color: 'bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success',
    description: 'Políticas de senha, sessão e autenticação',
  },
  compliance: {
    label: 'Compliance',
    icon: Shield,
    color: 'bg-status-warning/10 text-status-warning dark:bg-status-warning/20 dark:text-status-warning',
    description: 'Logs de auditoria e requisitos de consentimento',
  },
}

const COMPLEXITY_LABELS: Record<string, string> = {
  low: 'Baixa',
  medium: 'Média',
  high: 'Alta',
  very_high: 'Muito Alta',
}

const REVIEW_LABELS: Record<string, string> = {
  weekly: 'Semanal',
  monthly: 'Mensal',
  quarterly: 'Trimestral',
  annually: 'Anual',
}

export default function GlobalPoliciesPage() {
  const { user } = useAuth()
  const {
    policies,
    history,
    isLoading,
    isUpdating,
    error,
    refetch,
    fetchPolicies,
    fetchHistory,
    updatePolicy,
    togglePolicy,
    seedPolicies,
  } = useGlobalPolicies()

  const [selectedSector, setSelectedSector] = useState<SectorValue | "">("")
  const [isApplyingSector, setIsApplyingSector] = useState(false)

  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<PolicyCategory | 'all'>('all')
  const [editingPolicy, setEditingPolicy] = useState<Policy | null>(null)
  const [editValue, setEditValue] = useState<string | number | boolean>('')
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false)

  const filteredPolicies = useMemo(() => {
    return policies.filter((policy) => {
      const matchesSearch = !searchQuery || 
        policy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        policy.description.toLowerCase().includes(searchQuery.toLowerCase())
      
      const matchesCategory = activeTab === 'all' || policy.category === activeTab
      
      return matchesSearch && matchesCategory
    })
  }, [policies, searchQuery, activeTab])

  const stats = useMemo(() => {
    const byCategory = {
      data_retention: policies.filter(p => p.category === 'data_retention').length,
      ai_usage: policies.filter(p => p.category === 'ai_usage').length,
      security: policies.filter(p => p.category === 'security').length,
      compliance: policies.filter(p => p.category === 'compliance').length,
    }
    return {
      total: policies.length,
      active: policies.filter(p => p.isActive).length,
      byCategory,
    }
  }, [policies])

  const handleEditPolicy = (policy: Policy) => {
    setEditingPolicy(policy)
    setEditValue(policy.value)
    setIsEditModalOpen(true)
  }

  const handleSavePolicy = async () => {
    if (!editingPolicy) return

    const result = await updatePolicy(editingPolicy.id, editValue)
    if (result) {
      setIsEditModalOpen(false)
      setEditingPolicy(null)
      toast.success('Política atualizada com sucesso!')
    } else {
      toast.error('Erro ao atualizar política')
    }
  }

  const handleTogglePolicy = async (policyId: string, currentState: boolean) => {
    const result = await togglePolicy(policyId, !currentState)
    if (result) {
      toast.success(`Política ${!currentState ? 'ativada' : 'desativada'}`)
    } else {
      toast.error('Erro ao alterar status da política')
    }
  }

  const handleRefresh = async () => {
    toast.info('Sincronizando políticas...')
    await refetch()
    toast.success('Políticas sincronizadas!')
  }

  const handleApplySector = async () => {
    if (!selectedSector) return
    setIsApplyingSector(true)
    try {
      // company_id not available in auth context shape; fall back to demo for now
      const companyId = "demo_company"
      const res = await fetch(
        `/api/backend-proxy/policy-engine/apply-sector?companyId=${companyId}&sector=${selectedSector}`,
        { method: "POST" },
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await refetch()
      toast.success(`Template "${SECTOR_OPTIONS.find(s => s.value === selectedSector)?.label}" aplicado com sucesso!`)
      setSelectedSector("")
    } catch {
      toast.error("Erro ao aplicar template de setor")
    } finally {
      setIsApplyingSector(false)
    }
  }

  const handleOpenAuditModal = async () => {
    setIsAuditModalOpen(true)
    await fetchHistory()
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatValue = (policy: Policy): string => {
    if (policy.valueType === 'boolean') {
      return policy.value ? 'Ativado' : 'Desativado'
    }
    if (policy.valueType === 'select') {
      if (policy.options?.includes('low')) {
        return COMPLEXITY_LABELS[policy.value as string] || String(policy.value)
      }
      if (policy.options?.includes('weekly')) {
        return REVIEW_LABELS[policy.value as string] || String(policy.value)
      }
      return String(policy.value)
    }
    if (policy.valueType === 'number') {
      const numValue = Number(policy.value)
      if (numValue >= 1000) {
        return `${numValue.toLocaleString('pt-BR')} ${policy.unit || ''}`
      }
      return `${policy.value} ${policy.unit || ''}`
    }
    return String(policy.value)
  }

  const getCategoryIcon = (category: PolicyCategory) => {
    const config = CATEGORY_CONFIG[category]
    if (!config) return null
    const Icon = config.icon
    return <Icon className="w-4 h-4" />
  }

  if (isLoading && policies.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-gray-600 dark:text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Carregando políticas...</p>
        </div>
      </div>
    )
  }

  if (error && policies.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-status-warning mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-950 dark:text-gray-50 mb-2">
            Erro ao carregar políticas
          </h3>
          <p className="text-gray-500 mb-4">{error.message}</p>
          <Button onClick={refetch} className="gap-2">
            <RefreshCw className="w-4 h-4" />
            Tentar novamente
          </Button>
        </div>
      </div>
    )
  }

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
              <h1 className="text-2xl font-semibold text-gray-950 dark:text-gray-50">
                Políticas Globais
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Configure políticas de compliance, segurança e uso da plataforma
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleOpenAuditModal}
              className="gap-2"
            >
              <History className="w-4 h-4" />
              Histórico
            </Button>
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={isLoading}
              className="gap-2"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              Sincronizar
            </Button>
          </div>
        </div>

        {/* Templates por Setor — P3-3 */}
        <Card className="mb-6 border-gray-200 dark:border-gray-700">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-950 dark:text-gray-50 flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Templates por Setor
            </CardTitle>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Aplique políticas padrão pré-configuradas para o setor da empresa. Sobrescreve valores atuais.
            </p>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-3">
              <Select
                value={selectedSector}
                onValueChange={(v) => setSelectedSector(v as SectorValue)}
              >
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Selecionar setor…" />
                </SelectTrigger>
                <SelectContent>
                  {SECTOR_OPTIONS.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                onClick={handleApplySector}
                disabled={!selectedSector || isApplyingSector}
                className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 gap-2 sm:w-auto"
              >
                {isApplyingSector ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Zap className="w-4 h-4" />
                )}
                Aplicar Template
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {(Object.entries(CATEGORY_CONFIG) as [PolicyCategory, typeof CATEGORY_CONFIG[PolicyCategory]][]).map(([key, config]) => {
            const Icon = config.icon
            const count = stats.byCategory[key]
            return (
              <Card
                key={key}
                className={`cursor-pointer transition-all ${activeTab === key ? 'ring-2 ring-gray-900/20' : ''}`}
                onClick={() => setActiveTab(activeTab === key ? 'all' : key)}
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

        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Buscar políticas..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as PolicyCategory | 'all')} className="space-y-6">
          <TabsList className="bg-gray-100 dark:bg-gray-800">
            <TabsTrigger value="all" className="gap-2">
              <Settings className="w-4 h-4" />
              Todas
            </TabsTrigger>
            <TabsTrigger value="data_retention" className="gap-2">
              <Database className="w-4 h-4" />
              Retenção
            </TabsTrigger>
            <TabsTrigger value="ai_usage" className="gap-2">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              IA
            </TabsTrigger>
            <TabsTrigger value="security" className="gap-2">
              <Lock className="w-4 h-4" />
              Segurança
            </TabsTrigger>
            <TabsTrigger value="compliance" className="gap-2">
              <Shield className="w-4 h-4" />
              Compliance
            </TabsTrigger>
          </TabsList>

          <TabsContent value={activeTab} className="mt-6">
            {filteredPolicies.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="py-12">
                  <div className="text-center">
                    <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-950 dark:text-gray-50 mb-2">
                      Nenhuma política encontrada
                    </h3>
                    <p className="text-gray-500">
                      Tente ajustar os filtros de busca
                    </p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                        <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                          Política
                        </th>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                          Categoria
                        </th>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                          Valor Atual
                        </th>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                          Última Atualização
                        </th>
                        <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                          Status
                        </th>
                        <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider px-6 py-3">
                          Ações
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {filteredPolicies.map((policy) => {
                        const categoryConfig = CATEGORY_CONFIG[policy.category]
                        if (!categoryConfig) return null
                        
                        return (
                          <tr 
                            key={policy.id}
                            className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                          >
                            <td className="px-6 py-4">
                              <div>
                                <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                                  {policy.name}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-md">
                                  {policy.description}
                                </p>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <Badge className={`${categoryConfig.color} gap-1`}>
                                {getCategoryIcon(policy.category)}
                                {categoryConfig.label}
                              </Badge>
                            </td>
                            <td className="px-6 py-4">
                              <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                                {formatValue(policy)}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              <div>
                                <p className="text-sm text-gray-950 dark:text-gray-50">
                                  {formatDate(policy.updatedAt)}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                  por {policy.updatedBy}
                                </p>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-2">
                                <Switch
                                  checked={policy.isActive}
                                  onCheckedChange={() => handleTogglePolicy(policy.id, policy.isActive)}
                                  disabled={isUpdating}
                                />
                                <span className={`text-xs ${policy.isActive ? 'text-status-success' : 'text-gray-500'}`}>
                                  {policy.isActive ? 'Ativo' : 'Inativo'}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditPolicy(policy)}
                                className="text-gray-600 hover:text-gray-900 dark:hover:text-gray-50"
                                disabled={isUpdating}
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>

        <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Editar Política</DialogTitle>
              <DialogDescription>
                {editingPolicy?.description}
              </DialogDescription>
            </DialogHeader>
            
            {editingPolicy && (
              <div className="space-y-4 py-4">
                <div>
                  <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">
                    {editingPolicy.name}
                  </label>
                  
                  {editingPolicy.valueType === 'boolean' && (
                    <div className="flex items-center gap-3">
                      <Switch
                        checked={editValue as boolean}
                        onCheckedChange={(checked: boolean) => setEditValue(checked)}
                      />
                      <span className="text-sm text-gray-600">
                        {editValue ? 'Ativado' : 'Desativado'}
                      </span>
                    </div>
                  )}
                  
                  {editingPolicy.valueType === 'number' && (
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        value={editValue as number}
                        onChange={(e) => setEditValue(Number(e.target.value))}
                        min={editingPolicy.minValue}
                        max={editingPolicy.maxValue}
                        className="flex-1"
                      />
                      {editingPolicy.unit && (
                        <span className="text-sm text-gray-500 min-w-[80px]">
                          {editingPolicy.unit}
                        </span>
                      )}
                    </div>
                  )}
                  
                  {editingPolicy.valueType === 'select' && editingPolicy.options && (
                    <Select value={editValue as string} onValueChange={setEditValue}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {editingPolicy.options.map((option) => {
                          const label = COMPLEXITY_LABELS[option] || REVIEW_LABELS[option] || option
                          return (
                            <SelectItem key={option} value={option}>
                              {label}
                            </SelectItem>
                          )
                        })}
                      </SelectContent>
                    </Select>
                  )}
                  
                  {editingPolicy.valueType === 'string' && (
                    <Input
                      value={editValue as string}
                      onChange={(e) => setEditValue(e.target.value)}
                    />
                  )}
                  
                  {editingPolicy.valueType === 'number' && (editingPolicy.minValue || editingPolicy.maxValue) && (
                    <p className="text-xs text-gray-500 mt-2">
                      Valor permitido: {editingPolicy.minValue} - {editingPolicy.maxValue} {editingPolicy.unit}
                    </p>
                  )}
                </div>
              </div>
            )}
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsEditModalOpen(false)} disabled={isUpdating}>
                <X className="w-4 h-4 mr-2" />
                Cancelar
              </Button>
              <Button 
                onClick={handleSavePolicy}
                className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                disabled={isUpdating}
              >
                {isUpdating ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Save className="w-4 h-4 mr-2" />
                )}
                Salvar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={isAuditModalOpen} onOpenChange={setIsAuditModalOpen}>
          <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <History className="w-5 h-5" />
                Histórico de Alterações
              </DialogTitle>
              <DialogDescription>
                Registro de todas as mudanças em políticas globais
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              {history.length === 0 ? (
                <div className="text-center py-8">
                  <History className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">Nenhum histórico de alterações encontrado</p>
                </div>
              ) : (
                history.map((entry) => (
                  <div 
                    key={entry.id}
                    className="p-4 rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {entry.changeType === 'enable' && (
                          <CheckCircle2 className="w-4 h-4 text-status-success" />
                        )}
                        {entry.changeType === 'disable' && (
                          <AlertTriangle className="w-4 h-4 text-status-warning" />
                        )}
                        {entry.changeType === 'update' && (
                          <Edit className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        )}
                        <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                          {entry.policyName}
                        </span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {entry.changeType === 'update' && 'Atualização'}
                        {entry.changeType === 'enable' && 'Ativação'}
                        {entry.changeType === 'disable' && 'Desativação'}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm mb-2">
                      <div className="flex items-center gap-1 text-status-error dark:text-status-error">
                        <X className="w-3 h-3" />
                        <span className="line-through">{entry.previousValue}</span>
                      </div>
                      <span className="text-gray-400">→</span>
                      <div className="flex items-center gap-1 text-status-success dark:text-status-success">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>{entry.newValue}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <div className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {entry.changedBy}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(entry.changedAt)}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsAuditModalOpen(false)}>
                Fechar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
