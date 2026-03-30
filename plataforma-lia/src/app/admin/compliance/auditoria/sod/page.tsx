"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Users,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Info,
  XCircle,
  FileText,
  Clock,
} from "lucide-react"

interface ConflictMatrix {
  functionA: string
  functionB: string
  conflict: boolean
  riskLevel: 'Alto' | 'Médio' | 'Baixo'
}

interface DetectedConflict {
  id: number
  user: string
  userEmail: string
  role1: string
  role2: string
  type: 'Alto Risco' | 'Médio Risco' | 'Baixo Risco'
  mitigation: string
  status: 'mitigated' | 'pending' | 'ok'
  detectedAt: string
  reviewedAt?: string
}

const conflictMatrix: ConflictMatrix[] = [
  { functionA: 'Aprovar Contratações', functionB: 'Configurar Vagas', conflict: true, riskLevel: 'Alto' },
  { functionA: 'Aprovar Pagamentos', functionB: 'Registrar Pagamentos', conflict: true, riskLevel: 'Alto' },
  { functionA: 'Criar Usuários', functionB: 'Aprovar Acessos', conflict: true, riskLevel: 'Alto' },
  { functionA: 'Acessar Dados Financeiros', functionB: 'Gerar Relatórios', conflict: false, riskLevel: 'Baixo' },
  { functionA: 'Configurar Sistema', functionB: 'Auditar Sistema', conflict: true, riskLevel: 'Médio' },
  { functionA: 'Gerenciar Candidatos', functionB: 'Visualizar Relatórios', conflict: false, riskLevel: 'Baixo' },
  { functionA: 'Aprovar Despesas', functionB: 'Solicitar Despesas', conflict: true, riskLevel: 'Alto' },
  { functionA: 'Definir Políticas', functionB: 'Implementar Políticas', conflict: true, riskLevel: 'Médio' },
]

const detectedConflicts: DetectedConflict[] = [
  { 
    id: 1, 
    user: 'Carlos Admin', 
    userEmail: 'carlos.admin@empresa.com',
    role1: 'Aprovar Contratações', 
    role2: 'Configurar Vagas', 
    type: 'Alto Risco', 
    mitigation: 'Revisão trimestral por comitê', 
    status: 'mitigated',
    detectedAt: '2024-10-15',
    reviewedAt: '2024-10-20',
  },
  { 
    id: 2, 
    user: 'Maria RH', 
    userEmail: 'maria.rh@empresa.com',
    role1: 'Acessar Dados Financeiros', 
    role2: 'Gerar Relatórios', 
    type: 'Baixo Risco', 
    mitigation: 'Logs de acesso monitorados', 
    status: 'ok',
    detectedAt: '2024-11-01',
    reviewedAt: '2024-11-05',
  },
  { 
    id: 3, 
    user: 'João Financeiro', 
    userEmail: 'joao.financeiro@empresa.com',
    role1: 'Aprovar Pagamentos', 
    role2: 'Registrar Pagamentos', 
    type: 'Alto Risco', 
    mitigation: 'Aguardando revisão', 
    status: 'pending',
    detectedAt: '2024-12-10',
  },
  { 
    id: 4, 
    user: 'Ana TI', 
    userEmail: 'ana.ti@empresa.com',
    role1: 'Configurar Sistema', 
    role2: 'Auditar Sistema', 
    type: 'Médio Risco', 
    mitigation: 'Segregação parcial implementada', 
    status: 'mitigated',
    detectedAt: '2024-09-20',
    reviewedAt: '2024-09-25',
  },
]

const getStatusBadge = (status: 'mitigated' | 'pending' | 'ok') => {
  switch (status) {
    case 'mitigated':
      return <Badge className="bg-status-warning/15 text-status-warning dark:bg-status-warning/20 dark:text-status-warning gap-1"><ShieldCheck className="w-3 h-3" />Mitigado</Badge>
    case 'pending':
      return <Badge variant="destructive" className="gap-1"><Clock className="w-3 h-3" />Pendente</Badge>
    case 'ok':
      return <Badge variant="success" className="gap-1"><CheckCircle2 className="w-3 h-3" />OK</Badge>
  }
}

const getRiskBadge = (type: string) => {
  switch (type) {
    case 'Alto Risco':
      return <Badge variant="destructive">{type}</Badge>
    case 'Médio Risco':
      return <Badge className="bg-status-warning/15 text-status-warning dark:bg-status-warning/20 dark:text-status-warning">{type}</Badge>
    case 'Baixo Risco':
      return <Badge variant="secondary">{type}</Badge>
    default:
      return <Badge variant="secondary">{type}</Badge>
  }
}

