"use client"

import React, { useState } from "react"
import { 
  FileWarning, 
  Search, 
  Plus, 
  Filter,
  MoreHorizontal,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowUpDown,
  ShieldCheck,
  XCircle,
  ArrowRightLeft,
  Calendar
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const risks = [
  { 
    id: 'RISK-001', 
    description: 'Vazamento de dados pessoais de candidatos por falha de segurança ou acesso não autorizado', 
    category: 'Segurança', 
    probability: 'medium', 
    impact: 'critical', 
    score: 15, 
    treatment: 'mitigate',
    status: 'in_treatment', 
    owner: 'CISO',
    identifiedDate: '2024-08-15'
  },
  { 
    id: 'RISK-002', 
    description: 'Viés algorítmico em seleção de candidatos gerando discriminação não intencional', 
    category: 'Compliance', 
    probability: 'medium', 
    impact: 'high', 
    score: 12, 
    treatment: 'mitigate',
    status: 'in_treatment', 
    owner: 'Data Science',
    identifiedDate: '2024-09-01'
  },
  { 
    id: 'RISK-003', 
    description: 'Indisponibilidade da plataforma LIA impactando processos seletivos em andamento', 
    category: 'Operacional', 
    probability: 'low', 
    impact: 'high', 
    score: 10, 
    treatment: 'mitigate',
    status: 'closed', 
    owner: 'Infra',
    identifiedDate: '2024-07-20'
  },
  { 
    id: 'RISK-004', 
    description: 'Não conformidade com LGPD em coleta e tratamento de dados de candidatos', 
    category: 'Legal', 
    probability: 'low', 
    impact: 'critical', 
    score: 12, 
    treatment: 'mitigate',
    status: 'closed', 
    owner: 'DPO',
    identifiedDate: '2024-06-10'
  },
  { 
    id: 'RISK-005', 
    description: 'Falha em integração com ATS externos causando perda de sincronização de dados', 
    category: 'Operacional', 
    probability: 'medium', 
    impact: 'medium', 
    score: 9, 
    treatment: 'accept',
    status: 'closed', 
    owner: 'Produto',
    identifiedDate: '2024-10-05'
  },
  { 
    id: 'RISK-006', 
    description: 'Acesso não autorizado a CVs e perfis de candidatos por falha de controle de acesso', 
    category: 'Privacidade', 
    probability: 'low', 
    impact: 'high', 
    score: 8, 
    treatment: 'mitigate',
    status: 'closed', 
    owner: 'Segurança',
    identifiedDate: '2024-11-01'
  },
  { 
    id: 'RISK-007', 
    description: 'Perda de dados por falha de backup ou corrupção de dados', 
    category: 'Operacional', 
    probability: 'low', 
    impact: 'critical', 
    score: 8, 
    treatment: 'transfer',
    status: 'closed', 
    owner: 'Infra',
    identifiedDate: '2024-09-15'
  },
  { 
    id: 'RISK-008', 
    description: 'Fraude em processos seletivos por candidatos ou colaboradores internos', 
    category: 'Financeiro', 
    probability: 'low', 
    impact: 'medium', 
    score: 6, 
    treatment: 'accept',
    status: 'open', 
    owner: 'Compliance',
    identifiedDate: '2024-12-01'
  },
]

const getScoreColor = (score: number) => {
  if (score >= 15) return { bg: 'var(--status-error-bg)', text: 'var(--status-error)', label: 'Crítico' }
  if (score >= 10) return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning)', label: 'Alto' }
  if (score >= 5) return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning)', label: 'Médio' }
  return { bg: 'var(--status-success-bg)', text: 'var(--status-success)', label: 'Baixo' }
}

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'open':
      return { icon: AlertTriangle, color: 'text-status-error', bg: 'bg-status-error/15', label: 'Aberto' }
    case 'in_treatment':
      return { icon: Clock, color: 'text-status-warning', bg: 'bg-status-warning/15', label: 'Em Tratamento' }
    case 'closed':
      return { icon: CheckCircle2, color: 'text-status-success', bg: 'bg-status-success/15', label: 'Fechado' }
    default:
      return { icon: Clock, color: 'text-lia-text-secondary', bg: 'bg-lia-bg-tertiary', label: status }
  }
}

