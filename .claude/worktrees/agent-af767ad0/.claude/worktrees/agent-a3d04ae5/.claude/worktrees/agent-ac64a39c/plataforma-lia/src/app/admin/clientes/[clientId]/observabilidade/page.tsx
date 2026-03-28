"use client"

import React, { useState, useEffect, use } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Shield,
  Brain,
  Lock,
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  TrendingUp,
  Eye,
  Users,
  FileText,
  Calendar,
  AlertCircle,
  Server,
  Wifi,
  RefreshCw,
  ChevronRight,
  Filter,
  ArrowUpRight,
  ArrowDownRight,
  Loader2
} from "lucide-react"
import { useLGPDCompliance } from '@/hooks/admin/useLGPDCompliance'
import { useComplianceControls } from '@/hooks/admin/useComplianceControls'
import { useBiasAudits } from '@/hooks/admin/useBiasAudits'

interface ComplianceFramework {
  id: string
  name: string
  shortName: string
  progress: number
  controlsImplemented: number
  controlsPartial: number
  controlsNotImplemented: number
  totalControls: number
  lastAudit?: string
  nextReview?: string
}

interface ComplianceControl {
  id: string
  code: string
  name: string
  framework: string
  status: 'implemented' | 'partial' | 'not_implemented'
  lastChecked: string
  owner?: string
}

interface AIDecision {
  id: string
  timestamp: string
  agent: string
  decisionType: string
  candidateId: string
  candidateName: string
  outcome: string
  overridden: boolean
  explainability: boolean
  confidence: number
}

interface BiasAlert {
  id: string
  type: string
  description: string
  severity: 'high' | 'medium' | 'low'
  detectedAt: string
  resolved: boolean
}



const statusColors = {
  implemented: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  partial: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  not_implemented: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  in_progress: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  not_started: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200',
  verified: 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400',
  not_applicable: 'bg-gray-100 text-gray-500 dark:bg-gray-900/30 dark:text-gray-500',
}

const statusLabels: Record<string, string> = {
  implemented: 'Implementado',
  partial: 'Parcial',
  not_implemented: 'Não Implementado',
  in_progress: 'Em Progresso',
  not_started: 'Não Iniciado',
  verified: 'Verificado',
  not_applicable: 'N/A',
}

