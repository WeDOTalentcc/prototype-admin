"use client"

import React, { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
  Shield,
  ChevronLeft,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Loader2,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle
} from "lucide-react"
import { toast } from "sonner"
import { complianceService, ControlLibrary, CompanyControl, FrameworkStats } from '@/services/admin/compliance-service'

const ADMIN_CLIENT_ID = 'admin-global'
const FRAMEWORK_KEY = 'SOC2'

interface ExpandedControlProps {
  control: ControlLibrary
  companyControl?: CompanyControl
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'implemented':
    case 'verified':
      return <Badge variant="success">Implementado</Badge>
    case 'in_progress':
      return <Badge variant="warning">Em Progresso</Badge>
    case 'not_started':
      return <Badge variant="destructive">Não Iniciado</Badge>
    case 'not_applicable':
      return <Badge variant="default">N/A</Badge>
    default:
      return <Badge variant="default">-</Badge>
  }
}

function ExpandedControl({ control, companyControl }: ExpandedControlProps) {
  return (
    <div className="p-4 bg-gray-50 dark:bg-lia-bg-secondary/50 border-t border-lia-border-subtle dark:border-lia-border-subtle">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h4 className="text-xs font-semibold mb-2 lia-text-400 dark:lia-text-500">
            DESCRIÇÃO
          </h4>
          <p className="text-sm lia-text-500 dark:text-lia-text-tertiary">
            {control.controlDescription || 'Sem descrição disponível.'}
          </p>
        </div>
        <div>
          <h4 className="text-xs font-semibold mb-2 lia-text-400 dark:lia-text-500">
            ORIENTAÇÃO DE IMPLEMENTAÇÃO
          </h4>
          <p className="text-sm lia-text-500 dark:text-lia-text-tertiary">
            {control.implementationGuidance || 'Sem orientação disponível.'}
          </p>
        </div>
      </div>
      {control.evidenceRequirements && control.evidenceRequirements.length > 0 && (
        <div className="mt-4">
          <h4 className="text-xs font-semibold mb-2 lia-text-400 dark:lia-text-500">
            REQUISITOS DE EVIDÊNCIA
          </h4>
          <ul className="list-disc list-inside text-sm space-y-1 lia-text-500 dark:text-lia-text-tertiary">
            {control.evidenceRequirements.map((req, idx) => (
              <li key={idx}>{req}</li>
            ))}
          </ul>
        </div>
      )}
      {companyControl && (
        <div className="mt-4 p-3 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-medium lia-text-400 dark:lia-text-500">
                Responsável:
              </span>
              <span className="text-sm ml-2 lia-text-800 dark:text-lia-text-primary">
                {companyControl.ownerName || 'Não atribuído'}
              </span>
            </div>
            {companyControl.nextReviewDate && (
              <div>
                <span className="text-xs font-medium lia-text-400 dark:lia-text-500">
                  Próxima Revisão:
                </span>
                <span className="text-sm ml-2 lia-text-800 dark:text-lia-text-primary">
                  {new Date(companyControl.nextReviewDate).toLocaleDateString('pt-BR')}
                </span>
              </div>
            )}
          </div>
          {companyControl.notes && (
            <div className="mt-2">
              <span className="text-xs font-medium lia-text-400 dark:lia-text-500">
                Notas:
              </span>
              <p className="text-sm mt-1 lia-text-500 dark:text-lia-text-tertiary">
                {companyControl.notes}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const TSC_CATEGORIES = [
  { id: 'CC', name: 'Common Criteria (CC)', description: 'Critérios comuns de segurança' },
  { id: 'A', name: 'Availability (A)', description: 'Disponibilidade' },
  { id: 'C', name: 'Confidentiality (C)', description: 'Confidencialidade' },
  { id: 'PI', name: 'Processing Integrity (PI)', description: 'Integridade de Processamento' },
  { id: 'P', name: 'Privacy (P)', description: 'Privacidade' }
]

export default function SOC2Page() {
  const [controls, setControls] = useState<ControlLibrary[]>([])
  const [companyControls, setCompanyControls] = useState<CompanyControl[]>([])
  const [stats, setStats] = useState<FrameworkStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  const fetchData = useCallback(async () => {
    setIsRefreshing(true)
    try {
      const [controlsData, companyData, dashboardData] = await Promise.all([
        complianceService.getControlLibrary({ framework: FRAMEWORK_KEY, limit: 200 }),
        complianceService.getCompanyControls(ADMIN_CLIENT_ID, { framework: FRAMEWORK_KEY, limit: 200 }),
        complianceService.getDashboard(ADMIN_CLIENT_ID)
      ])
      setControls(controlsData.controls)
      setCompanyControls(companyData.controls)
      setStats(dashboardData.byFramework?.[FRAMEWORK_KEY] || null)
    } catch (err) {
      toast.error('Erro ao carregar controles SOC 2')
    } finally {
      setIsRefreshing(false)
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const toggleRow = (id: string) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }

  const getCompanyControlForLibrary = (libraryId: string): CompanyControl | undefined => {
    return companyControls.find(cc => cc.controlLibraryId === libraryId)
  }

  const categories = [...new Set(controls.map(c => c.controlCategory).filter(Boolean))]

  const filteredControls = controls.filter(control => {
    const companyControl = getCompanyControlForLibrary(control.id)
    const status = companyControl?.status || 'not_started'
    
    const matchesSearch = searchTerm === '' || 
      control.controlId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      control.controlName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (control.controlDescription?.toLowerCase().includes(searchTerm.toLowerCase()))

    const matchesStatus = statusFilter === 'all' || status === statusFilter
    const matchesCategory = categoryFilter === 'all' || control.controlCategory === categoryFilter

    return matchesSearch && matchesStatus && matchesCategory
  })

  if (isLoading) {
    return (
      <div className="p-6" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="max-w-7xl mx-auto flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none lia-text-600 dark:text-lia-text-tertiary" />
          <span className="ml-3 text-sm lia-text-400 dark:lia-text-500">
            Carregando controles SOC 2...
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
            <Link href="/admin/compliance/controles">
              <Button variant="ghost" size="sm">
                <ChevronLeft className="w-4 h-4 mr-1" />
                Voltar
              </Button>
            </Link>
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30"
            >
              <Shield className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold lia-text-800 dark:text-lia-text-primary"
              >
                Controles SOC 2 Type II
              </h1>
              <p className="text-sm lia-text-400 dark:lia-text-500">
                Trust Service Criteria - Segurança, Disponibilidade, Confidencialidade
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={fetchData} disabled={isRefreshing}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin motion-reduce:animate-none' : ''}`} />
            {isRefreshing ? 'Atualizando...' : 'Atualizar'}
          </Button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {TSC_CATEGORIES.map(tsc => (
            <Card key={tsc.id} className="cursor-pointer hover:transition-shadow" >
              <CardContent className="p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="info" className="text-micro">{tsc.id}</Badge>
                  <span className="text-xs font-medium truncate lia-text-800 dark:text-lia-text-primary">
                    {tsc.name}
                  </span>
                </div>
                <p className="text-micro lia-text-400 dark:lia-text-500">
                  {tsc.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {stats && (
          <Card >
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                  Progresso de Conformidade
                </span>
                <span className="text-sm font-semibold lia-text-800 dark:text-lia-text-primary">
                  {Math.round(stats.compliancePercentage)}%
                </span>
              </div>
              <Progress value={stats.compliancePercentage} className="h-2 mb-3" />
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-status-success" />
                  <span className="text-xs lia-text-500 dark:text-lia-text-tertiary">
                    {stats.implemented + stats.verified} Implementados
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-status-warning" />
                  <span className="text-xs lia-text-500 dark:text-lia-text-tertiary">
                    {stats.inProgress} Em Progresso
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-wedo-orange" />
                  <span className="text-xs lia-text-500 dark:text-lia-text-tertiary">
                    {stats.notStarted} Não Iniciados
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <XCircle className="w-4 h-4 lia-text-400" />
                  <span className="text-xs lia-text-500 dark:text-lia-text-tertiary">
                    {stats.notApplicable} N/A
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium lia-text-400 dark:lia-text-500">
                    Total: {stats.totalControls} controles
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Card >
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-3 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 lia-text-400" />
                <Input
                  placeholder="Buscar por ID ou nome do controle..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full md:w-[180px]">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os Status</SelectItem>
                  <SelectItem value="implemented">Implementado</SelectItem>
                  <SelectItem value="verified">Verificado</SelectItem>
                  <SelectItem value="in_progress">Em Progresso</SelectItem>
                  <SelectItem value="not_started">Não Iniciado</SelectItem>
                  <SelectItem value="not_applicable">N/A</SelectItem>
                </SelectContent>
              </Select>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-full md:w-sidebar-content">
                  <SelectValue placeholder="Categoria" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas as Categorias</SelectItem>
                  {categories.map(cat => (
                    <SelectItem key={cat} value={cat!}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="rounded-md border overflow-hidden border-lia-border-subtle dark:border-lia-border-subtle">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50 dark:bg-lia-bg-secondary/50">
                    <TableHead className="w-10"></TableHead>
                    <TableHead className="w-28">ID</TableHead>
                    <TableHead>Nome do Controle</TableHead>
                    <TableHead className="w-40">TSC</TableHead>
                    <TableHead className="w-32">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredControls.length > 0 ? (
                    filteredControls.map((control) => {
                      const companyControl = getCompanyControlForLibrary(control.id)
                      const isExpanded = expandedRows.has(control.id)
                      return (
                        <React.Fragment key={control.id}>
                          <TableRow 
                            className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/30"
                            onClick={() => toggleRow(control.id)}
                          >
                            <TableCell>
                              {isExpanded ? (
                                <ChevronDown className="w-4 h-4 lia-text-400" />
                              ) : (
                                <ChevronRight className="w-4 h-4 lia-text-400" />
                              )}
                            </TableCell>
                            <TableCell className="font-mono text-xs lia-text-400 dark:lia-text-500">
                              {control.controlId}
                            </TableCell>
                            <TableCell className="lia-text-800 dark:text-lia-text-primary">
                              {control.controlName}
                            </TableCell>
                            <TableCell>
                              <Badge variant="info" className="text-micro">
                                {control.controlCategory || 'CC'}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {getStatusBadge(companyControl?.status || 'not_started')}
                            </TableCell>
                          </TableRow>
                          {isExpanded && (
                            <TableRow>
                              <TableCell colSpan={5} className="p-0">
                                <ExpandedControl control={control} companyControl={companyControl} />
                              </TableCell>
                            </TableRow>
                          )}
                        </React.Fragment>
                      )
                    })
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8">
                        <p className="lia-text-400 dark:lia-text-500" aria-live="polite" aria-atomic="true">
                          {controls.length === 0 
                            ? 'Nenhum controle SOC 2 configurado.' 
                            : 'Nenhum controle encontrado com os filtros aplicados.'
                          }
                        </p>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            <div className="mt-3 text-xs text-right lia-text-400 dark:lia-text-500">
              Exibindo {filteredControls.length} de {controls.length} controles
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
