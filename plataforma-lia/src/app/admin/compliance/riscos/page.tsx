"use client"

import React from "react"
import Link from "next/link"
import { 
  AlertTriangle, 
  AlertCircle, 
  Clock, 
  TrendingUp, 
  ArrowRight,
  FileWarning,
  RefreshCw,
  Truck,
  ShieldPlus,
  BarChart3,
  Calendar,
  CheckCircle2
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

const risks = [
  { id: 'RISK-001', name: 'Vazamento de dados pessoais de candidatos', category: 'Segurança', probability: 'medium', impact: 'critical', score: 15, status: 'mitigating', owner: 'CISO', identifiedDate: '2024-08-15' },
  { id: 'RISK-002', name: 'Viés algorítmico em seleção de candidatos', category: 'Compliance', probability: 'medium', impact: 'high', score: 12, status: 'mitigating', owner: 'Data Science', identifiedDate: '2024-09-01' },
  { id: 'RISK-003', name: 'Indisponibilidade da plataforma LIA', category: 'Operacional', probability: 'low', impact: 'high', score: 10, status: 'mitigated', owner: 'Infra', identifiedDate: '2024-07-20' },
  { id: 'RISK-004', name: 'Não conformidade com LGPD', category: 'Legal', probability: 'low', impact: 'critical', score: 12, status: 'mitigated', owner: 'DPO', identifiedDate: '2024-06-10' },
  { id: 'RISK-005', name: 'Falha em integração com ATS externos', category: 'Operacional', probability: 'medium', impact: 'medium', score: 9, status: 'accepted', owner: 'Produto', identifiedDate: '2024-10-05' },
  { id: 'RISK-006', name: 'Acesso não autorizado a CVs e perfis', category: 'Privacidade', probability: 'low', impact: 'high', score: 8, status: 'mitigated', owner: 'Segurança', identifiedDate: '2024-11-01' },
  { id: 'RISK-007', name: 'Perda de dados por falha de backup', category: 'Operacional', probability: 'low', impact: 'critical', score: 8, status: 'mitigated', owner: 'Infra', identifiedDate: '2024-09-15' },
  { id: 'RISK-008', name: 'Fraude em processos seletivos', category: 'Financeiro', probability: 'low', impact: 'medium', score: 6, status: 'accepted', owner: 'Compliance', identifiedDate: '2024-12-01' },
]

const insuranceCoverage = 'R$ 5.000.000,00'

const riskStats = {
  total: risks.length,
  critical: risks.filter(r => r.score >= 12).length,
  high: risks.filter(r => r.score >= 8 && r.score < 12).length,
  mitigated: risks.filter(r => r.status === 'mitigated').length,
  lastAssessment: '2025-01-10',
  insuranceCoverage: insuranceCoverage
}

const risksByCategory = [
  { category: 'Segurança', count: risks.filter(r => r.category === 'Segurança').length, color: 'var(--status-error)' },
  { category: 'Operacional', count: risks.filter(r => r.category === 'Operacional').length, color: 'var(--status-warning)' },
  { category: 'Compliance', count: risks.filter(r => r.category === 'Compliance').length, color: 'var(--status-warning)' },
  { category: 'Privacidade', count: risks.filter(r => r.category === 'Privacidade').length, color: 'var(--wedo-purple)' },
  { category: 'Legal', count: risks.filter(r => r.category === 'Legal').length },
  { category: 'Financeiro', count: risks.filter(r => r.category === 'Financeiro').length, color: 'var(--wedo-cyan)' },
]

const riskMatrix = [
  { probability: 'Muito Alta', impacts: [5, 10, 15, 20, 25] },
  { probability: 'Alta', impacts: [4, 8, 12, 16, 20] },
  { probability: 'Média', impacts: [3, 6, 9, 12, 15] },
  { probability: 'Baixa', impacts: [2, 4, 6, 8, 10] },
  { probability: 'Muito Baixa', impacts: [1, 2, 3, 4, 5] },
]

const getMatrixCellColor = (value: number) => {
  if (value >= 15) return { bg: 'var(--status-error)', text: 'white' }
  if (value >= 10) return { bg: 'var(--status-warning)', text: 'white' }
  if (value >= 5) return { bg: 'var(--status-warning)', text: 'white' }
  return { bg: 'var(--status-success)', text: 'white' }
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'mitigating': return 'Em Mitigação'
    case 'mitigated': return 'Mitigado'
    case 'accepted': return 'Aceito'
    case 'transferred': return 'Transferido'
    case 'open': return 'Aberto'
    default: return status
  }
}