const getTreatmentConfig = (treatment: string) => {
  switch (treatment) {
    case 'mitigate':
      return { icon: ShieldCheck, color: 'lia-text-600 dark:text-lia-text-tertiary', bg: 'bg-lia-bg-secondary dark:bg-lia-bg-secondary/50', label: 'Mitigar' }
    case 'accept':
      return { icon: CheckCircle2, color: 'text-status-success', bg: 'bg-status-success/10', label: 'Aceitar' }
    case 'transfer':
      return { icon: ArrowRightLeft, color: 'text-wedo-purple', bg: 'bg-wedo-purple/10', label: 'Transferir' }
    case 'avoid':
      return { icon: XCircle, color: 'text-status-error', bg: 'bg-status-error/10', label: 'Evitar' }
    default:
      return { icon: Clock, color: 'text-lia-text-secondary', bg: 'bg-lia-bg-secondary', label: treatment }
  }
}

const getProbabilityLabel = (value: string) => {
  const labels: Record<string, string> = { 'very_low': 'Muito Baixa', 'low': 'Baixa', 'medium': 'Média', 'high': 'Alta', 'very_high': 'Muito Alta' }
  return labels[value] || value
}

const getImpactLabel = (value: string) => {
  const labels: Record<string, string> = { 'minimal': 'Mínimo', 'low': 'Baixo', 'medium': 'Médio', 'high': 'Alto', 'critical': 'Crítico' }
  return labels[value] || value
}

const getProbabilityColor = (value: string) => {
  if (value === 'high' || value === 'very_high') return 'text-status-error bg-status-error/10'
  if (value === 'medium') return 'text-status-warning bg-status-warning/10'
  return 'text-status-success bg-status-success/10'
}

const getImpactColor = (value: string) => {
  if (value === 'high' || value === 'critical') return 'text-status-error bg-status-error/10'
  if (value === 'medium') return 'text-status-warning bg-status-warning/10'
  return 'text-status-success bg-status-success/10'
}

const getCategoryColor = (category: string) => {
  const colors: Record<string, string> = {
    'Segurança': 'bg-status-error/15 text-status-error',
    'Operacional': 'bg-status-warning/15 text-status-warning',
    'Compliance': 'bg-wedo-purple/15 text-wedo-purple',
    'Privacidade': 'bg-wedo-purple/15 text-wedo-purple',
    'Legal': 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary',
    'Financeiro': 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary',
  }
  return colors[category] || 'bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary'
}

