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
  Scale,
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
import { complianceService, SOXControl, FrameworkStats } from '@/services/admin/compliance-service'

const ADMIN_CLIENT_ID = 'admin-global'

const SOX_SECTIONS = [
  { id: '302', name: 'Seção 302', description: 'Certificação de Relatórios Financeiros' },
  { id: '404', name: 'Seção 404', description: 'Avaliação de Controles Internos' },
  { id: '409', name: 'Seção 409', description: 'Divulgação em Tempo Real' },
  { id: '802', name: 'Seção 802', description: 'Penalidades Criminais' },
  { id: 'ITGC', name: 'ITGC', description: 'Controles Gerais de TI' }
]

function getTestResultBadge(result: string) {
  switch (result) {
    case 'effective':
      return <Badge variant="success">Efetivo</Badge>
    case 'ineffective':
      return <Badge variant="destructive">Inefetivo</Badge>
    case 'pending':
      return <Badge variant="warning">Pendente</Badge>
    case 'not_tested':
      return <Badge variant="default">Não Testado</Badge>
    default:
      return <Badge variant="default">-</Badge>
  }
}

function getControlTypeBadge(type: string) {
  switch (type) {
    case 'preventive':
      return <Badge variant="info" className="text-micro">Preventivo</Badge>
    case 'detective':
      return <Badge variant="secondary" className="text-micro">Detectivo</Badge>
    case 'corrective':
      return <Badge variant="warning" className="text-micro">Corretivo</Badge>
    default:
      return <Badge variant="default" className="text-micro">{type}</Badge>
  }
}

interface ExpandedSOXControlProps {
  control: SOXControl
}