const top5CriticalRisks = [...risks].sort((a, b) => b.score - a.score).slice(0, 5)

const subpages = [
  { 
    name: 'Risk Register (ISMS)', 
    href: '/admin/compliance/riscos/registro', 
    icon: FileWarning,
    description: 'Registro de riscos do SGSI',
    count: risks.length
  },
  { 
    name: 'Continuidade de Negócios', 
    href: '/admin/compliance/riscos/continuidade', 
    icon: RefreshCw,
    description: 'PCN, RTO/RPO e testes DR',
    count: 3
  },
  { 
    name: 'Due Diligence Fornecedores', 
    href: '/admin/compliance/riscos/fornecedores', 
    icon: Truck,
    description: 'Avaliação de terceiros',
    count: 6
  },
  { 
    name: 'Seguro Cibernético', 
    href: '/admin/compliance/riscos/seguro', 
    icon: ShieldPlus,
    description: 'BCB 498 - Apólice e coberturas',
    status: 'Ativo'
  },
]

const getScoreColor = (score: number) => {
  if (score >= 12) return { bg: 'var(--status-error-bg)', text: 'var(--status-error)', label: 'Crítico' }
  if (score >= 8) return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning)', label: 'Alto' }
  if (score >= 4) return { bg: 'var(--status-warning-bg)', text: 'var(--status-warning)', label: 'Médio' }
  return { bg: 'var(--status-success-bg)', text: 'var(--status-success)', label: 'Baixo' }
}