export default function SoDPage() {
  const conflictCount = detectedConflicts.length
  const pendingCount = detectedConflicts.filter(c => c.status === 'pending').length
  const mitigatedCount = detectedConflicts.filter(c => c.status === 'mitigated').length

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30"
            >
              <Users className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold lia-text-800 dark:text-lia-text-primary"
              >
                Matriz SoD
              </h1>
              <p className="text-sm lia-text-400 dark:lia-text-500">
                Segregação de Funções (Segregation of Duties)
              </p>
            </div>
          </div>
          <Button className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200">
            <FileText className="w-4 h-4" />
            Gerar Relatório
          </Button>
        </div>

        <Card className="mb-6 border-status-warning/30 bg-status-warning/10 dark:bg-status-warning/10 dark:border-status-warning/30">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-status-warning/15 dark:bg-status-warning/30 rounded-md">
                <AlertTriangle className="w-5 h-5 text-status-warning" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-status-warning dark:text-status-warning">
                  Matriz de Segregação de Funções - Em implementação
                </p>
                <p className="text-xs text-status-warning dark:text-status-warning mt-1">
                  <strong>Gap crítico identificado para SOX Section 404.</strong> Esta funcionalidade está em processo de implementação 
                  para garantir conformidade total com os requisitos de controle interno. Revisão e aprovação pendentes pelo comitê de compliance.
                </p>
              </div>
              <Badge className="bg-status-warning/20 text-status-warning dark:bg-status-warning dark:text-status-warning">Em Implementação</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-gray-100 dark:bg-lia-bg-secondary rounded-md">
                <Info className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium lia-text-950 dark:lia-text-50">
                  O que é Segregação de Funções (SoD)?
                </p>
                <p className="text-xs lia-text-500 mt-1">
                  A Segregação de Funções é um controle interno crítico exigido pela <strong>SOX Section 404</strong>. 
                  O princípio determina que nenhum indivíduo deve ter controle sobre todas as fases de uma transação crítica. 
                  Por exemplo, a mesma pessoa não deve poder criar e aprovar pagamentos, ou configurar e auditar sistemas. 
                  Isso previne fraudes e erros, garantindo integridade nos processos financeiros e operacionais.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gray-100 dark:bg-lia-bg-secondary rounded-md">
                  <Users className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                </div>
                <div>
                  <p className="text-sm lia-text-500">Total de Conflitos</p>
                  <p className="text-2xl font-semibold lia-text-950 dark:lia-text-50">{conflictCount}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-status-error/10 dark:bg-status-error/20 rounded-md">
                  <AlertTriangle className="w-5 h-5 text-status-error" />
                </div>
                <div>
                  <p className="text-sm lia-text-500">Pendentes</p>
                  <p className="text-2xl font-semibold lia-text-950 dark:lia-text-50">{pendingCount}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-status-warning/10 dark:bg-status-warning/20 rounded-md">
                  <ShieldCheck className="w-5 h-5 text-status-warning" />
                </div>
                <div>
                  <p className="text-sm lia-text-500">Mitigados</p>
                  <p className="text-2xl font-semibold lia-text-950 dark:lia-text-50">{mitigatedCount}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                  <CheckCircle2 className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-sm lia-text-500">Status Geral</p>
                  <p className="text-lg font-semibold lia-text-950 dark:lia-text-50">
                    {pendingCount === 0 ? 'Conforme' : 'Atenção'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">Matriz de Conflitos de Funções</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-secondary/50">
                    <th className="text-left text-xs font-medium lia-text-500 uppercase tracking-wider px-6 py-3">Função A</th>
                    <th className="text-center text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">vs</th>
                    <th className="text-left text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Função B</th>
                    <th className="text-center text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Conflito?</th>
                    <th className="text-center text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Nível de Risco</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:lia-divide-700">
                  {conflictMatrix.map((item, index) => (
                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                      <td className="px-6 py-4">
                        <span className="text-sm font-medium lia-text-950 dark:lia-text-50">{item.functionA}</span>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span className="lia-text-400">↔</span>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm font-medium lia-text-950 dark:lia-text-50">{item.functionB}</span>
                      </td>
                      <td className="px-4 py-4 text-center">
                        {item.conflict ? (
                          <div className="flex items-center justify-center">
                            <AlertTriangle className="w-5 h-5 text-status-error" />
                          </div>
                        ) : (
                          <div className="flex items-center justify-center">
                            <CheckCircle2 className="w-5 h-5 text-status-success" />
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-4 text-center">
                        {getRiskBadge(item.riskLevel === 'Alto' ? 'Alto Risco' : item.riskLevel === 'Médio' ? 'Médio Risco' : 'Baixo Risco')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium">Conflitos Detectados</CardTitle>
              <Badge variant="outline">{detectedConflicts.length} conflitos</Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-secondary/50">
                    <th className="text-left text-xs font-medium lia-text-500 uppercase tracking-wider px-6 py-3">Usuário</th>
                    <th className="text-left text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Função 1</th>
                    <th className="text-left text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Função 2</th>
                    <th className="text-center text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Tipo</th>
                    <th className="text-left text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Mitigação</th>
                    <th className="text-center text-xs font-medium lia-text-500 uppercase tracking-wider px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:lia-divide-700">
                  {detectedConflicts.map((conflict) => (
                    <tr key={conflict.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm font-medium lia-text-950 dark:lia-text-50">{conflict.user}</p>
                          <p className="text-xs lia-text-500">{conflict.userEmail}</p>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm lia-text-800 dark:text-lia-text-primary">{conflict.role1}</span>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm lia-text-800 dark:text-lia-text-primary">{conflict.role2}</span>
                      </td>
                      <td className="px-4 py-4 text-center">
                        {getRiskBadge(conflict.type)}
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-sm lia-text-800 dark:text-lia-text-primary">{conflict.mitigation}</span>
                      </td>
                      <td className="px-4 py-4 text-center">
                        {getStatusBadge(conflict.status)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">Legenda</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-6">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-status-success" />
                <span className="text-sm lia-text-800 dark:text-lia-text-primary">Sem Conflito / OK</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-status-error" />
                <span className="text-sm lia-text-800 dark:text-lia-text-primary">Conflito Identificado</span>
              </div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-status-warning" />
                <span className="text-sm lia-text-800 dark:text-lia-text-primary">Mitigado</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-status-error" />
                <span className="text-sm lia-text-800 dark:text-lia-text-primary">Pendente</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