function LoadingSpinner({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClass = size === 'lg' ? 'w-8 h-8' : size === 'md' ? 'w-6 h-6' : 'w-4 h-4'
  return <Loader2 className={`${sizeClass} animate-spin text-gray-600 dark:text-gray-400`} />
}

function ComplianceTab({ clientId }: { clientId: string }) {
  const { dashboard, controls, isLoading, error, refetch } = useComplianceControls(clientId)

  const formatDate = (dateStr: string | undefined | null) => {
    if (!dateStr) return '-'
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const frameworks: ComplianceFramework[] = dashboard?.byFramework
    ? Object.entries(dashboard.byFramework).map(([key, stats], index) => ({
        id: String(index + 1),
        name: key === 'ISO27001' ? 'ISO 27001' : key === 'SOC2' ? 'SOC 2 Type II' : key,
        shortName: key,
        progress: stats.compliancePercentage,
        controlsImplemented: stats.implemented + stats.verified,
        controlsPartial: stats.inProgress,
        controlsNotImplemented: stats.notStarted,
        totalControls: stats.totalControls,
        nextReview: undefined,
      }))
    : []

  const displayControls: ComplianceControl[] = controls.map((c) => ({
    id: c.id,
    code: c.control?.controlId || '-',
    name: c.control?.controlName || '-',
    framework: c.control?.framework || '-',
    status: c.status === 'implemented' || c.status === 'verified' ? 'implemented' : c.status === 'in_progress' ? 'partial' : 'not_implemented',
    lastChecked: c.lastReviewedAt || c.updatedAt || '',
    owner: c.ownerName,
  }))

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Carregando dados de compliance...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
        <p className="text-sm text-red-600">Erro ao carregar dados de compliance</p>
        <Button variant="outline" size="sm" onClick={refetch} className="mt-3">
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar novamente
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {frameworks.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {frameworks.map((framework) => (
            <Card key={framework.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-base" style={{ color: 'var(--eleven-text-primary)' }}>
                      {framework.name}
                    </h3>
                    <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      {framework.totalControls} controles totais
                    </p>
                  </div>
                  <Badge variant={framework.progress >= 80 ? 'success' : framework.progress >= 50 ? 'warning' : 'destructive'}>
                    {framework.progress.toFixed(0)}%
                  </Badge>
                </div>
                
                <Progress value={framework.progress} className="h-2 mb-4" />
                
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2 rounded-md bg-emerald-50 dark:bg-emerald-900/20">
                    <p className="text-lg font-semibold text-emerald-600 dark:text-emerald-400">{framework.controlsImplemented}</p>
                    <p className="text-[10px] text-emerald-600 dark:text-emerald-400">Implementado</p>
                  </div>
                  <div className="p-2 rounded-md bg-amber-50 dark:bg-amber-900/20">
                    <p className="text-lg font-semibold text-amber-600 dark:text-amber-400">{framework.controlsPartial}</p>
                    <p className="text-[10px] text-amber-600 dark:text-amber-400">Parcial</p>
                  </div>
                  <div className="p-2 rounded-md bg-red-50 dark:bg-red-900/20">
                    <p className="text-lg font-semibold text-red-600 dark:text-red-400">{framework.controlsNotImplemented}</p>
                    <p className="text-[10px] text-red-600 dark:text-red-400">Pendente</p>
                  </div>
                </div>

                {framework.nextReview && (
                  <div className="mt-4 pt-4 border-t" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                    <div className="flex items-center justify-between text-xs">
                      <span style={{ color: 'var(--eleven-text-tertiary)' }}>Próxima revisão</span>
                      <span className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                        {formatDate(framework.nextReview)}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-6 text-center">
            <Shield className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Nenhum framework de compliance configurado</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
              Controles de Compliance
            </CardTitle>
            <Button variant="outline" size="sm">
              <Filter className="w-4 h-4 mr-2" />
              Filtrar
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {displayControls.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Código</th>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Controle</th>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Framework</th>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Status</th>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Última Verificação</th>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Responsável</th>
                  </tr>
                </thead>
                <tbody>
                  {displayControls.map((control) => (
                    <tr key={control.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800/50" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                      <td className="py-3 px-2 text-sm font-mono" style={{ color: 'var(--eleven-text-primary)' }}>{control.code}</td>
                      <td className="py-3 px-2 text-sm" style={{ color: 'var(--eleven-text-primary)' }}>{control.name}</td>
                      <td className="py-3 px-2">
                        <Badge variant="outline" className="text-xs">{control.framework}</Badge>
                      </td>
                      <td className="py-3 px-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusColors[control.status] || statusColors.not_implemented}`}>
                          {control.status === 'implemented' && <CheckCircle2 className="w-3 h-3 mr-1" />}
                          {control.status === 'partial' && <AlertTriangle className="w-3 h-3 mr-1" />}
                          {control.status === 'not_implemented' && <XCircle className="w-3 h-3 mr-1" />}
                          {statusLabels[control.status] || control.status}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>{formatDate(control.lastChecked)}</td>
                      <td className="py-3 px-2 text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>{control.owner || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-6">
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Nenhum controle encontrado</p>
            </div>
          )}
        </CardContent>
      </Card>

      {dashboard && dashboard.upcomingReviews > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
              Próximas Revisões Agendadas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-4 rounded-md bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600">
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-50">
                    {dashboard.upcomingReviews} revisões agendadas
                  </p>
                  {dashboard.overdueReviews > 0 && (
                    <p className="text-xs text-red-600 mt-1">
                      {dashboard.overdueReviews} revisões em atraso
                    </p>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function AIGovernanceTab({ clientId }: { clientId: string }) {
  const { summary, latestAudit, audits, isLoading, error, refetch } = useBiasAudits(clientId)
  const { decisions, totalDecisions, isLoading: lgpdLoading } = useLGPDCompliance(clientId)

  const formatDateTime = (dateStr: string | undefined | null) => {
    if (!dateStr) return '-'
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
    } catch {
      return dateStr
    }
  }

  const biasAlerts: BiasAlert[] = latestAudit && latestAudit.biasResults
    ? Object.entries(latestAudit.biasResults).map(([key, result], index) => ({
        id: String(index + 1),
        type: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        description: result.details || `${key} analysis`,
        severity: result.status === 'concern' ? 'high' : result.status === 'consider' ? 'medium' : 'low',
        detectedAt: latestAudit.auditDate,
        resolved: result.status === 'clear',
      }))
    : []

  const displayDecisions: AIDecision[] = decisions.map((d) => ({
    id: d.id,
    timestamp: d.createdAt,
    agent: d.agentType,
    decisionType: d.decisionType,
    candidateId: d.candidateId || '',
    candidateName: d.candidateName || 'Candidato',
    outcome: d.decision,
    overridden: d.humanReviewRequested,
    explainability: !!d.explanation,
    confidence: d.confidence,
  }))

  const totalDecisionsCount = totalDecisions || displayDecisions.length
  const overriddenCount = displayDecisions.filter(d => d.overridden).length
  const overrideRate = totalDecisionsCount > 0 ? ((overriddenCount / totalDecisionsCount) * 100).toFixed(1) : '0'
  const explainabilityCount = displayDecisions.filter(d => d.explainability).length
  const explainabilityCoverage = totalDecisionsCount > 0 ? ((explainabilityCount / totalDecisionsCount) * 100).toFixed(1) : '0'

  const agentCounts = displayDecisions.reduce((acc, d) => {
    acc[d.agent] = (acc[d.agent] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  if (isLoading || lgpdLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Carregando dados de governança de IA...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Total Decisões IA</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>{totalDecisionsCount.toLocaleString()}</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-emerald-500" />
                  <span className="text-xs text-emerald-600">Últimos 30 dias</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-purple-50 dark:bg-purple-900/20 flex items-center justify-center">
                <Brain className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Taxa de Override</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>{overrideRate}%</p>
                <div className="flex items-center gap-1 mt-1">
                  <ArrowDownRight className="w-3 h-3 text-emerald-500" />
                  <span className="text-xs text-emerald-600">Revisão humana</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center">
                <RefreshCw className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Cobertura Explainability</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>{explainabilityCoverage}%</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-emerald-500" />
                  <span className="text-xs text-emerald-600">Com explicação</span>
                </div>
              </div>
 <div className="w-10 h-10 rounded-md bg-gray-50 dark:bg-gray-800 flex items-center justify-center">
 <Eye className="w-5 h-5 text-gray-900 dark:text-gray-300" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {Object.keys(agentCounts).length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                Decisões por Agente
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(agentCounts).map(([agent, count]) => {
                  const percentage = totalDecisionsCount > 0 ? ((count / totalDecisionsCount) * 100).toFixed(0) : '0'
                  const agentLabels: Record<string, string> = {
                    screening: 'Triagem',
                    scoring: 'Scoring',
                    interview: 'Entrevista',
                    matching: 'Matching'
                  }
                  return (
                    <div key={agent}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                          {agentLabels[agent] || agent}
                        </span>
                        <span className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          {count} ({percentage}%)
                        </span>
                      </div>
                      <Progress value={Number(percentage)} className="h-2" />
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        )}

        <Card className={Object.keys(agentCounts).length > 0 ? "lg:col-span-2" : "lg:col-span-3"}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                Alertas de Bias Detectados
              </CardTitle>
              {summary && (
                <Badge variant={summary.byStatus.concern > 0 ? 'destructive' : 'success'}>
                  {summary.byStatus.concern + summary.byStatus.consider} ativos
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {biasAlerts.length > 0 ? (
              <div className="space-y-3">
                {biasAlerts.map((alert) => (
                  <div 
                    key={alert.id} 
                    className={`p-4 rounded-md border ${alert.resolved ? 'bg-gray-50 dark:bg-gray-800/50' : alert.severity === 'high' ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800' : 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'}`}
                    style={{ borderColor: alert.resolved ? 'var(--eleven-border-subtle)' : undefined }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${alert.severity === 'high' ? 'bg-red-100 dark:bg-red-900/30' : 'bg-amber-100 dark:bg-amber-900/30'}`}>
                          <AlertTriangle className={`w-4 h-4 ${alert.severity === 'high' ? 'text-red-600 dark:text-red-400' : 'text-amber-600 dark:text-amber-400'}`} />
                        </div>
                        <div>
                          <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                            {alert.type}
                          </p>
                          <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                            {alert.description}
                          </p>
                          <p className="text-xs mt-2" style={{ color: 'var(--eleven-text-tertiary)' }}>
                            Detectado em: {formatDateTime(alert.detectedAt)}
                          </p>
                        </div>
                      </div>
                      <Badge variant={alert.resolved ? 'success' : alert.severity === 'high' ? 'destructive' : 'warning'}>
                        {alert.resolved ? 'Resolvido' : alert.severity.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Nenhum alerta de bias detectado</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
              Decisões Recentes
            </CardTitle>
            <Button variant="outline" size="sm">
              <Filter className="w-4 h-4 mr-2" />
              Filtrar
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {displayDecisions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Data/Hora</th>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Agente</th>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Candidato</th>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Decisão</th>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Confiança</th>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>Override</th>
                    <th className="text-left py-3 px-2 text-xs font-medium" style={{ color: 'var(--eleven-text-tertiary)' }}>XAI</th>
                  </tr>
                </thead>
                <tbody>
                  {displayDecisions.map((decision) => {
                    const agentLabels: Record<string, string> = {
                      screening: 'Triagem',
                      scoring: 'Scoring',
                      interview: 'Entrevista',
                      matching: 'Matching'
                    }
                    return (
                      <tr key={decision.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800/50" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                        <td className="py-3 px-2 text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>{formatDateTime(decision.timestamp)}</td>
                        <td className="py-3 px-2">
                          <Badge variant="outline" className="text-xs">{agentLabels[decision.agent] || decision.agent}</Badge>
                        </td>
                        <td className="py-3 px-2 text-sm" style={{ color: 'var(--eleven-text-primary)' }}>{decision.candidateName}</td>
                        <td className="py-3 px-2 text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{decision.outcome}</td>
                        <td className="py-3 px-2">
                          <div className="flex items-center gap-2">
                            <Progress value={decision.confidence * 100} className="h-1.5 w-16" />
                            <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>{(decision.confidence * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="py-3 px-2">
                          {decision.overridden ? (
                            <Badge variant="warning" className="text-xs">Sim</Badge>
                          ) : (
                            <Badge variant="outline" className="text-xs">Não</Badge>
                          )}
                        </td>
                        <td className="py-3 px-2">
                          {decision.explainability ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                          ) : (
                            <XCircle className="w-4 h-4 text-gray-400" />
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-6">
              <Brain className="w-8 h-8 text-wedo-cyan mx-auto mb-2" />
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Nenhuma decisão automatizada registrada</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function LGPDTab({ clientId }: { clientId: string }) {
  const { stats, dpo, breaches, isLoading, error, refetch } = useLGPDCompliance(clientId)

  const activeConsents = 0  // dados disponíveis em /admin/compliance/lgpd/consentimentos
  const pendingDSRs = 0     // dados disponíveis em /admin/compliance/lgpd/portal-titular
  const expiredData = 0     // dados disponíveis em /admin/compliance/lgpd/consentimentos

  const formatDate = (dateStr: string | undefined | null) => {
    if (!dateStr) return '-'
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const dsrTypeLabels: Record<string, string> = {
    access: 'Acesso',
    deletion: 'Exclusão',
    portability: 'Portabilidade',
    rectification: 'Retificação'
  }

  const dsrStatusLabels: Record<string, { label: string, variant: 'success' | 'warning' | 'destructive' | 'info' | 'default' }> = {
    pending: { label: 'Pendente', variant: 'warning' },
    in_progress: { label: 'Em Andamento', variant: 'info' },
    completed: { label: 'Concluído', variant: 'success' },
    overdue: { label: 'Atrasado', variant: 'destructive' }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Carregando dados LGPD...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>DPO Registrado</p>
                <p className="text-lg font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                  {dpo ? dpo.dpoName : (stats?.dpoRegistered ? 'Sim' : 'Não')}
                </p>
                {dpo && (
                  <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    {dpo.dpoEmail}
                  </p>
                )}
              </div>
              <div className="w-10 h-10 rounded-md bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                <Users className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Consentimentos Ativos</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>{activeConsents}</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-emerald-500" />
                  <span className="text-xs text-emerald-600">+8 esta semana</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Incidentes Abertos</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                  {stats?.openBreaches || breaches.filter(b => b.status !== 'resolved').length || 0}
                </p>
                {stats && stats.breachesPendingAnpd > 0 && (
                  <div className="flex items-center gap-1 mt-1">
                    <AlertCircle className="w-3 h-3 text-amber-500" />
                    <span className="text-xs text-amber-600">{stats.breachesPendingAnpd} pendentes ANPD</span>
                  </div>
                )}
              </div>
              <div className="w-10 h-10 rounded-md bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Dados Expirados</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>{expiredData}</p>
                <div className="flex items-center gap-1 mt-1">
                  <AlertCircle className="w-3 h-3 text-red-500" />
                  <span className="text-xs text-red-600">Requer ação</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-red-50 dark:bg-red-900/20 flex items-center justify-center">
                <Clock className="w-5 h-5 text-red-600 dark:text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {breaches.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                Incidentes de Dados (LGPD Art. 48)
              </CardTitle>
              <Badge variant={breaches.some(b => b.status !== 'resolved') ? 'warning' : 'success'}>
                {breaches.filter(b => b.status !== 'resolved').length} abertos
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {breaches.slice(0, 5).map((breach) => (
                <div 
                  key={breach.id}
                  className={`p-4 rounded-md border ${breach.severity === 'critical' || breach.severity === 'high' ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800' : 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'}`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                        {breach.breachDescription}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant={breach.severity === 'critical' ? 'destructive' : breach.severity === 'high' ? 'warning' : 'default'}>
                          {breach.severity.toUpperCase()}
                        </Badge>
                        {!breach.notificationSentToAnpd && breach.hoursUntilDeadline !== undefined && (
                          <span className="text-xs text-red-600">
                            {breach.hoursUntilDeadline}h para notificar ANPD
                          </span>
                        )}
                      </div>
                      <p className="text-xs mt-2" style={{ color: 'var(--eleven-text-tertiary)' }}>
                        Detectado: {formatDate(breach.breachDetectedAt)}
                      </p>
                    </div>
                    <Badge variant={breach.status === 'resolved' ? 'success' : 'warning'}>
                      {breach.status === 'resolved' ? 'Resolvido' : breach.status === 'notified' ? 'Notificado' : 'Aberto'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                Consentimentos por Candidato
              </CardTitle>
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4 mr-2" />
                Filtrar
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <FileText className="w-8 h-8 mb-3" style={{ color: 'var(--eleven-text-tertiary)' }} />
              <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                Consentimentos gerenciados centralmente
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Acesse a página de Consentimentos para ver e gerenciar os registros.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                Solicitações DSR
              </CardTitle>
              <Badge variant={pendingDSRs > 0 ? 'warning' : 'success'}>
                {pendingDSRs} pendentes
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Clock className="w-8 h-8 mb-3" style={{ color: 'var(--eleven-text-tertiary)' }} />
              <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                Solicitações de Titulares (Art. 18 LGPD)
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                As DSRs são gerenciadas no Portal do Titular.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
            Alertas de Retenção
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-4 rounded-md bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                <Clock className="w-4 h-4 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  {expiredData} registros com período de retenção expirado
                </p>
                <p className="text-xs mt-1 text-amber-600 dark:text-amber-400">
                  Estes dados devem ser excluídos ou ter seu consentimento renovado de acordo com a LGPD.
                </p>
                <Button variant="outline" size="sm" className="mt-3">
                  Revisar Dados
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function HealthTab() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Integrações Online</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>—</p>
                <div className="flex items-center gap-1 mt-1">
                  <Wifi className="w-3 h-3 text-gray-400" />
                  <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Aguardando dados</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center">
                <Server className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Incidentes Abertos</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>0</p>
                <div className="flex items-center gap-1 mt-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                  <span className="text-xs text-emerald-600">Nenhum incidente</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center">
                <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Uptime Médio</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>—</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-gray-400" />
                  <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Últimos 30 dias</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-gray-50 dark:bg-gray-800 flex items-center justify-center">
                <Activity className="w-5 h-5 text-gray-900 dark:text-gray-300" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
              Status das Integrações
            </CardTitle>
            <Button variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Atualizar
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <Server className="w-8 h-8 mb-3" style={{ color: 'var(--eleven-text-tertiary)' }} />
            <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
              Status de integrações em breve
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
              O monitoramento em tempo real das integrações será exibido aqui.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
              Timeline de Incidentes
            </CardTitle>
            <Badge variant="success">0 abertos</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <CheckCircle2 className="w-8 h-8 mb-3 text-emerald-500" />
            <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
              Nenhum incidente registrado
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Os incidentes serão listados aqui quando detectados.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default function ObservabilidadePage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const [activeTab, setActiveTab] = useState('compliance')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="space-y-6">
        <div>
          <div className="h-7 w-64 bg-gray-200 rounded animate-pulse" />
          <div className="h-5 w-96 bg-gray-100 rounded animate-pulse mt-2" />
        </div>
        <div className="h-12 w-full bg-gray-100 rounded-md animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-gray-100 rounded-md animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 
          className="text-lg font-semibold"
          style={{ color: 'var(--eleven-text-primary)' }}
        >
          Observabilidade & Governança
        </h2>
        <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
          Monitore compliance, governança de IA, privacidade e saúde do sistema
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="w-full justify-start bg-gray-100 dark:bg-gray-800 p-1 rounded-md">
          <TabsTrigger value="compliance" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Compliance
          </TabsTrigger>
          <TabsTrigger value="ai-governance" className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-wedo-cyan" />
            AI Governance
          </TabsTrigger>
          <TabsTrigger value="lgpd" className="flex items-center gap-2">
            <Lock className="w-4 h-4" />
            LGPD & Privacy
          </TabsTrigger>
          <TabsTrigger value="health" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Health & Incidents
          </TabsTrigger>
        </TabsList>

        <TabsContent value="compliance" className="mt-6">
          <ComplianceTab clientId={clientId} />
        </TabsContent>

        <TabsContent value="ai-governance" className="mt-6">
          <AIGovernanceTab clientId={clientId} />
        </TabsContent>

        <TabsContent value="lgpd" className="mt-6">
          <LGPDTab clientId={clientId} />
        </TabsContent>

        <TabsContent value="health" className="mt-6">
          <HealthTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
