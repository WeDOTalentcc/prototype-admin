"use client"

import React, { useState, useEffect, useCallback } from "react"
import { 
  ShieldPlus, 
  CheckCircle2, 
  Calendar, 
  AlertTriangle,
  FileText,
  Building2,
  DollarSign,
  Clock,
  Shield,
  FileCheck,
  Download,
  History,
  Plus,
  Upload,
  Edit2,
  Trash2,
  RefreshCw,
  XCircle,
  Loader2
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
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
  insuranceService,
  InsurancePolicy,
  InsuranceCoverage,
  InsuranceDocument,
  InsuranceClaim,
  InsuranceDashboard,
  InsuranceAlert,
  BCBCoverageChecklistItem,
  CreatePolicyInput,
  CreateCoverageInput,
  CreateClaimInput,
} from "@/services/admin/insurance-service"
import { ActivePolicyCard } from "./ActivePolicyCard"
import { InsurancePoliciesTable, InsuranceClaimsTable } from "./InsurancePoliciesTable"

const BCB_COVERAGE_TYPES = [
  { type: 'data_breach', name: 'Violação de Dados', article: 'Art. 3º, I', description: 'Cobertura para violação e vazamento de dados pessoais' },
  { type: 'ransomware', name: 'Extorsão Cibernética', article: 'Art. 3º, II', description: 'Pagamento de resgate e custos de ransomware' },
  { type: 'business_interruption', name: 'Interrupção de Negócios', article: 'Art. 3º, III', description: 'Perdas por interrupção de operações devido a incidentes cyber' },
  { type: 'regulatory_defense', name: 'Defesa Regulatória', article: 'Art. 3º, IV', description: 'Custos legais e defesa junto a órgãos reguladores' },
  { type: 'crisis_management', name: 'Gestão de Crise', article: 'Art. 3º, V', description: 'Comunicação de crise e gestão de reputação' },
  { type: 'forensic_investigation', name: 'Investigação Forense', article: 'Art. 3º, VI', description: 'Custos de investigação e análise forense' },
  { type: 'notification_costs', name: 'Custos de Notificação', article: 'Art. 3º, VII', description: 'Notificação de titulares e autoridades' },
  { type: 'third_party_liability', name: 'Responsabilidade Civil', article: 'Art. 3º, VIII', description: 'Responsabilidade civil perante terceiros' },
]

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value)
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'active':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">
        <CheckCircle2 className="w-3 h-3 mr-1" />
        Ativo
      </Badge>
    case 'expired':
      return <Badge className="bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-bg-tertiary">
        Expirado
      </Badge>
    case 'pending':
      return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">
        <Clock className="w-3 h-3 mr-1" />
        Pendente
      </Badge>
    case 'cancelled':
      return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">
        Cancelado
      </Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

