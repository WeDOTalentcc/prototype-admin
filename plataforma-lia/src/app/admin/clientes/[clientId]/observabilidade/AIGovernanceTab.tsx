"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Brain,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Eye,
  RefreshCw,
  Filter,
  ArrowDownRight,
} from "lucide-react"
import { useLGPDCompliance } from '@/hooks/admin/useLGPDCompliance'
import { useBiasAudits } from '@/hooks/admin/useBiasAudits'
import { AIDecisionsTable } from "./AIDecisionsTable"
import { LoadingSpinner, AIDecision, BiasAlert } from './observabilidade-shared'

export function AIGovernanceTab({ clientId }: { clientId: string }) {
  const { summary, latestAudit, audits: _audits, isLoading, error: _biasError, refetch: _biasRefetch } = useBiasAudits(clientId)
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
        resolved: result.status === 'clear' }))
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
    confidence: d.confidence }))

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
        <span className="ml-3 text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Carregando dados de governança de IA...</span>
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
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Total Decisões IA</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">{totalDecisionsCount.toLocaleString()}</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">Últimos 30 dias</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-wedo-purple/10 dark:bg-wedo-purple/20 flex items-center justify-center">
                <Brain className="w-5 h-5 text-wedo-purple dark:text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Taxa de Override</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">{overrideRate}%</p>
                <div className="flex items-center gap-1 mt-1">
                  <ArrowDownRight className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">Revisão humana</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-warning/10 dark:bg-status-warning/20 flex items-center justify-center">
                <RefreshCw className="w-5 h-5 text-status-warning dark:text-status-warning" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Cobertura Explainability</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">{explainabilityCoverage}%</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">Com explicação</span>
                </div>
              </div>
 <div className="w-10 h-10 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-secondary flex items-center justify-center">
 <Eye className="w-5 h-5 text-lia-text-primary dark:text-lia-text-secondary" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {Object.keys(agentCounts).length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
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
                        <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                          {agentLabels[agent] || agent}
                        </span>
                        <span className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
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
              <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
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
                    className={`p-4 rounded-md border ${alert.resolved ? 'bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 border-lia-border-subtle dark:border-lia-border-subtle' : alert.severity === 'high' ? 'bg-status-error/10 dark:bg-status-error/20 border-status-error/30 dark:border-status-error/30' : 'bg-status-warning/10 dark:bg-status-warning/20 border-status-warning/30 dark:border-status-warning/30'}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${alert.severity === 'high' ? 'bg-status-error/15 dark:bg-status-error/30' : 'bg-status-warning/15 dark:bg-status-warning/30'}`}>
                          <AlertTriangle className={`w-4 h-4 ${alert.severity === 'high' ? 'text-status-error dark:text-status-error' : 'text-status-warning dark:text-status-warning'}`} />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                            {alert.type}
                          </p>
                          <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary">
                            {alert.description}
                          </p>
                          <p className="text-xs mt-2 text-lia-text-tertiary dark:text-lia-text-secondary">
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
                <CheckCircle2 className="w-8 h-8 text-status-success mx-auto mb-2" />
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Nenhum alerta de bias detectado</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Decisões Recentes
            </CardTitle>
            <Button variant="outline" size="sm">
              <Filter className="w-4 h-4 mr-2" />
              Filtrar
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <AIDecisionsTable decisions={displayDecisions} formatDateTime={formatDateTime} />
        </CardContent>
      </Card>
    </div>
  )
}