export default function RiskRegisterPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  const filteredRisks = risks.filter(risk => {
    const matchesSearch = risk.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      risk.id.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = categoryFilter === 'all' || risk.category === categoryFilter
    const matchesStatus = statusFilter === 'all' || risk.status === statusFilter
    return matchesSearch && matchesCategory && matchesStatus
  })

  const criticalCount = risks.filter(r => r.score >= 12).length
  const closedCount = risks.filter(r => r.status === 'closed').length
  const inTreatmentCount = risks.filter(r => r.status === 'in_treatment').length
  const openCount = risks.filter(r => r.status === 'open').length

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30"
            >
              <FileWarning className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary"
                
              >
                Risk Register (ISMS)
              </h1>
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                Registro de riscos do Sistema de Gestão de Segurança da Informação
              </p>
            </div>
          </div>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Novo Risco
          </Button>
        </div>

        <Card className="mb-6" style={{borderLeft: '4px solid var(--status-error)'}}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-status-error mt-0.5" />
              <div>
                <p className="font-medium text-sm text-status-error">
                  Gap de Compliance - ISO 27001
                </p>
                <p className="text-sm mt-1 text-lia-text-secondary dark:text-lia-text-tertiary" >
                  O registro de riscos é um requisito crítico da norma ISO 27001. Mantenha este registro 
                  atualizado com avaliações periódicas de probabilidade e impacto para garantir conformidade 
                  com o Sistema de Gestão de Segurança da Informação (SGSI).
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                  <FileWarning className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
                <div>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary" >{risks.length}</p>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Total de Riscos</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-red-500/10">
                  <AlertTriangle className="w-5 h-5 text-status-error" />
                </div>
                <div>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary" >{criticalCount}</p>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Riscos Críticos</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-status-warning-bg">
                  <Clock className="w-5 h-5 text-status-warning" />
                </div>
                <div>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary" >{inTreatmentCount}</p>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Em Tratamento</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-green-500/10">
                  <CheckCircle2 className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary" >{closedCount}</p>
                  <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Fechados</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        <Card >
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
                Registro de Riscos
              </CardTitle>
              <div className="flex items-center gap-2 flex-wrap">
                <div className="relative w-64">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                  <Input
                    placeholder="Buscar riscos..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Categoria" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas</SelectItem>
                    <SelectItem value="Segurança">Segurança</SelectItem>
                    <SelectItem value="Privacidade">Privacidade</SelectItem>
                    <SelectItem value="Operacional">Operacional</SelectItem>
                    <SelectItem value="Financeiro">Financeiro</SelectItem>
                    <SelectItem value="Legal">Legal</SelectItem>
                    <SelectItem value="Compliance">Compliance</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos</SelectItem>
                    <SelectItem value="open">Aberto</SelectItem>
                    <SelectItem value="in_treatment">Em Tratamento</SelectItem>
                    <SelectItem value="closed">Fechado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[100px]">ID</TableHead>
                    <TableHead className="min-w-[250px]">Descrição</TableHead>
                    <TableHead>Categoria</TableHead>
                    <TableHead className="text-center">Probabilidade</TableHead>
                    <TableHead className="text-center">Impacto</TableHead>
                    <TableHead className="text-center">Score</TableHead>
                    <TableHead>Tratamento</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Responsável</TableHead>
                    <TableHead>Identificado</TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRisks.map((risk) => {
                    const scoreConfig = getScoreColor(risk.score)
                    const statusConfig = getStatusConfig(risk.status)
                    const treatmentConfig = getTreatmentConfig(risk.treatment)
                    const StatusIcon = statusConfig.icon
                    const TreatmentIcon = treatmentConfig.icon
                    return (
                      <TableRow key={risk.id}>
                        <TableCell>
                          <Badge variant="outline" className="font-mono text-xs">
                            {risk.id}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-lia-text-primary dark:text-lia-text-primary" >
                            {risk.description}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge className={`text-xs ${getCategoryColor(risk.category)}`}>
                            {risk.category}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="secondary" className={`text-xs ${getProbabilityColor(risk.probability)}`}>
                            {getProbabilityLabel(risk.probability)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="secondary" className={`text-xs ${getImpactColor(risk.impact)}`}>
                            {getImpactLabel(risk.impact)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <span 
                            className="text-sm font-bold px-2 py-1 rounded-md"
                            style={{backgroundColor: scoreConfig.bg, color: scoreConfig.text}}
                          >
                            {risk.score}
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium ${treatmentConfig.bg} ${treatmentConfig.color}`}>
                            <TreatmentIcon className="w-3 h-3" />
                            {treatmentConfig.label}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bg} ${statusConfig.color}`}>
                            <StatusIcon className="w-3 h-3" />
                            {statusConfig.label}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary" >
                            {risk.owner}
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1 text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                            <Calendar className="w-3 h-3" />
                            {new Date(risk.identifiedDate).toLocaleDateString('pt-BR')}
                          </div>
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreHorizontal className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem>Ver detalhes</DropdownMenuItem>
                              <DropdownMenuItem>Editar risco</DropdownMenuItem>
                              <DropdownMenuItem>Atualizar status</DropdownMenuItem>
                              <DropdownMenuItem className="text-status-error">Arquivar</DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
