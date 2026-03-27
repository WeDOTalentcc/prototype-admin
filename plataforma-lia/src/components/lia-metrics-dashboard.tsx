"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  TrendingUp, TrendingDown, Clock, Users, Target, CheckCircle,
  Phone, Calendar, Award, Zap, AlertCircle, ArrowRight, Activity,
  Timer
} from "lucide-react"
import { LiaMetricsChart } from "./lia-metrics-chart"
import { textStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"

interface LiaMetricsDashboardProps {
  candidates: any[]
}

// Gerar dados de evolução temporal (últimos 7 dias)
const generateTimeSeriesData = (currentValue: number, volatility: number = 5) => {
  const days = ['7d', '6d', '5d', '4d', '3d', '2d', 'Hoje']
  return days.map((day, index) => ({
    date: day,
    value: Math.max(0, Math.min(100,
      currentValue + (Math.random() - 0.5) * volatility * (7 - index)
    ))
  }))
}

export function LiaMetricsDashboard({ candidates }: LiaMetricsDashboardProps) {
  // Calcular métricas gerais
  const totalCandidates = candidates.length

  // Métricas de Contato
  const contacted = candidates.filter(c => c.contactStatus !== 'não contatado').length
  const contactRate = totalCandidates > 0 ? (contacted / totalCandidates) * 100 : 0

  // Métricas de Triagem
  const triageStarted = candidates.filter(c =>
    c.liaStatus === 'em_contato' ||
    c.liaStatus === 'triagem_completa' ||
    c.triageComplete
  ).length
  const triageCompleted = candidates.filter(c =>
    c.liaStatus === 'triagem_completa' ||
    c.triageComplete
  ).length
  const triageConversionRate = contacted > 0 ? (triageCompleted / contacted) * 100 : 0

  // Métricas de Triagem Aprovada
  const triageApproved = candidates.filter(c => {
    if (!c.triageComplete || !c.triageData) return false
    return c.triageData.mobility === 'OK' &&
           c.triageData.salary !== 'Acima do budget' &&
           c.triageData.interest !== 'Baixo'
  }).length
  const triageApprovalRate = triageCompleted > 0 ? (triageApproved / triageCompleted) * 100 : 0

  // Métricas de Entrevista
  const interviewScheduled = candidates.filter(c =>
    c.status === 'Entrevista marcada' ||
    c.status === 'Entrevista agendada' ||
    c.stage === 'Entrevista'
  ).length
  const interviewConversionRate = triageApproved > 0 ? (interviewScheduled / triageApproved) * 100 : 0

  // Métricas de Performance
  const avgLiaScore = candidates.length > 0
    ? candidates.reduce((sum, c) => sum + (c.liaScore || 0), 0) / candidates.length
    : 0
  const avgSkillsMatch = candidates.length > 0
    ? candidates.reduce((sum, c) => sum + (c.skillsMatch || 0), 0) / candidates.length
    : 0

  // Tempo médio por etapa (simulado - em produção viria do backend)
  const avgTimeContact = 1.5 // dias
  const avgTimeTriage = 2.8 // dias
  const avgTimeInterview = 5.2 // dias
  const avgTimeTotal = avgTimeContact + avgTimeTriage + avgTimeInterview

  // Candidatos aguardando ação
  const pendingApproval = candidates.filter(c => c.approvalPending).length
  const pendingFeedback = candidates.filter(c =>
    c.status === 'Reprovado' && !c.feedbackSent
  ).length

  // Breakdown por etapa
  const stageBreakdown = [
    {
      stage: 'Contato Inicial',
      count: contacted,
      total: totalCandidates,
      rate: contactRate,
      avgTime: avgTimeContact,
      icon: <Phone className="w-4 h-4" />,
      color: 'text-gray-600 dark:text-gray-400',
      bgColor: 'bg-gray-100 dark:bg-gray-800'
    },
    {
      stage: 'Triagem Iniciada',
      count: triageStarted,
      total: contacted,
      rate: contacted > 0 ? (triageStarted / contacted) * 100 : 0,
      avgTime: avgTimeTriage,
      icon: <Target className="w-4 h-4" />,
      color: 'text-gray-900 dark:text-gray-50',
 bgColor: 'bg-gray-50 dark:bg-gray-800'
    },
    {
      stage: 'Triagem Completa',
      count: triageCompleted,
      total: triageStarted,
      rate: triageConversionRate,
      avgTime: avgTimeTriage,
      icon: <CheckCircle className="w-4 h-4" />,
      color: 'text-status-success',
      bgColor: 'bg-status-success/10'
    },
    {
      stage: 'Triagem Aprovada',
      count: triageApproved,
      total: triageCompleted,
      rate: triageApprovalRate,
      avgTime: 0.5,
      icon: <Award className="w-4 h-4" />,
      color: 'text-status-success',
      bgColor: 'bg-status-success/10'
    },
    {
      stage: 'Entrevista Agendada',
      count: interviewScheduled,
      total: triageApproved,
      rate: interviewConversionRate,
      avgTime: avgTimeInterview,
      icon: <Calendar className="w-4 h-4" />,
      color: 'text-wedo-purple',
      bgColor: 'bg-wedo-purple/10'
    }
  ]

  // Funil de Conversão
  const funnelStages = stageBreakdown.map(stage => ({
    ...stage,
    stage: stage.stage.replace('Triagem', 'Triagem Iniciada')
  }))

  // Distribuição de Scores LIA
  const scoreDistribution = [
    { date: '0-2', value: candidates.filter(c => (c.liaScore || 0) >= 0 && (c.liaScore || 0) < 2).length },
    { date: '2-4', value: candidates.filter(c => (c.liaScore || 0) >= 2 && (c.liaScore || 0) < 4).length },
    { date: '4-6', value: candidates.filter(c => (c.liaScore || 0) >= 4 && (c.liaScore || 0) < 6).length },
    { date: '6-8', value: candidates.filter(c => (c.liaScore || 0) >= 6 && (c.liaScore || 0) < 8).length },
    { date: '8-10', value: candidates.filter(c => (c.liaScore || 0) >= 8 && (c.liaScore || 0) <= 10).length },
  ]

  // Métricas por fonte
  const sourceMetricsObj = candidates.reduce((acc, c) => {
    const source = c.source
    if (!source) return acc

    if (!acc[source]) {
      acc[source] = { source, count: 0, contacted: 0, avgScore: 0 }
    }

    acc[source].count += 1
    acc[source].contacted += c.contactStatus !== 'não contatado' ? 1 : 0
    acc[source].avgScore = (acc[source].avgScore * (acc[source].count - 1) + (c.liaScore || 0)) / acc[source].count

    return acc
  }, {} as Record<string, any>)

  const sourceMetrics = Object.values(sourceMetricsObj).map((source: any) => ({
    ...source,
    conversionRate: source.count > 0 ? (source.contacted / source.count) * 100 : 0
  }))

  // Breakdown por status
  const candidateStatusBreakdown = [
    { status: 'Contato Inicial', count: contacted, percentage: (contacted / totalCandidates) * 100, icon: <Phone className="w-4 h-4" /> },
    { status: 'Triagem Iniciada', count: triageStarted, percentage: (triageStarted / totalCandidates) * 100, icon: <Target className="w-4 h-4" /> },
    { status: 'Triagem Completa', count: triageCompleted, percentage: (triageCompleted / totalCandidates) * 100, icon: <CheckCircle className="w-4 h-4" /> },
    { status: 'Triagem Aprovada', count: triageApproved, percentage: (triageApproved / totalCandidates) * 100, icon: <Award className="w-4 h-4" /> },
    { status: 'Entrevista Agendada', count: interviewScheduled, percentage: (interviewScheduled / totalCandidates) * 100, icon: <Calendar className="w-4 h-4" /> },
    { status: 'Reprovado', count: candidates.filter(c => c.status === 'Reprovado').length, percentage: (candidates.filter(c => c.status === 'Reprovado').length / totalCandidates) * 100, icon: <AlertCircle className="w-4 h-4" /> },
  ]

  return (
    <div className="space-y-4">
      {/* KPIs Principais - Mais Compactos */}
      <div className="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-3">
        {/* Taxa de Contato */}
        <Card>
          <CardContent className="p-3">
            <div className="flex items-center justify-between mb-1">
              <Phone className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <Badge className={`text-xs px-1.5 py-0.5 ${contactRate >= 80 ? 'bg-status-success' : contactRate >= 60 ? 'bg-status-warning' : 'bg-status-error'} text-white`}>
                {contactRate.toFixed(0)}%
              </Badge>
            </div>
            <div className={`text-lg font-bold text-gray-950 dark:text-gray-50`}>
              {contacted}/{totalCandidates}
            </div>
            <div className={`${textStyles.bodySmall} dark:text-gray-200`}>
              Taxa de Contato
            </div>
          </CardContent>
        </Card>

        {/* Taxa de Triagem */}
        <Card>
          <CardContent className="p-3">
            <div className="flex items-center justify-between mb-1">
              <CheckCircle className="w-4 h-4 text-status-success" />
              <Badge className={`text-xs px-1.5 py-0.5 ${triageConversionRate >= 70 ? 'bg-status-success' : triageConversionRate >= 50 ? 'bg-status-warning' : 'bg-status-error'} text-white`}>
                {triageConversionRate.toFixed(0)}%
              </Badge>
            </div>
            <div className={`text-lg font-bold text-gray-950 dark:text-gray-50`}>
              {triageCompleted}/{contacted}
            </div>
            <div className={`${textStyles.bodySmall} dark:text-gray-200`}>
              Taxa de Triagem
            </div>
          </CardContent>
        </Card>

        {/* Taxa de Aprovação */}
        <Card>
          <CardContent className="p-3">
            <div className="flex items-center justify-between mb-1">
              <Award className="w-4 h-4 text-status-success" />
              <Badge className={`text-xs px-1.5 py-0.5 ${triageApprovalRate >= 60 ? 'bg-status-success' : triageApprovalRate >= 40 ? 'bg-status-warning' : 'bg-status-error'} text-white`}>
                {triageApprovalRate.toFixed(0)}%
              </Badge>
            </div>
            <div className={`text-lg font-bold text-gray-950 dark:text-gray-50`}>
              {triageApproved}/{triageCompleted}
            </div>
            <div className={`${textStyles.bodySmall} dark:text-gray-200`}>
              Taxa de Aprovação
            </div>
          </CardContent>
        </Card>

        {/* Taxa de Conversão */}
        <Card>
          <CardContent className="p-3">
            <div className="flex items-center justify-between mb-1">
              <Calendar className="w-4 h-4 text-wedo-purple" />
              <Badge className={`text-xs px-1.5 py-0.5 ${interviewConversionRate >= 50 ? 'bg-status-success' : interviewConversionRate >= 30 ? 'bg-status-warning' : 'bg-status-error'} text-white`}>
                {interviewConversionRate.toFixed(0)}%
              </Badge>
            </div>
            <div className={`text-lg font-bold text-gray-950 dark:text-gray-50`}>
              {interviewScheduled}/{triageApproved}
            </div>
            <div className={`${textStyles.bodySmall} dark:text-gray-200`}>
              Agendamentos
            </div>
          </CardContent>
        </Card>

        {/* Tempo Médio de Contato */}
        <Card>
          <CardContent className="p-3">
            <div className="flex items-center justify-between mb-1">
              <Clock className="w-4 h-4 text-wedo-orange" />
              <TrendingUp className="w-3 h-3 text-status-success" />
            </div>
            <div className={`text-lg font-bold text-gray-950 dark:text-gray-50`}>
              {avgTimeContact.toFixed(1)}h
            </div>
            <div className={`${textStyles.bodySmall} dark:text-gray-200`}>
              Tempo Contato
            </div>
          </CardContent>
        </Card>

        {/* Score Médio LIA */}
        <Card>
          <CardContent className="p-3">
            <div className="flex items-center justify-between mb-1">
              <Zap className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <Badge className="text-xs px-1.5 py-0.5 bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900">
                {avgLiaScore.toFixed(1)}
              </Badge>
            </div>
            <div className={`text-lg font-bold text-gray-950 dark:text-gray-50`}>
              {avgSkillsMatch}%
            </div>
            <div className={`${textStyles.bodySmall} dark:text-gray-200`}>
              Score/Match
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Funil Compacto e Gráficos em Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Funil de Conversão */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
              <Activity className="w-4 h-4 text-indigo-600" />
              Funil de Conversão LIA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {funnelStages.map((stage, index) => (
                <div key={index} className="relative">
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-md ${stage.bgColor} flex items-center justify-center`}>
                      {stage.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className={`${textStyles.label} dark:text-gray-200`}>
                          {stage.stage}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-600">
                            {stage.count}/{stage.total}
                          </span>
                          <Badge className="text-xs px-1.5 py-0.5" variant="outline">
                            {stage.rate.toFixed(0)}%
                          </Badge>
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${
                            stage.rate >= 70 ? 'bg-wedo-green' :
                            stage.rate >= 50 ? 'bg-wedo-orange' :
                            'bg-status-error'
                          }`}
                          style={{ width: `${stage.rate}%` }}
                        />
                      </div>
                    </div>
                    {stage.avgTime > 0 && (
                      <div className={`flex items-center gap-1 ${textStyles.bodySmall}`}>
                        <Timer className="w-3 h-3" />
                        {stage.avgTime}h
                      </div>
                    )}
                  </div>
                  {index < funnelStages.length - 1 && (
                    <ArrowRight className="w-3 h-3 text-gray-600 ml-4 my-1" />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Score Distribution - Mais Compacto */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
              <TrendingUp className="w-4 h-4 text-status-success" />
              Distribuição de Scores LIA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48">
              <LiaMetricsChart
                data={scoreDistribution}
                title="Distribuição de Scores"
                color="var(--status-success)"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Gráficos Adicionais - Grid Compacto */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Taxa de Contato ao Longo do Tempo */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
              <Phone className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              Taxa de Contato (7 dias)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-32">
              <LiaMetricsChart
                data={generateTimeSeriesData(contactRate)}
                title=""
                color="var(--gray-600)"
              />
            </div>
          </CardContent>
        </Card>

        {/* Taxa de Conversão ao Longo do Tempo */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
              <TrendingUp className="w-4 h-4 text-status-success" />
              Taxa de Conversão (7 dias)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-32">
              <LiaMetricsChart
                data={generateTimeSeriesData(triageConversionRate)}
                title=""
                color="var(--status-success)"
              />
            </div>
          </CardContent>
        </Card>

        {/* Match de Skills ao Longo do Tempo */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
              <Target className="w-4 h-4 text-wedo-purple" />
              Match de Skills (7 dias)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-32">
              <LiaMetricsChart
                data={generateTimeSeriesData(avgSkillsMatch)}
                title=""
                color="#9333ea"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alertas e Ações Pendentes */}
      {pendingApproval > 0 && (
        <Card className="bg-wedo-orange/10">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-wedo-orange/20 rounded-md flex items-center justify-center">
                  <AlertCircle className="w-4 h-4 text-wedo-orange" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-wedo-orange">
                    {pendingApproval} Ações Pendentes
                  </div>
                  <div className="text-xs text-wedo-orange/80">
                    Aguardando aprovação para contato ou próximo passo
                  </div>
                </div>
              </div>
              <Button size="sm" className="bg-wedo-orange hover:bg-wedo-orange/90 text-white">
                <Zap className="w-3 h-3 mr-1" />
                Revisar Agora
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Métricas Detalhadas por Fonte - Compacto */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
            <Users className="w-4 h-4 text-gray-900 dark:text-gray-50" />
            Performance por Fonte
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {sourceMetrics.map((source) => (
              <div key={source.source} className="flex items-center gap-2">
                <div className="w-6 h-6 bg-gray-100 dark:bg-gray-800 rounded flex items-center justify-center">
                  <Users className="w-3 h-3 text-gray-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-medium text-gray-800 dark:text-gray-200">{source.source}</span>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs px-1 py-0">
                        {source.count} cand.
                      </Badge>
                      <Badge className={`text-xs px-1 py-0 ${
                        source.conversionRate >= 70 ? 'bg-status-success' :
                        source.conversionRate >= 50 ? 'bg-status-warning' :
                        'bg-status-error'
                      } text-white`}>
                        {source.conversionRate.toFixed(0)}%
                      </Badge>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
                    <div
                      className={`h-1 rounded-full ${
                        source.conversionRate >= 70 ? 'bg-status-success' :
                        source.conversionRate >= 50 ? 'bg-status-warning' :
                        'bg-status-error'
                      }`}
                      style={{ width: `${source.conversionRate}%` }}
                    />
                  </div>
                </div>
                <div className={textStyles.bodySmall}>
                  Score: {source.avgScore.toFixed(1)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Status dos Candidatos - Grid Compacto */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
        {candidateStatusBreakdown.map((status) => (
          <Card key={status.status}>
            <CardContent className="p-2">
              <div className="flex items-center justify-between mb-1">
                {status.icon}
                <span className="text-xs font-bold text-gray-950 dark:text-gray-50">
                  {status.count}
                </span>
              </div>
              <div className={`${textStyles.bodySmall} dark:text-gray-200 truncate`}>
                {status.status}
              </div>
              <div className={textStyles.bodySmall}>
                {status.percentage.toFixed(0)}% do total
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Insights e Recomendações - Mais Compacto */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
            <TrendingUp className="w-4 h-4 text-indigo-600" />
            Insights da LIA
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {/* Insight 1: Taxa de Contato */}
            <div className={`p-3 rounded-md ${
              contactRate >= 80 ? 'bg-status-success/10' :
              contactRate >= 60 ? 'bg-status-warning/10' :
              'bg-status-error/10'
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <Phone className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                <span className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                  Taxa de Contato
                </span>
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200">
                {contactRate >= 80 ?
                  '✅ Excelente! Continue assim.' :
                  contactRate >= 60 ?
                  '⚠️ Pode melhorar. Tente contatos em horários alternativos.' :
                  '❌ Baixa. Considere múltiplos canais de contato.'
                }
              </p>
            </div>

            {/* Insight 2: Taxa de Conversão */}
            <div className={`p-3 rounded-md ${
              triageConversionRate >= 70 ? 'bg-status-success/10' :
              triageConversionRate >= 50 ? 'bg-status-warning/10' :
              'bg-status-error/10'
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <Target className="w-3 h-3 text-status-success" />
                <span className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                  Taxa de Conversão
                </span>
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200">
                {triageConversionRate >= 70 ?
                  '✅ Ótima conversão na triagem!' :
                  triageConversionRate >= 50 ?
                  '⚠️ Conversão moderada. Revise critérios.' :
                  '❌ Conversão baixa. Ajuste requisitos.'
                }
              </p>
            </div>

            {/* Insight 3: Tempo de Resposta */}
            <div className={`p-3 rounded-md ${
              avgTimeContact <= 2 ? 'bg-status-success/10' :
              avgTimeContact <= 4 ? 'bg-status-warning/10' :
              'bg-status-error/10'
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <Clock className="w-3 h-3 text-wedo-orange" />
                <span className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                  Velocidade
                </span>
              </div>
              <p className="text-xs text-gray-800 dark:text-gray-200">
                {avgTimeContact <= 2 ?
                  '✅ Resposta rápida! Mantém candidatos engajados.' :
                  avgTimeContact <= 4 ?
                  '⚠️ Tempo razoável. Pode ser mais ágil.' :
                  '❌ Muito lento. Risco de perder candidatos.'
                }
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Scores */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-gray-600 dark:text-gray-300 mb-1">
                  Score Médio LIA
                </div>
                <div className="text-3xl font-bold text-gray-950 dark:text-gray-50">
                  {avgLiaScore.toFixed(1)}
                </div>
              </div>
              <div className="w-16 h-16 rounded-full bg-wedo-cyan flex items-center justify-center text-white text-xl font-bold">
                {(avgLiaScore * 10).toFixed(0)}
              </div>
            </div>
            <div className="mt-3 w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-wedo-cyan transition-all duration-500"
                style={{ width: `${avgLiaScore * 10}%` }}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-gray-600 dark:text-gray-300 mb-1">
                  Match Médio de Skills
                </div>
                <div className="text-3xl font-bold text-gray-950 dark:text-gray-50">
                  {avgSkillsMatch.toFixed(0)}%
                </div>
              </div>
              <div className="w-16 h-16 rounded-full bg-wedo-green flex items-center justify-center text-white text-xl font-bold">
                {avgSkillsMatch.toFixed(0)}
              </div>
            </div>
            <div className="mt-3 w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-wedo-green transition-all duration-500"
                style={{ width: `${avgSkillsMatch}%` }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Evolução Temporal das Métricas */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Evolução das Métricas (Últimos 7 Dias)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-6">
            <LiaMetricsChart
              data={generateTimeSeriesData(contactRate)}
              title="Taxa de Contato"
              color="var(--gray-600)"
              targetValue={80}
            />
            <LiaMetricsChart
              data={generateTimeSeriesData(triageConversionRate)}
              title="Taxa de Conversão (Triagem)"
              color="var(--status-success)"
              targetValue={70}
            />
            <LiaMetricsChart
              data={generateTimeSeriesData(triageApprovalRate)}
              title="Taxa de Aprovação"
              color="#8b5cf6"
              targetValue={60}
            />
            <LiaMetricsChart
              data={generateTimeSeriesData(interviewConversionRate)}
              title="Taxa de Entrevista"
              color="var(--status-warning)"
              targetValue={50}
            />
          </div>
        </CardContent>
      </Card>

      {/* SLA e Métricas de Tempo */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Timer className="w-4 h-4" />
            SLA e Tempo Médio por Etapa
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* SLA Overview */}
            <div className="grid grid-cols-4 gap-4 mb-4">
 <div className="p-3 bg-gray-100 rounded-md">
                <div className="flex items-center justify-between mb-2">
                  <Timer className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  <Badge className="bg-status-success text-white text-xs">
                    ✓ No Prazo
                  </Badge>
                </div>
                <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                  {avgTimeContact.toFixed(1)}d
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  Contato Inicial
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  SLA: 2 dias
                </div>
              </div>

              <div className="p-3 bg-status-success/10 dark:bg-gray-800 rounded-md">
                <div className="flex items-center justify-between mb-2">
                  <Timer className="w-5 h-5 text-status-success" />
                  <Badge className="bg-status-success text-white text-xs">
                    ✓ No Prazo
                  </Badge>
                </div>
                <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                  {avgTimeTriage.toFixed(1)}d
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  Triagem Completa
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  SLA: 3 dias
                </div>
              </div>

              <div className="p-3 bg-status-warning/10 dark:bg-gray-800 rounded-md">
                <div className="flex items-center justify-between mb-2">
                  <Timer className="w-5 h-5 text-status-warning" />
                  <Badge className="bg-status-warning text-white text-xs">
                    ⚠ Atenção
                  </Badge>
                </div>
                <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                  {avgTimeInterview.toFixed(1)}d
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  Agendamento
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  SLA: 5 dias
                </div>
              </div>

              <div className="p-3 bg-wedo-purple/10 dark:bg-gray-800 rounded-md">
                <div className="flex items-center justify-between mb-2">
                  <Clock className="w-5 h-5 text-wedo-purple" />
                  <Badge className="bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900 text-xs">
                    Total
                  </Badge>
                </div>
                <div className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                  {avgTimeTotal.toFixed(1)}d
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  Tempo Total
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  Contato → Entrevista
                </div>
              </div>
            </div>

            {/* Tempo Médio até Contratação */}
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gray-400 rounded-md flex items-center justify-center">
                    <Award className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                      Tempo Médio até Contratação
                    </div>
                    <div className="text-3xl font-bold text-gray-950 dark:text-gray-50">
                      {(avgTimeTotal + 7).toFixed(0)} dias
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-600 dark:text-gray-300 mb-1">
                    Meta do Mercado
                  </div>
                  <div className="text-2xl font-semibold text-gray-800 dark:text-gray-200">
                    15 dias
                  </div>
                  <Badge className="mt-2 bg-status-success text-white">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    Dentro da Meta
                  </Badge>
                </div>
              </div>

              {/* Progress bar comparativa */}
              <div className="mt-4">
                <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-2">
                  <span>Seu desempenho</span>
                  <span>Benchmark mercado</span>
                </div>
                <div className="relative h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="absolute h-full bg-gray-400 rounded-full transition-all duration-500"
                    style={{ width: `${((avgTimeTotal + 7) / 15) * 100}%` }}
                  />
                  <div
                    className="absolute h-full border-r-2 border-status-error/30"
                    style={{ left: '100%' }}
                  />
                </div>
              </div>
            </div>

            {/* Breakdown Detalhado */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-white dark:bg-gray-800 rounded-md">
                <div className="text-xs text-gray-600 dark:text-gray-300 mb-2">
                  Mais Rápido
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-status-success" />
                  <div>
                    <div className="text-lg font-bold text-gray-950 dark:text-gray-50">
                      {(avgTimeTotal * 0.6).toFixed(1)}d
                    </div>
                    <div className="text-xs text-gray-600">
                      Melhor caso
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-white dark:bg-gray-800 rounded-md">
                <div className="text-xs text-gray-600 dark:text-gray-300 mb-2">
                  Médio
                </div>
                <div className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  <div>
                    <div className="text-lg font-bold text-gray-950 dark:text-gray-50">
                      {avgTimeTotal.toFixed(1)}d
                    </div>
                    <div className="text-xs text-gray-600">
                      Caso típico
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-white dark:bg-gray-800 rounded-md">
                <div className="text-xs text-gray-600 dark:text-gray-300 mb-2">
                  Mais Lento
                </div>
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-wedo-orange" />
                  <div>
                    <div className="text-lg font-bold text-gray-950 dark:text-gray-50">
                      {(avgTimeTotal * 1.8).toFixed(1)}d
                    </div>
                    <div className="text-xs text-gray-600">
                      Pior caso
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
