"use client"

import React, { useState, useEffect, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
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
import {
  ShieldCheck,
  RefreshCw,
  Loader2,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  Download,
  Database,
  FileCheck,
  ClipboardCheck,
  Eye,
  MessageSquare,
  Scale,
  Shield,
  Lock,
  Building2,
  ExternalLink
} from "lucide-react"
import { toast } from "sonner"

interface ChecklistItem {
  text: string
  completed: boolean
}

interface HealthCheckItem {
  id: string
  reqId: string
  requirement: string
  framework: string
  category: string
  status: 'implemented' | 'partial' | 'pending' | 'na' | 'not_checked'
  evidence: string
  evidenceDetails: string | null
  checklistItems: ChecklistItem[]
  lastVerification: string | null
  comment: string | null
  nextReviewDate: string | null
  verified: boolean
  referenceUrl: string | null
  referenceLabel: string | null
}

interface FrameworkSummary {
  framework: string
  name: string
  compliancePercentage: number
  implemented: number
  partial: number
  pending: number
  na: number
  total: number
  icon: React.ReactNode
}

const API_BASE = '/api/backend-proxy/health-check/'

const FRAMEWORK_ICONS: Record<string, React.ReactNode> = {
  'SOX': <Scale className="w-5 h-5 text-gray-600 dark:text-gray-400" />,
  'SOC2': <Shield className="w-5 h-5 text-gray-600 dark:text-gray-400" />,
  'ISO27001': <Lock className="w-5 h-5 text-gray-600 dark:text-gray-400" />,
  'LGPD': <FileCheck className="w-5 h-5 text-gray-600 dark:text-gray-400" />,
  'BCB498': <Building2 className="w-5 h-5 text-gray-600 dark:text-gray-400" />,
  'EUAI': <ShieldCheck className="w-5 h-5 text-gray-600 dark:text-gray-400" />,
  'NYC144': <ClipboardCheck className="w-5 h-5 text-gray-600 dark:text-gray-400" />,
}

const FRAMEWORK_NAMES: Record<string, string> = {
  'SOX': 'SOX',
  'SOC2': 'SOC 2',
  'ISO27001': 'ISO 27001',
  'LGPD': 'LGPD',
  'BCB498': 'BCB 498',
  'EUAI': 'EU AI Act',
  'NYC144': 'NYC LL144',
}

const STATUS_OPTIONS = [
  { value: 'all', label: 'Todos os Status' },
  { value: 'implemented', label: 'Implementado' },
  { value: 'partial', label: 'Parcial' },
  { value: 'pending', label: 'Pendente' },
  { value: 'not_checked', label: 'Não Verificado' },
  { value: 'na', label: 'N/A' },
]

const CATEGORY_OPTIONS = [
  { value: 'all', label: 'Todas as Categorias' },
  { value: 'access_control', label: 'Controle de Acesso' },
  { value: 'data_protection', label: 'Proteção de Dados' },
  { value: 'security', label: 'Segurança' },
  { value: 'audit', label: 'Auditoria' },
  { value: 'governance', label: 'Governança' },
]

function getStatusBadge(status: string) {
  switch (status) {
    case 'implemented':
      return <Badge variant="success">Implementado</Badge>
    case 'partial':
      return <Badge variant="warning">Parcial</Badge>
    case 'pending':
      return <Badge variant="destructive">Pendente</Badge>
    case 'not_checked':
      return <Badge variant="outline">Não Verificado</Badge>
    case 'na':
    case 'not_applicable':
      return <Badge variant="default">N/A</Badge>
    default:
      return <Badge variant="outline">-</Badge>
  }
}

function getComplianceStatusIcon(percentage: number) {
  if (percentage >= 90) {
    return <CheckCircle2 className="w-5 h-5 text-status-success" />
  } else if (percentage >= 70) {
    return <AlertCircle className="w-5 h-5 text-status-warning" />
  } else {
    return <XCircle className="w-5 h-5 text-status-error" />
  }
}

function getComplianceStatusColor(percentage: number): string {
  if (percentage >= 90) return 'text-status-success'
  if (percentage >= 70) return 'text-status-warning'
  return 'text-status-error'
}

export default function HealthCheckPage() {
  const [summary, setSummary] = useState<FrameworkSummary[]>([])
  const [items, setItems] = useState<HealthCheckItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isSeedingData, setIsSeedingData] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [frameworkFilter, setFrameworkFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())
  
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<HealthCheckItem | null>(null)
  const [verifyComment, setVerifyComment] = useState('')
  const [verifyNextReviewDate, setVerifyNextReviewDate] = useState('')
  const [isVerifying, setIsVerifying] = useState(false)

  useEffect(() => {
    let isMounted = true
    
    const loadData = async () => {
      setIsRefreshing(true)
      try {
        const summaryResponse = await fetch(`${API_BASE}summary/`, { redirect: 'follow' })
        
        if (!isMounted) return
        
        if (summaryResponse.ok) {
          const summaryData = await summaryResponse.json()
          const frameworks = summaryData.by_framework || summaryData.frameworks || []
          const mappedSummary: FrameworkSummary[] = frameworks.map((fw: any) => ({
            framework: fw.framework,
            name: FRAMEWORK_NAMES[fw.framework] || fw.framework,
            compliancePercentage: fw.compliance_percentage || 0,
            implemented: fw.implemented || 0,
            partial: fw.partial || 0,
            pending: fw.pending || 0,
            na: fw.not_applicable || fw.na || 0,
            total: fw.total || 0,
            icon: FRAMEWORK_ICONS[fw.framework] || <ShieldCheck className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          }))
          if (isMounted) {
            setSummary(mappedSummary)
          }
        } else {
          if (isMounted) setSummary([])
        }

        const queryParams = new URLSearchParams()
        if (frameworkFilter !== 'all') queryParams.set('framework', frameworkFilter)
        if (statusFilter !== 'all') queryParams.set('status', statusFilter)
        
        const itemsUrl = queryParams.toString()
          ? `${API_BASE}?${queryParams}`
          : API_BASE
        
        const itemsResponse = await fetch(itemsUrl, { redirect: 'follow' })
        
        if (!isMounted) return
        
        if (itemsResponse.ok) {
          const itemsData = await itemsResponse.json()
          const mappedItems: HealthCheckItem[] = (itemsData.items || []).map((item: any) => ({
            id: item.id,
            reqId: item.req_id,
            requirement: item.requirement,
            framework: item.framework,
            category: item.category,
            status: item.status,
            evidence: item.evidence || '',
            evidenceDetails: item.evidence_details || null,
            checklistItems: item.checklist_items || [],
            lastVerification: item.last_checked_at,
            comment: item.check_comments || item.comment,
            nextReviewDate: item.next_review_date,
            verified: item.last_checked_at ? true : false,
            referenceUrl: item.reference_url,
            referenceLabel: item.reference_label
          }))
          if (isMounted) {
            setItems(mappedItems)
          }
        } else {
          if (isMounted) setItems([])
        }
      } catch (error) {
        if (isMounted) {
          setSummary([])
          setItems([])
        }
      } finally {
        if (isMounted) {
          setIsRefreshing(false)
          setIsLoading(false)
        }
      }
    }
    
    loadData()
    
    return () => {
      isMounted = false
    }
  }, [frameworkFilter, statusFilter])

  const fetchData = useCallback(async () => {
    setIsRefreshing(true)
    try {
      const summaryResponse = await fetch(`${API_BASE}summary/`, { redirect: 'follow' })
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json()
        const frameworks = summaryData.by_framework || summaryData.frameworks || []
        const mappedSummary: FrameworkSummary[] = frameworks.map((fw: any) => ({
          framework: fw.framework,
          name: FRAMEWORK_NAMES[fw.framework] || fw.framework,
          compliancePercentage: fw.compliance_percentage || 0,
          implemented: fw.implemented || 0,
          partial: fw.partial || 0,
          pending: fw.pending || 0,
          na: fw.not_applicable || fw.na || 0,
          total: fw.total || 0,
          icon: FRAMEWORK_ICONS[fw.framework] || <ShieldCheck className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        }))
        setSummary(mappedSummary)
      } else {
        setSummary([])
      }

      const itemsResponse = await fetch(API_BASE, { redirect: 'follow' })
      if (itemsResponse.ok) {
        const itemsData = await itemsResponse.json()
        const mappedItems: HealthCheckItem[] = (itemsData.items || []).map((item: any) => ({
          id: item.id,
          reqId: item.req_id,
          requirement: item.requirement,
          framework: item.framework,
          category: item.category,
          status: item.status,
          evidence: item.evidence || '',
          evidenceDetails: item.evidence_details || null,
          checklistItems: item.checklist_items || [],
          lastVerification: item.last_checked_at,
          comment: item.check_comments || item.comment,
          nextReviewDate: item.next_review_date,
          verified: item.last_checked_at ? true : false,
          referenceUrl: item.reference_url,
          referenceLabel: item.reference_label
        }))
        setItems(mappedItems)
      } else {
        setItems([])
      }
    } catch (error) {
      setSummary([])
      setItems([])
    } finally {
      setIsRefreshing(false)
      setIsLoading(false)
    }
  }, [])

  const handleSeedData = async () => {
    setIsSeedingData(true)
    try {
      const response = await fetch(`${API_BASE}seed/`, {
        method: 'POST',
        redirect: 'follow'
      })
      
      if (response.ok) {
        toast.success('Dados de demonstração criados com sucesso')
        await fetchData()
      } else {
        toast.error('Falha ao criar dados de demonstração')
      }
    } catch (error) {
      toast.error('Erro ao carregar dados de demonstração')
    } finally {
      setIsSeedingData(false)
    }
  }

  const handleExport = () => {
    const csvContent = [
      ['Req ID', 'Requisito', 'Framework', 'Categoria', 'Status', 'Evidência', 'Última Verificação', 'Comentário'].join(','),
      ...filteredItems.map(item => [
        item.reqId,
        `"${item.requirement}"`,
        item.framework,
        item.category,
        item.status,
        `"${item.evidence}"`,
        item.lastVerification ? new Date(item.lastVerification).toLocaleDateString('pt-BR') : '',
        `"${item.comment || ''}"`
      ].join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `health-check-export-${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    toast.success('Relatório exportado com sucesso')
  }

  const handleOpenVerifyModal = (item: HealthCheckItem) => {
    setSelectedItem(item)
    setVerifyComment(item.comment || '')
    setVerifyNextReviewDate(item.nextReviewDate ? item.nextReviewDate.split('T')[0] : '')
    setIsVerifyModalOpen(true)
  }

  const handleVerify = async () => {
    if (!selectedItem) return
    
    setIsVerifying(true)
    try {
      const response = await fetch(`${API_BASE}${selectedItem.reqId}/check/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        redirect: 'follow',
        body: JSON.stringify({
          comment: verifyComment,
          next_review_date: verifyNextReviewDate,
          verified: true
        })
      })

      if (response.ok) {
        toast.success(`Requisito ${selectedItem.reqId} verificado com sucesso`)
        setItems(prev => prev.map(item => 
          item.id === selectedItem.id 
            ? { ...item, verified: true, comment: verifyComment, nextReviewDate: verifyNextReviewDate, lastVerification: new Date().toISOString() }
            : item
        ))
        setIsVerifyModalOpen(false)
      } else {
        toast.error(`Falha ao verificar requisito ${selectedItem.reqId}`)
      }
    } catch (error) {
      toast.error(`Erro ao verificar requisito ${selectedItem.reqId}`)
    } finally {
      setIsVerifying(false)
    }
  }

  const toggleItemSelection = (id: string) => {
    setSelectedItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }

  const toggleAllSelection = () => {
    if (selectedItems.size === filteredItems.length) {
      setSelectedItems(new Set())
    } else {
      setSelectedItems(new Set(filteredItems.map(item => item.id)))
    }
  }

  const filteredItems = items.filter(item => {
    const matchesSearch = searchTerm === '' ||
      item.reqId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.requirement.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesFramework = frameworkFilter === 'all' || item.framework === frameworkFilter
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter
    const matchesCategory = categoryFilter === 'all' || item.category === categoryFilter

    return matchesSearch && matchesFramework && matchesStatus && matchesCategory
  })

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-600 dark:text-gray-400" />
          <span className="ml-3 text-sm text-gray-400 dark:text-gray-500">
            Carregando Health Check...
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center"
              style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
            >
              <ClipboardCheck className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold text-gray-800 dark:text-gray-100"
              >
                Compliance Health Check
              </h1>
              <p className="text-sm text-gray-400 dark:text-gray-500">
                Verificação consolidada de requisitos de conformidade
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleSeedData} disabled={isSeedingData}>
              <Database className={`w-4 h-4 mr-2 ${isSeedingData ? 'animate-pulse' : ''}`} />
              {isSeedingData ? 'Carregando...' : 'Seed Data'}
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" />
              Exportar
            </Button>
            <Button variant="outline" size="sm" onClick={fetchData} disabled={isRefreshing}>
              <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? 'Atualizando...' : 'Atualizar'}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {summary.map((fw) => (
            <Card 
              key={fw.framework}
              className={`cursor-pointer hover:transition-shadow ${frameworkFilter === fw.framework ? 'ring-2 ring-gray-900/20' : ''}`}
              style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}
              onClick={() => setFrameworkFilter(frameworkFilter === fw.framework ? 'all' : fw.framework)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-8 h-8 rounded-md flex items-center justify-center"
                      style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
                    >
                      {fw.icon}
                    </div>
                    <span className="text-sm font-medium text-gray-800 dark:text-gray-100">
                      {fw.name}
                    </span>
                  </div>
                  {getComplianceStatusIcon(fw.compliancePercentage)}
                </div>
                <div className="mb-2">
                  <div className="flex items-baseline gap-1">
                    <span className={`text-2xl font-semibold ${getComplianceStatusColor(fw.compliancePercentage)}`}>
                      {fw.compliancePercentage}%
                    </span>
                  </div>
                  <Progress value={fw.compliancePercentage} className="h-1.5 mt-2" />
                </div>
                <div className="grid grid-cols-2 gap-1 text-micro text-gray-400 dark:text-gray-500">
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-status-success" />
                    <span>{fw.implemented} impl.</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-status-warning" />
                    <span>{fw.partial} parc.</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-status-error" />
                    <span>{fw.pending} pend.</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-gray-400" />
                    <span>{fw.na} N/A</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-3 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Buscar por ID ou requisito..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={frameworkFilter} onValueChange={setFrameworkFilter}>
                <SelectTrigger className="w-full md:w-[160px]">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Framework" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="SOX">SOX</SelectItem>
                  <SelectItem value="SOC2">SOC 2</SelectItem>
                  <SelectItem value="ISO27001">ISO 27001</SelectItem>
                  <SelectItem value="LGPD">LGPD</SelectItem>
                  <SelectItem value="BCB498">BCB 498</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full md:w-[180px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-full md:w-[180px]">
                  <SelectValue placeholder="Categoria" />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORY_OPTIONS.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="rounded-md border overflow-hidden border-gray-200 dark:border-gray-700">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50 dark:bg-gray-800/50">
                    <TableHead className="w-10">
                      <Checkbox
                        checked={selectedItems.size === filteredItems.length && filteredItems.length > 0}
                        onCheckedChange={toggleAllSelection}
                      />
                    </TableHead>
                    <TableHead className="w-28">Req ID</TableHead>
                    <TableHead>Requisito</TableHead>
                    <TableHead className="w-28">Status</TableHead>
                    <TableHead className="w-32">Evidência</TableHead>
                    <TableHead className="w-36">Última Verificação</TableHead>
                    <TableHead className="w-28">Legislação</TableHead>
                    <TableHead className="w-24 text-center">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredItems.length > 0 ? (
                    filteredItems.map((item) => (
                      <TableRow 
                        key={item.id}
                        className="hover:bg-gray-50 dark:hover:bg-gray-800/30"
                      >
                        <TableCell>
                          <Checkbox
                            checked={selectedItems.has(item.id)}
                            onCheckedChange={() => toggleItemSelection(item.id)}
                          />
                        </TableCell>
                        <TableCell className="font-mono text-xs text-gray-400 dark:text-gray-500">
                          {item.reqId}
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="text-sm text-gray-800 dark:text-gray-100">
                              {item.requirement}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant="lilac" className="text-micro">{FRAMEWORK_NAMES[item.framework] || item.framework}</Badge>
                              {item.comment && (
                                <span className="text-micro flex items-center gap-1 text-gray-400 dark:text-gray-500">
                                  <MessageSquare className="w-3 h-3" />
                                  Comentário
                                </span>
                              )}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          {getStatusBadge(item.status)}
                        </TableCell>
                        <TableCell>
                          <span className="text-xs text-gray-400 dark:text-gray-500">
                            {item.evidence || '-'}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="text-xs text-gray-400 dark:text-gray-500">
                            {item.lastVerification 
                              ? new Date(item.lastVerification).toLocaleDateString('pt-BR')
                              : '-'
                            }
                          </span>
                        </TableCell>
                        <TableCell>
                          {item.referenceUrl ? (
                            <a
                              href={item.referenceUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs flex items-center gap-1 text-gray-600 dark:text-gray-400 hover:underline"
                              title={item.referenceLabel || 'Ver legislação'}
                            >
                              <ExternalLink className="w-3 h-3" />
                              <span className="truncate max-w-20">
                                {item.referenceLabel || 'Link'}
                              </span>
                            </a>
                          ) : (
                            <span className="text-xs text-gray-400 dark:text-gray-500">
                              -
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center justify-center gap-1">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleOpenVerifyModal(item)}
                              className="h-8 w-8 p-0"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleOpenVerifyModal(item)}
                              className="h-8 w-8 p-0"
                            >
                              <MessageSquare className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-8">
                        <p className="text-gray-400 dark:text-gray-500">
                          {items.length === 0 
                            ? 'Nenhum requisito cadastrado. Clique em "Seed Data" para carregar dados de demonstração.'
                            : 'Nenhum requisito encontrado com os filtros aplicados.'
                          }
                        </p>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            <div className="mt-3 flex items-center justify-between">
              <span className="text-xs text-gray-400 dark:text-gray-500">
                {selectedItems.size > 0 && (
                  <span className="mr-4">{selectedItems.size} selecionado(s)</span>
                )}
                Exibindo {filteredItems.length} de {items.length} requisitos
              </span>
            </div>
          </CardContent>
        </Card>

        <Dialog open={isVerifyModalOpen} onOpenChange={setIsVerifyModalOpen}>
          <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-base font-semibold text-gray-800 dark:text-gray-100">
                Verificar Requisito
              </DialogTitle>
              <DialogDescription>
                {selectedItem?.reqId} - {selectedItem?.requirement}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="comment">Comentários</Label>
                <Textarea
                  id="comment"
                  placeholder="Adicione observações sobre a verificação..."
                  value={verifyComment}
                  onChange={(e) => setVerifyComment(e.target.value)}
                  rows={4}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="nextReview">Data da Próxima Revisão</Label>
                <Input
                  id="nextReview"
                  type="date"
                  value={verifyNextReviewDate}
                  onChange={(e) => setVerifyNextReviewDate(e.target.value)}
                />
              </div>
              {selectedItem && (
                <div className="p-3 rounded-md bg-gray-100 dark:bg-gray-800">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-400 dark:text-gray-500">Framework:</span>
                      <p className="text-gray-800 dark:text-gray-100">{FRAMEWORK_NAMES[selectedItem.framework]}</p>
                    </div>
                    <div>
                      <span className="text-gray-400 dark:text-gray-500">Status Atual:</span>
                      <div className="mt-1">{getStatusBadge(selectedItem.status)}</div>
                    </div>
                    <div>
                      <span className="text-gray-400 dark:text-gray-500">Evidência:</span>
                      <p className="text-gray-800 dark:text-gray-100">{selectedItem.evidence || 'Não anexada'}</p>
                    </div>
                    <div>
                      <span className="text-gray-400 dark:text-gray-500">Última Verificação:</span>
                      <p className="text-gray-800 dark:text-gray-100">
                        {selectedItem.lastVerification 
                          ? new Date(selectedItem.lastVerification).toLocaleDateString('pt-BR')
                          : 'Nunca verificado'
                        }
                      </p>
                    </div>
                  </div>
                  {selectedItem.referenceUrl && (
                    <div className="mt-3 pt-3 border-t border-gray-300 dark:border-gray-600">
                      <span className="text-gray-400 dark:text-gray-500">Legislação de Referência:</span>
                      <a
                        href={selectedItem.referenceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 mt-1 text-gray-600 dark:text-gray-400 hover:underline text-sm"
                      >
                        <ExternalLink className="w-4 h-4" />
                        {selectedItem.referenceLabel || 'Ver documento oficial'}
                      </a>
                    </div>
                  )}
                  {selectedItem.checklistItems && selectedItem.checklistItems.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-300 dark:border-gray-600">
                      <span className="text-xs font-medium text-gray-400 dark:text-gray-500">
                        Lista de Verificação ({selectedItem.checklistItems.filter(i => i.completed).length}/{selectedItem.checklistItems.length})
                      </span>
                      <div className="mt-2 space-y-2">
                        {selectedItem.checklistItems.map((checkItem, idx) => (
                          <div key={idx} className="flex items-start gap-2">
                            <Checkbox
                              checked={checkItem.completed}
                              className="mt-0.5"
                            />
                            <span
                              className={`text-xs ${checkItem.completed ? 'line-through text-gray-400 dark:text-gray-500' : 'text-gray-800 dark:text-gray-100'}`}
                            >
                              {checkItem.text}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {selectedItem.evidenceDetails && (
                    <div className="mt-3 pt-3 border-t border-gray-300 dark:border-gray-600">
                      <span className="text-xs font-medium text-gray-400 dark:text-gray-500">
                        Documentação Requerida:
                      </span>
                      <pre 
                        className="mt-2 text-xs whitespace-pre-wrap text-gray-500 dark:text-gray-400" style={{ fontFamily: 'inherit' }}
                      >
                        {selectedItem.evidenceDetails}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsVerifyModalOpen(false)}>
                Cancelar
              </Button>
              <Button 
                onClick={handleVerify} 
                disabled={isVerifying}
                className="bg-gray-900" style={{ color: 'white' }}
              >
                {isVerifying ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Verificando...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Confirmar Verificação
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