function ExpandedSOXControl({ control }: ExpandedSOXControlProps) {
  return (
    <div className="p-4 bg-gray-50 dark:bg-lia-bg-secondary/50 border-t border-lia-border-subtle dark:border-lia-border-subtle">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h4 className="text-xs font-semibold mb-2 lia-text-400 dark:lia-text-500">
            DESCRIÇÃO
          </h4>
          <p className="text-sm lia-text-500 dark:text-lia-text-tertiary">
            {control.description || 'Sem descrição disponível.'}
          </p>
        </div>
        <div>
          <h4 className="text-xs font-semibold mb-2 lia-text-400 dark:lia-text-500">
            INFORMAÇÕES DO TESTE
          </h4>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium lia-text-400 dark:lia-text-500">
                Frequência:
              </span>
              <span className="text-sm lia-text-800 dark:text-lia-text-primary">
                {control.frequency || 'Não definida'}
              </span>
            </div>
            {control.testDate && (
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium lia-text-400 dark:lia-text-500">
                  Data do Teste:
                </span>
                <span className="text-sm lia-text-800 dark:text-lia-text-primary">
                  {new Date(control.testDate).toLocaleDateString('pt-BR')}
                </span>
              </div>
            )}
            {control.testerName && (
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium lia-text-400 dark:lia-text-500">
                  Testador:
                </span>
                <span className="text-sm lia-text-800 dark:text-lia-text-primary">
                  {control.testerName}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
      {control.notes && (
        <div className="mt-4 p-3 rounded-md bg-gray-100 dark:bg-lia-bg-secondary">
          <span className="text-xs font-medium lia-text-400 dark:lia-text-500">
            Notas:
          </span>
          <p className="text-sm mt-1 lia-text-500 dark:text-lia-text-tertiary">
            {control.notes}
          </p>
        </div>
      )}
    </div>
  )
}

export default function SOXPage() {
  const [controls, setControls] = useState<SOXControl[]>([])
  const [stats, setStats] = useState<FrameworkStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [testResultFilter, setTestResultFilter] = useState<string>('all')
  const [sectionFilter, setSectionFilter] = useState<string>('all')
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())

  const fetchData = useCallback(async () => {
    setIsRefreshing(true)
    try {
      const [soxData, dashboardData] = await Promise.all([
        complianceService.getSOXControls(ADMIN_CLIENT_ID),
        complianceService.getDashboard(ADMIN_CLIENT_ID)
      ])
      setControls(soxData.controls)
      setStats(dashboardData.byFramework?.['SOX'] || null)
    } catch (err) {
      toast.error('Erro ao carregar controles SOX')
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

  const soxSummary = controls.reduce((acc, control) => {
    acc[control.testResult] = (acc[control.testResult] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const filteredControls = controls.filter(control => {
    const matchesSearch = searchTerm === '' || 
      control.controlId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      control.controlName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (control.description?.toLowerCase().includes(searchTerm.toLowerCase()))

    const matchesTestResult = testResultFilter === 'all' || control.testResult === testResultFilter
    const matchesSection = sectionFilter === 'all' || control.section === sectionFilter

    return matchesSearch && matchesTestResult && matchesSection
  })

  if (isLoading) {
    return (
      <div className="p-6" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="max-w-7xl mx-auto flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none lia-text-600 dark:text-lia-text-tertiary" />
          <span className="ml-3 text-sm lia-text-400 dark:lia-text-500">
            Carregando controles SOX...
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
              <Scale className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold lia-text-800 dark:text-lia-text-primary"
              >
                Controles SOX
              </h1>
              <p className="text-sm lia-text-400 dark:lia-text-500">
                Sarbanes-Oxley - Controles financeiros e de TI
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={fetchData} disabled={isRefreshing}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin motion-reduce:animate-none' : ''}`} />
            {isRefreshing ? 'Atualizando...' : 'Atualizar'}
          </Button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {SOX_SECTIONS.map(section => (
            <Card 
              key={section.id} 
              className={`cursor-pointer hover:transition-shadow ${sectionFilter === section.id ? 'ring-2 ring-gray-900/20' : ''}`}
              
              onClick={() => setSectionFilter(sectionFilter === section.id ? 'all' : section.id)}
            >
              <CardContent className="p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="lilac" className="text-micro">{section.id}</Badge>
                </div>
                <p className="text-xs font-medium lia-text-800 dark:text-lia-text-primary">
                  {section.name}
                </p>
                <p className="text-micro lia-text-400 dark:lia-text-500">
                  {section.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card >
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                Resumo de Testes
              </span>
              <span className="text-sm font-semibold lia-text-800 dark:text-lia-text-primary">
                {controls.length} controles
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-status-success" />
                <span className="text-xs lia-text-500 dark:text-lia-text-tertiary">
                  {soxSummary.effective || 0} Efetivos
                </span>
              </div>
              <div className="flex items-center gap-2">
                <XCircle className="w-4 h-4 text-status-error" />
                <span className="text-xs lia-text-500 dark:text-lia-text-tertiary">
                  {soxSummary.ineffective || 0} Inefetivos
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-status-warning" />
                <span className="text-xs lia-text-500 dark:text-lia-text-tertiary">
                  {soxSummary.pending || 0} Pendentes
                </span>
              </div>
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 lia-text-400" />
                <span className="text-xs lia-text-500 dark:text-lia-text-tertiary">
                  {soxSummary.not_tested || 0} Não Testados
                </span>
              </div>
            </div>
            {stats && (
              <div className="mt-3">
                <Progress value={stats.compliancePercentage} className="h-2" />
                <p className="text-xs mt-1 lia-text-400 dark:lia-text-500">
                  {Math.round(stats.compliancePercentage)}% de conformidade
                </p>
              </div>
            )}
          </CardContent>
        </Card>

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
              <Select value={testResultFilter} onValueChange={setTestResultFilter}>
                <SelectTrigger className="w-full md:w-[180px]">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Resultado" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os Resultados</SelectItem>
                  <SelectItem value="effective">Efetivo</SelectItem>
                  <SelectItem value="ineffective">Inefetivo</SelectItem>
                  <SelectItem value="pending">Pendente</SelectItem>
                  <SelectItem value="not_tested">Não Testado</SelectItem>
                </SelectContent>
              </Select>
              <Select value={sectionFilter} onValueChange={setSectionFilter}>
                <SelectTrigger className="w-full md:w-[160px]">
                  <SelectValue placeholder="Seção" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas as Seções</SelectItem>
                  {SOX_SECTIONS.map(section => (
                    <SelectItem key={section.id} value={section.id}>{section.name}</SelectItem>
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
                    <TableHead className="w-24">Seção</TableHead>
                    <TableHead className="w-28">Tipo</TableHead>
                    <TableHead className="w-28">Frequência</TableHead>
                    <TableHead className="w-32">Resultado</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredControls.length > 0 ? (
                    filteredControls.map((control) => {
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
                              <Badge variant="lilac" className="text-micro">
                                {control.section}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {getControlTypeBadge(control.controlType)}
                            </TableCell>
                            <TableCell>
                              <span className="text-xs lia-text-400 dark:lia-text-500">
                                {control.frequency || '-'}
                              </span>
                            </TableCell>
                            <TableCell>
                              {getTestResultBadge(control.testResult)}
                            </TableCell>
                          </TableRow>
                          {isExpanded && (
                            <TableRow>
                              <TableCell colSpan={7} className="p-0">
                                <ExpandedSOXControl control={control} />
                              </TableCell>
                            </TableRow>
                          )}
                        </React.Fragment>
                      )
                    })
                  ) : (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8">
                        <p className="lia-text-400 dark:lia-text-500" aria-live="polite" aria-atomic="true">
                          {controls.length === 0 
                            ? 'Nenhum controle SOX configurado.' 
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