const getClaimStatusBadge = (status: string) => {
  switch (status) {
    case 'open':
 return <Badge className="text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-lia-bg-tertiary">Aberto</Badge>
    case 'under_review':
      return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">Em Análise</Badge>
    case 'approved':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Aprovado</Badge>
    case 'denied':
      return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">Negado</Badge>
    case 'paid':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Pago</Badge>
    case 'closed':
      return <Badge className="bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-bg-tertiary">Encerrado</Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

const getAlertSeverityStyle = (severity: string) => {
  switch (severity) {
    case 'critical':
      return { bg: 'var(--status-error-bg)', border: 'var(--status-error)', icon: 'text-status-error' }
    case 'high':
      return { bg: 'var(--status-warning-bg)', border: 'var(--status-warning)', icon: 'text-status-warning' }
    case 'medium':
      return { bg: 'var(--lia-interactive-active)', border: 'var(--lia-border-subtle)', icon: 'text-lia-text-secondary dark:text-lia-text-tertiary' }
    default:
      return { bg: 'var(--lia-bg-secondary)', border: 'var(--lia-text-tertiary)', icon: 'text-lia-text-secondary' }
  }
}

export default function SeguroCiberneticoPage() {
  const clientId = 'default'
  
  const [loading, setLoading] = useState(true)
  const [dashboard, setDashboard] = useState<InsuranceDashboard | null>(null)
  const [policies, setPolicies] = useState<InsurancePolicy[]>([])
  const [coverages, setCoverages] = useState<InsuranceCoverage[]>([])
  const [documents, setDocuments] = useState<InsuranceDocument[]>([])
  const [claims, setClaims] = useState<InsuranceClaim[]>([])
  const [alerts, setAlerts] = useState<InsuranceAlert[]>([])
  const [checklist, setChecklist] = useState<BCBCoverageChecklistItem[]>([])
  
  const [policyModalOpen, setPolicyModalOpen] = useState(false)
  const [coverageModalOpen, setCoverageModalOpen] = useState(false)
  const [claimModalOpen, setClaimModalOpen] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<InsurancePolicy | null>(null)
  const [selectedPolicyId, setSelectedPolicyId] = useState<string | null>(null)
  
  const [submitting, setSubmitting] = useState(false)
  
  const [policyForm, setPolicyForm] = useState<CreatePolicyInput>({
    policyNumber: '',
    insurer: '',
    coverage: 0,
    deductible: 0,
    startDate: '',
    endDate: '',
    policyType: 'cyber',
    notes: '',
  })
  
  const [coverageForm, setCoverageForm] = useState<CreateCoverageInput>({
    coverageType: '',
    name: '',
    description: '',
    coverageLimit: 0,
    bcbArticle: '',
  })
  
  const [claimForm, setClaimForm] = useState<CreateClaimInput>({
    policyId: '',
    incidentDate: '',
    description: '',
    claimAmount: 0,
  })

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [dashboardData, policiesData, claimsData, alertsData, checklistData] = await Promise.all([
        insuranceService.getDashboard(clientId),
        insuranceService.getPolicies(clientId),
        insuranceService.getClaims(clientId),
        insuranceService.getAlerts(clientId),
        insuranceService.getCoverageChecklist(clientId),
      ])
      
      setDashboard(dashboardData)
      setPolicies(policiesData.policies)
      setClaims(claimsData.claims)
      setAlerts(alertsData.alerts)
      setChecklist(checklistData.items)
      
      if (dashboardData.activePolicy) {
        setSelectedPolicyId(dashboardData.activePolicy.id)
        const [coveragesData, documentsData] = await Promise.all([
          insuranceService.getCoverages(clientId, dashboardData.activePolicy.id),
          insuranceService.getDocuments(clientId, dashboardData.activePolicy.id),
        ])
        setCoverages(coveragesData.coverages)
        setDocuments(documentsData.documents)
      }
    } catch (error) {
    } finally {
      setLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleCreatePolicy = async () => {
    setSubmitting(true)
    try {
      await insuranceService.createPolicy(clientId, policyForm)
      setPolicyModalOpen(false)
      resetPolicyForm()
      await loadData()
    } catch (error) {
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdatePolicy = async () => {
    if (!editingPolicy) return
    setSubmitting(true)
    try {
      await insuranceService.updatePolicy(clientId, editingPolicy.id, {
        policyNumber: policyForm.policyNumber,
        insurer: policyForm.insurer,
        coverage: policyForm.coverage,
        deductible: policyForm.deductible,
        startDate: policyForm.startDate,
        endDate: policyForm.endDate,
        notes: policyForm.notes,
      })
      setPolicyModalOpen(false)
      setEditingPolicy(null)
      resetPolicyForm()
      await loadData()
    } catch (error) {
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeletePolicy = async (policyId: string) => {
    if (!confirm('Tem certeza que deseja desativar esta apólice?')) return
    try {
      await insuranceService.deletePolicy(clientId, policyId)
      await loadData()
    } catch (error) {
    }
  }

  const handleAddCoverage = async () => {
    if (!selectedPolicyId) return
    setSubmitting(true)
    try {
      await insuranceService.addCoverage(clientId, selectedPolicyId, coverageForm)
      setCoverageModalOpen(false)
      resetCoverageForm()
      await loadData()
    } catch (error) {
    } finally {
      setSubmitting(false)
    }
  }

  const handleCreateClaim = async () => {
    setSubmitting(true)
    try {
      await insuranceService.createClaim(clientId, claimForm)
      setClaimModalOpen(false)
      resetClaimForm()
      await loadData()
    } catch (error) {
    } finally {
      setSubmitting(false)
    }
  }

  const resetPolicyForm = () => {
    setPolicyForm({
      policyNumber: '',
      insurer: '',
      coverage: 0,
      deductible: 0,
      startDate: '',
      endDate: '',
      policyType: 'cyber',
      notes: '',
    })
  }

  const resetCoverageForm = () => {
    setCoverageForm({
      coverageType: '',
      name: '',
      description: '',
      coverageLimit: 0,
      bcbArticle: '',
    })
  }

  const resetClaimForm = () => {
    setClaimForm({
      policyId: '',
      incidentDate: '',
      description: '',
      claimAmount: 0,
    })
  }

  const openEditPolicy = (policy: InsurancePolicy) => {
    setEditingPolicy(policy)
    setPolicyForm({
      policyNumber: policy.policyNumber,
      insurer: policy.insurer,
      coverage: policy.coverage,
      deductible: policy.deductible,
      startDate: policy.startDate,
      endDate: policy.endDate,
      policyType: policy.policyType,
      notes: policy.notes || '',
    })
    setPolicyModalOpen(true)
  }

  const openNewPolicy = () => {
    setEditingPolicy(null)
    resetPolicyForm()
    setPolicyModalOpen(true)
  }

  const activePolicy = dashboard?.activePolicy || policies.find(p => p.status === 'active')
  const daysRemaining = dashboard?.daysUntilExpiry ?? -1
  const isExpiringSoon = daysRemaining > 0 && daysRemaining <= 60
  const isExpired = daysRemaining < 0

  const displayChecklist = checklist.length > 0 ? checklist : BCB_COVERAGE_TYPES.map(ct => ({
    coverageType: ct.type,
    name: ct.name,
    description: ct.description,
    bcbArticle: ct.article,
    isMandatory: true,
    isCovered: coverages.some(c => c.coverageType === ct.type && c.isActive),
  }))

  const coveredCount = displayChecklist.filter(item => item.isCovered).length
  const compliancePercentage = displayChecklist.length > 0 
    ? Math.round((coveredCount / displayChecklist.length) * 100) 
    : 0

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-content-lg" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="flex items-center gap-3" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-secondary dark:text-lia-text-tertiary" />
          <span className="text-lia-text-secondary dark:text-lia-text-tertiary" >Carregando dados do seguro...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30"
            >
              <ShieldPlus className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary"
                
              >
                Seguro Cibernético BCB 498
              </h1>
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                Gestão de apólice e conformidade com Resolução BCB 498/2025
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => loadData()}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Atualizar
            </Button>
            <Button onClick={openNewPolicy}>
              <Plus className="w-4 h-4 mr-2" />
              Nova Apólice
            </Button>
          </div>
        </div>

        {alerts.length > 0 && (
          <div className="space-y-3 mb-6">
            {alerts.map((alert) => {
              const style = getAlertSeverityStyle(alert.severity)
              return (
                <div 
                  key={alert.id}
                  className="p-4 rounded-md border-l-4 flex items-center gap-3"
                  style={{backgroundColor: style.bg, borderLeftColor: style.border}}
                >
                  <AlertTriangle className={`w-5 h-5 ${style.icon}`} />
                  <div className="flex-1">
                    <p className="font-medium text-lia-text-primary dark:text-lia-text-primary" >{alert.title}</p>
                    <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >{alert.message}</p>
                  </div>
                  {alert.dueDate && (
                    <Badge variant="outline">{new Date(alert.dueDate).toLocaleDateString('pt-BR')}</Badge>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {isExpiringSoon && !isExpired && activePolicy && (
          <div 
            className="mb-6 p-4 rounded-md border-l-4 flex items-center gap-3 bg-status-warning-bg" style={{ borderLeftColor: 'var(--status-warning)' }}
          >
            <AlertTriangle className="w-5 h-5 text-status-warning" />
            <div>
              <p className="font-medium text-status-warning">Alerta de Renovação</p>
              <p className="text-sm text-status-warning">
                A apólice vence em {daysRemaining} dias ({new Date(activePolicy.endDate).toLocaleDateString('pt-BR')}). Inicie o processo de renovação com antecedência.
              </p>
            </div>
          </div>
        )}

        {isExpired && activePolicy && (
          <div 
            className="mb-6 p-4 rounded-md border-l-4 flex items-center gap-3 bg-red-500/10" style={{ borderLeftColor: 'var(--status-error)' }}
          >
            <AlertTriangle className="w-5 h-5 text-status-error" />
            <div>
              <p className="font-medium text-status-error">Apólice Expirada</p>
              <p className="text-sm text-status-error">
                A apólice expirou em {new Date(activePolicy.endDate).toLocaleDateString('pt-BR')}. Renove imediatamente para manter a cobertura e conformidade com BCB 498.
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-status-success/15">
                  <Shield className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Status da Apólice</p>
                  <p className="font-medium text-lia-text-primary dark:text-lia-text-primary" >
                    {activePolicy ? 'Ativa' : 'Sem apólice ativa'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                  <Clock className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
                <div>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Dias até Vencimento</p>
                  <p className={`font-medium ${isExpiringSoon ? 'text-status-warning' : isExpired ? 'text-status-error' : 'text-lia-text-primary dark:text-lia-text-primary'}`}>
                    {isExpired ? 'Expirado' : daysRemaining > 0 ? `${daysRemaining} dias` : 'N/A'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-status-success/15">
                  <DollarSign className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Valor Coberto</p>
                  <p className="font-medium text-status-success">
                    {activePolicy ? formatCurrency(activePolicy.coverage) : 'R$ 0,00'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-wedo-purple/15">
                  <FileCheck className="w-5 h-5 text-wedo-purple" />
                </div>
                <div>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Conformidade BCB</p>
                  <p className="font-medium text-lia-text-primary dark:text-lia-text-primary" >
                    {coveredCount}/{displayChecklist.length} ({compliancePercentage}%)
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {activePolicy && (
            <ActivePolicyCard
              activePolicy={activePolicy}
              daysRemaining={daysRemaining}
              isExpiringSoon={isExpiringSoon}
              isExpired={isExpired}
              statusBadge={getStatusBadge(activePolicy.status)}
              onEdit={openEditPolicy}
            />
          )}

          <Card  className={activePolicy ? '' : 'lg:col-span-3'}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
                    Documentos
                  </CardTitle>
                </div>
                {activePolicy && (
                  <Button variant="outline" size="sm">
                    <Upload className="w-4 h-4 mr-1" />
                    Upload
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {documents.length > 0 ? (
                <div className="space-y-3">
                  {documents.map((doc) => (
                    <div 
                      key={doc.id}
                      className="p-3 rounded-md flex items-center justify-between bg-lia-bg-secondary dark:bg-lia-bg-primary"
                      
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                        <div>
                          <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary" >{doc.filename}</p>
                          <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                            {new Date(doc.uploadedAt).toLocaleDateString('pt-BR')} • {doc.documentType}
                          </p>
                        </div>
                      </div>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                  Nenhum documento anexado
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldPlus className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
                    Coberturas Incluídas
                  </CardTitle>
                </div>
                {activePolicy && (
                  <Button variant="outline" size="sm" onClick={() => setCoverageModalOpen(true)}>
                    <Plus className="w-4 h-4 mr-1" />
                    Adicionar
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {coverages.length > 0 ? (
                <div className="space-y-3">
                  {coverages.map((coverage) => (
                    <div 
                      key={coverage.id}
                      className="p-3 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-primary"
                      
                    >
                      <div className="flex items-start gap-3">
                        <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5" />
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary" >
                              {coverage.name}
                            </span>
                            {coverage.bcbArticle && (
                              <Badge variant="outline" className="text-micro font-mono">{coverage.bcbArticle}</Badge>
                            )}
                          </div>
                          {coverage.description && (
                            <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary" >
                              {coverage.description}
                            </p>
                          )}
                          {coverage.coverageLimit && (
                            <p className="text-xs mt-1 text-status-success">
                              Limite: {formatCurrency(coverage.coverageLimit)}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                  Nenhuma cobertura cadastrada
                </div>
              )}
            </CardContent>
          </Card>

          <Card >
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
                  Checklist BCB 498/2025
                </CardTitle>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <Progress value={compliancePercentage} className="flex-1 h-2" />
                <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary" >
                  {compliancePercentage}%
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {displayChecklist.map((item, index) => (
                  <div 
                    key={`checklist-${index}`}
                    className="flex items-center justify-between p-3 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-primary"
                    
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        {item.isCovered ? (
                          <CheckCircle2 className="w-4 h-4 text-status-success" />
                        ) : (
                          <XCircle className="w-4 h-4 text-status-error" />
                        )}
                        <span className="text-sm text-lia-text-primary dark:text-lia-text-primary" >
                          {item.name}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-micro font-mono">
                        {item.bcbArticle}
                      </Badge>
                      <Badge 
                        className={
                          item.isCovered 
                            ? 'bg-status-success/15 text-status-success hover:bg-status-success/15' 
                            : 'bg-status-error/15 text-status-error hover:bg-status-error/15'
                        }
                      >
                        {item.isCovered ? 'Coberto' : 'Não Coberto'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 p-3 rounded-md border-l-4 border-l-lia-border-default bg-lia-interactive-active/20">
                <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                  <strong>Resolução BCB 498/2025</strong> - Dispõe sobre a política de segurança cibernética e sobre os requisitos para a contratação de serviços de processamento e armazenamento de dados e de computação em nuvem.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6" >
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <History className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
                  Histórico de Apólices
                </CardTitle>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <InsurancePoliciesTable policies={policies} onEdit={openEditPolicy} onDelete={handleDeletePolicy} />
          </CardContent>
        </Card>

        <Card >
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
                  Histórico de Sinistros
                </CardTitle>
              </div>
              {activePolicy && (
                <Button variant="outline" size="sm" onClick={() => {
                  setClaimForm(prev => ({ ...prev, policyId: activePolicy.id }))
                  setClaimModalOpen(true)
                }}>
                  <Plus className="w-4 h-4 mr-1" />
                  Registrar Sinistro
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <InsuranceClaimsTable claims={claims} />
          </CardContent>
        </Card>
      </div>

      <Dialog open={policyModalOpen} onOpenChange={setPolicyModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingPolicy ? 'Editar Apólice' : 'Nova Apólice'}</DialogTitle>
            <DialogDescription>
              {editingPolicy ? 'Atualize os dados da apólice de seguro cibernético.' : 'Cadastre uma nova apólice de seguro cibernético.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Número da Apólice</Label>
                <Input 
                  value={policyForm.policyNumber}
                  onChange={(e) => setPolicyForm(prev => ({ ...prev, policyNumber: e.target.value }))}
                  placeholder="CYB-2024-123456"
                />
              </div>
              <div className="space-y-2">
                <Label>Seguradora</Label>
                <Input 
                  value={policyForm.insurer}
                  onChange={(e) => setPolicyForm(prev => ({ ...prev, insurer: e.target.value }))}
                  placeholder="AIG Brasil"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Valor de Cobertura (R$)</Label>
                <Input 
                  type="number"
                  value={policyForm.coverage || ''}
                  onChange={(e) => setPolicyForm(prev => ({ ...prev, coverage: parseFloat(e.target.value) || 0 }))}
                  placeholder="5000000"
                />
              </div>
              <div className="space-y-2">
                <Label>Franquia (R$)</Label>
                <Input 
                  type="number"
                  value={policyForm.deductible || ''}
                  onChange={(e) => setPolicyForm(prev => ({ ...prev, deductible: parseFloat(e.target.value) || 0 }))}
                  placeholder="50000"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Data de Início</Label>
                <Input 
                  type="date"
                  value={policyForm.startDate}
                  onChange={(e) => setPolicyForm(prev => ({ ...prev, startDate: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Data de Término</Label>
                <Input 
                  type="date"
                  value={policyForm.endDate}
                  onChange={(e) => setPolicyForm(prev => ({ ...prev, endDate: e.target.value }))}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Observações</Label>
              <Textarea 
                value={policyForm.notes}
                onChange={(e) => setPolicyForm(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Observações adicionais..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPolicyModalOpen(false)}>Cancelar</Button>
            <Button 
              onClick={editingPolicy ? handleUpdatePolicy : handleCreatePolicy}
              disabled={submitting}
            >
              {submitting && <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />}
              {editingPolicy ? 'Salvar' : 'Criar Apólice'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={coverageModalOpen} onOpenChange={setCoverageModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Adicionar Cobertura</DialogTitle>
            <DialogDescription>
              Adicione uma nova cobertura à apólice ativa.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Tipo de Cobertura</Label>
              <Select 
                value={coverageForm.coverageType}
                onValueChange={(value) => {
                  const selected = BCB_COVERAGE_TYPES.find(ct => ct.type === value)
                  setCoverageForm(prev => ({
                    ...prev,
                    coverageType: value,
                    name: selected?.name || '',
                    description: selected?.description || '',
                    bcbArticle: selected?.article || '',
                  }))
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione o tipo de cobertura" />
                </SelectTrigger>
                <SelectContent>
                  {BCB_COVERAGE_TYPES.map((ct) => (
                    <SelectItem key={ct.type} value={ct.type}>
                      {ct.name} ({ct.article})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Nome da Cobertura</Label>
              <Input 
                value={coverageForm.name}
                onChange={(e) => setCoverageForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Violação de Dados"
              />
            </div>
            <div className="space-y-2">
              <Label>Descrição</Label>
              <Textarea 
                value={coverageForm.description}
                onChange={(e) => setCoverageForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Descrição da cobertura..."
                rows={3}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Limite de Cobertura (R$)</Label>
                <Input 
                  type="number"
                  value={coverageForm.coverageLimit || ''}
                  onChange={(e) => setCoverageForm(prev => ({ ...prev, coverageLimit: parseFloat(e.target.value) || 0 }))}
                  placeholder="1000000"
                />
              </div>
              <div className="space-y-2">
                <Label>Artigo BCB</Label>
                <Input 
                  value={coverageForm.bcbArticle}
                  onChange={(e) => setCoverageForm(prev => ({ ...prev, bcbArticle: e.target.value }))}
                  placeholder="Art. 3º, I"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCoverageModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleAddCoverage} disabled={submitting}>
              {submitting && <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />}
              Adicionar Cobertura
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={claimModalOpen} onOpenChange={setClaimModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Registrar Sinistro</DialogTitle>
            <DialogDescription>
              Registre um novo sinistro para a apólice ativa.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Data do Incidente</Label>
                <Input 
                  type="date"
                  value={claimForm.incidentDate}
                  onChange={(e) => setClaimForm(prev => ({ ...prev, incidentDate: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Valor Estimado (R$)</Label>
                <Input 
                  type="number"
                  value={claimForm.claimAmount || ''}
                  onChange={(e) => setClaimForm(prev => ({ ...prev, claimAmount: parseFloat(e.target.value) || 0 }))}
                  placeholder="100000"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Descrição do Incidente</Label>
              <Textarea 
                value={claimForm.description}
                onChange={(e) => setClaimForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Descreva o incidente de segurança..."
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setClaimModalOpen(false)}>Cancelar</Button>
            <Button onClick={handleCreateClaim} disabled={submitting}>
              {submitting && <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />}
              Registrar Sinistro
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