export default function RiscosPage() {
  const totalRisks = risksByCategory.reduce((acc, r) => acc + r.count, 0)

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <div 
            className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30"
          >
            <AlertTriangle className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </div>
          <div>
            <h1 
              className="text-xl font-semibold text-gray-800 dark:text-gray-100"
              
            >
              Gestão de Riscos
            </h1>
            <p className="text-sm text-gray-400 dark:text-gray-500" >
              Dashboard de riscos, continuidade e seguro cibernético
            </p>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-400 dark:text-gray-500" >
                    Total de Riscos
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-gray-800 dark:text-gray-100" >
                    {riskStats.total}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <TrendingUp className="w-3 h-3 text-status-warning" />
                    <span className="text-xs text-status-warning">+2 este mês</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30">
                  <FileWarning className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-400 dark:text-gray-500" >
                    Riscos Críticos
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-gray-800 dark:text-gray-100" >
                    {riskStats.critical}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="destructive" className="text-micro">
                      Score ≥12
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-red-500/10">
                  <AlertCircle className="w-5 h-5 text-status-error" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-400 dark:text-gray-500" >
                    Riscos em Tratamento
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-gray-800 dark:text-gray-100" >
                    {risks.filter(r => r.status === 'mitigating').length}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className="text-micro bg-status-warning/15 text-status-warning hover:bg-status-warning/15">
                      <Clock className="w-3 h-3 mr-1" />
                      Ação em curso
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-status-warning-bg">
                  <Clock className="w-5 h-5 text-status-warning" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-400 dark:text-gray-500" >
                    Taxa de Mitigação
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-gray-800 dark:text-gray-100" >
                    {Math.round((riskStats.mitigated / riskStats.total) * 100)}%
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className="text-micro bg-status-success/15 text-status-success hover:bg-status-success/15">
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      {riskStats.mitigated} mitigados
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-green-500/10">
                  <CheckCircle2 className="w-5 h-5 text-status-success" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <Card className="lg:col-span-1" >
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <CardTitle className="text-base font-medium text-gray-800 dark:text-gray-100" >
                  Riscos por Categoria
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {risksByCategory.filter(c => c.count > 0).map((category) => (
                  <div key={category.category}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-500 dark:text-gray-400" >
                        {category.category}
                      </span>
                      <span className="text-sm font-medium text-gray-800 dark:text-gray-100" >
                        {category.count}
                      </span>
                    </div>
                    <div className="h-2 rounded-full overflow-hidden bg-gray-50 dark:bg-gray-900" >
                      <div 
                        className="h-full rounded-full transition-all"
                        style={{width: `${(category.count / totalRisks) * 100}%`,
                          backgroundColor: category.color}}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700" >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-100" >
                    Cobertura de Seguro
                  </span>
                  <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">
                    {insuranceCoverage}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2" >
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <CardTitle className="text-base font-medium text-gray-800 dark:text-gray-100" >
                  Matriz de Riscos (Probabilidade x Impacto)
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr>
                      <th className="w-24 text-left p-1 text-gray-400 dark:text-gray-500" >Prob/Impacto</th>
                      <th className="text-center p-1 text-gray-400 dark:text-gray-500" >Mín</th>
                      <th className="text-center p-1 text-gray-400 dark:text-gray-500" >Baixo</th>
                      <th className="text-center p-1 text-gray-400 dark:text-gray-500" >Médio</th>
                      <th className="text-center p-1 text-gray-400 dark:text-gray-500" >Alto</th>
                      <th className="text-center p-1 text-gray-400 dark:text-gray-500" >Crítico</th>
                    </tr>
                  </thead>
                  <tbody>
                    {riskMatrix.map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        <td className="p-1 font-medium text-gray-500 dark:text-gray-400" >{row.probability}</td>
                        {row.impacts.map((value, colIndex) => {
                          const cellColor = getMatrixCellColor(value)
                          return (
                            <td key={colIndex} className="p-1">
                              <div 
                                className="w-8 h-8 rounded-md flex items-center justify-center mx-auto text-xs font-bold"
                                style={{backgroundColor: cellColor.bg, color: cellColor.text}}
                              >
                                {value}
                              </div>
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center justify-center gap-4 mt-4 text-xs text-gray-400 dark:text-gray-500" >
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-md bg-status-success" />
                  <span>Baixo (1-4)</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-md bg-status-warning" />
                  <span>Médio (5-9)</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-md bg-status-warning" />
                  <span>Alto (10-14)</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-md bg-status-error" />
                  <span>Crítico (15+)</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6" >
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-status-error" />
                <CardTitle className="text-base font-medium text-gray-800 dark:text-gray-100" >
                  Top 5 Riscos Prioritários
                </CardTitle>
              </div>
              <Link 
                href="/admin/compliance/riscos/registro"
                className="text-sm flex items-center gap-1 hover:underline text-gray-700"
              >
                Ver todos
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {top5CriticalRisks.map((risk) => {
                const scoreConfig = getScoreColor(risk.score)
                return (
                  <div 
                    key={risk.id}
                    className="p-4 rounded-md border-l-4"
                    style={{backgroundColor: scoreConfig.bg,
                      borderLeftColor: scoreConfig.text}}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <Badge variant="outline" className="text-micro font-mono" style={{borderColor: scoreConfig.text, color: scoreConfig.text}}>
                        {risk.id}
                      </Badge>
                      <span className="text-lg font-bold" style={{color: scoreConfig.text}}>{risk.score}</span>
                    </div>
                    <p className="text-sm font-medium mb-2 text-gray-800 dark:text-gray-100" >
                      {risk.name}
                    </p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant="secondary" className="text-micro">
                        {risk.category}
                      </Badge>
                      <span className="text-xs text-gray-400 dark:text-gray-500" >
                        {getStatusLabel(risk.status)}
                      </span>
                    </div>
                    <div className="mt-2 text-xs text-gray-400 dark:text-gray-500" >
                      Owner: {risk.owner}
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {subpages.map((page) => {
            const Icon = page.icon
            return (
              <Link key={page.href} href={page.href}>
                <Card 
                  className="cursor-pointer transition-all hover:h-full"
                  
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30"
                      >
                        <Icon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate text-gray-800 dark:text-gray-100" >
                          {page.name}
                        </p>
                        <p className="text-xs truncate text-gray-400 dark:text-gray-500" >
                          {page.description}
                        </p>
                      </div>
                      {'count' in page && (
                        <Badge variant="secondary" className="text-xs">
                          {page.count}
                        </Badge>
                      )}
                      {'status' in page && (
                        <Badge className="text-xs bg-status-success/15 text-status-success hover:bg-status-success/15">
                          {page.status}
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}
