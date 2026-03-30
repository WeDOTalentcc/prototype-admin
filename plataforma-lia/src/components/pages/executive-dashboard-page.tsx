"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  BarChart3, TrendingUp, TrendingDown, Users, Briefcase, DollarSign,
  Clock, Target, AlertTriangle, CheckCircle, Calendar, Filter,
  Download, Share2, Mail, RefreshCw, Eye, ArrowUpRight, ArrowDownRight,
  Building, MapPin, Star, Zap, Heart, UserCheck, MessageSquare,
  PieChart, Activity, Award, Percent, Timer, FileText, Trophy, Brain
} from "lucide-react"
import { PredictiveAnalyticsTab } from "@/components/dashboard/predictive-analytics-tab"
import { CalibrationDashboard } from "@/components/calibration"
import { AgentControlCenter } from "@/components/agent-control-center"
import { Scale } from "lucide-react"

const executiveDashboardData = {
  period: {
    current: "Janeiro 2024",
    previous: "Dezembro 2023"
  },
  summary: {
    totalJobs: 25,
    activeJobs: 18,
    urgentJobs: 5,
    criticalJobs: 2,
    totalCandidates: 1247,
    totalHires: 12,
    averageTimeToHire: 28,
    averageCostPerHire: 3200,
    conversionRate: 67,
    npsScore: 82
  },
  trends: {
    jobs: { value: 25, change: +15, trend: "up" },
    candidates: { value: 1247, change: +23, trend: "up" },
    hires: { value: 12, change: -8, trend: "down" },
    timeToHire: { value: 28, change: -12, trend: "down" },
    costPerHire: { value: 3200, change: +5, trend: "up" },
    nps: { value: 82, change: +7, trend: "up" }
  },
  departmentMetrics: [
    { department: "Tecnologia", jobs: 8, candidates: 456, hires: 5, avgTime: 25, conversion: 72 },
    { department: "Design", jobs: 4, candidates: 234, hires: 3, avgTime: 22, conversion: 68 },
    { department: "Produto", jobs: 3, candidates: 187, hires: 2, avgTime: 35, conversion: 58 },
    { department: "Marketing", jobs: 5, candidates: 298, hires: 2, avgTime: 31, conversion: 45 },
    { department: "Vendas", jobs: 5, candidates: 72, hires: 0, avgTime: 45, conversion: 0 }
  ],
  topPerformingJobs: [
    { id: "WDT-2025-001", title: "UX Designer Sênior", department: "Design", candidates: 45, hires: 2, conversion: 67, avgTime: 18 },
    { id: "WDT-2025-002", title: "Frontend Developer", department: "Tecnologia", candidates: 68, hires: 3, conversion: 72, avgTime: 21 },
    { id: "WDT-2025-003", title: "Product Manager", department: "Produto", candidates: 28, hires: 1, conversion: 58, avgTime: 25 }
  ],
  pendingActions: [
    { type: "interview", message: "8 entrevistas pendentes de agendamento", count: 8, priority: "alta" },
    { type: "feedback", message: "12 feedbacks de entrevista pendentes", count: 12, priority: "média" },
    { type: "offer", message: "3 propostas aguardando aprovação", count: 3, priority: "alta" },
    { type: "deadline", message: "5 vagas com prazo em 7 dias", count: 5, priority: "crítica" }
  ],
  recruitmentFunnel: {
    total: 1247,
    screening: 623,
    interview: 298,
    final: 156,
    hired: 12,
    dropped: 158
  },
  benchmarks: {
    industryAverages: {
      timeToHire: 35,
      costPerHire: 4200,
      conversionRate: 58,
      nps: 78,
      offerAcceptanceRate: 82
    }
  },
  financialMetrics: {
    totalBudget: 480000,
    spentToDate: 342000,
    projectedSpend: 456000,
    costSavings: 38000,
    roi: 285,
    budgetUtilization: 71.25
  },
  strategicMetrics: {
    employeeSatisfaction: 4.3,
    retentionRate: 91,
    diversityScore: 73,
    skillsGapCoverage: 68,
    marketCompetitiveness: 82
  },
  riskFactors: [
    { factor: "Budget Overrun Risk", probability: 23, impact: "Medium", mitigation: "Optimize sourcing channels" },
    { factor: "Talent Shortage in Tech", probability: 67, impact: "High", mitigation: "Expand remote hiring" },
    { factor: "Salary Inflation", probability: 45, impact: "Medium", mitigation: "Review compensation bands" }
  ]
}

export function ExecutiveDashboardPage() {
  const [selectedPeriod, setSelectedPeriod] = useState("month")
  const [selectedDepartment, setSelectedDepartment] = useState("all")
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = () => {
    setRefreshing(true)
    setTimeout(() => setRefreshing(false), 2000)
  }

  const data = executiveDashboardData

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-xl font-sans font-semibold text-lia-text-primary dark:text-lia-text-primary mb-1">
                Dashboard Executivo
              </h1>
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                Visão consolidada de métricas e performance de recrutamento
              </p>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary dark:text-lia-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:ring-gray-50/20/50"
              >
                <option value="week">Esta Semana</option>
                <option value="month">Este Mês</option>
                <option value="quarter">Este Trimestre</option>
                <option value="year">Este Ano</option>
              </select>

              <select
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
                className="px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary dark:text-lia-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:ring-gray-50/20/50"
              >
                <option value="all">Todos Departamentos</option>
                <option value="tecnologia">Tecnologia</option>
                <option value="design">Design</option>
                <option value="produto">Produto</option>
                <option value="marketing">Marketing</option>
                <option value="vendas">Vendas</option>
              </select>

              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
                className="gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin motion-reduce:animate-none' : ''}`} />
                Atualizar
              </Button>

              <Button variant="outline" size="sm" className="gap-2">
                <Download className="w-4 h-4" />
                Exportar
              </Button>
            </div>
          </div>
        </div>

        <Tabs defaultValue="funnel" className="w-full">
          <TabsList className="mb-6 bg-gray-100 dark:bg-lia-bg-secondary p-1 rounded-md">
            <TabsTrigger value="funnel" className="gap-2 data-[state=active]:bg-lia-bg-primary dark:data-[state=active]:bg-gray-700">
              <BarChart3 className="w-4 h-4" />
              Funil & Performance
            </TabsTrigger>
            <TabsTrigger value="strategic" className="gap-2 data-[state=active]:bg-lia-bg-primary dark:data-[state=active]:bg-gray-700">
              <Award className="w-4 h-4" />
              Visão Estratégica
            </TabsTrigger>
            <TabsTrigger value="agents" className="gap-2 data-[state=active]:bg-lia-bg-primary dark:data-[state=active]:bg-gray-700">
              <Activity className="w-4 h-4" />
              Atividades dos Agentes
            </TabsTrigger>
            <TabsTrigger value="intelligence" className="gap-2 data-[state=active]:bg-lia-bg-primary dark:data-[state=active]:bg-gray-700">
              <Brain className="w-4 h-4 text-wedo-cyan" />
              Inteligência LIA
            </TabsTrigger>
          </TabsList>

          {/* TAB 1: FUNIL & PERFORMANCE */}
          <TabsContent value="funnel">
            <div className="space-y-6">
              {/* Ações Pendentes - Centro de Ação */}
              {data.pendingActions.length > 0 && (
                <Card className="bg-status-warning/10/50 dark:bg-status-warning/10">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base font-sans flex items-center gap-2 text-status-warning dark:text-status-warning">
                      <AlertTriangle className="w-5 h-5" />
                      Ações Pendentes
                      <Badge className="bg-status-warning/15 text-status-warning ml-2">
                        {data.pendingActions.reduce((acc, a) => acc + a.count, 0)} itens
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                      {data.pendingActions.map((action, index) => (
                        <div
                          key={`action-${index}`}
                          className={`p-3 rounded-md ${
                            action.priority === 'crítica'
                              ? 'bg-status-error/10 dark:bg-status-error/20'
                              : action.priority === 'alta'
                              ? 'bg-status-warning/10 dark:bg-status-warning/20'
                              : 'bg-gray-50 dark:bg-lia-bg-secondary'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">
                              {action.count}
                            </span>
                            <Badge
                              variant={action.priority === 'crítica' ? 'destructive' : 'outline'}
                              className="text-xs"
                            >
                              {action.priority}
                            </Badge>
                          </div>
                          <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">{action.message}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* KPIs Principais */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="bg-gray-100 dark:bg-lia-bg-secondary">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <Briefcase className="w-8 h-8 text-lia-text-secondary" />
                      <div className={`flex items-center text-xs font-medium ${data.trends.jobs.trend === 'up' ? 'text-status-success' : 'text-status-error'}`}>
                        {data.trends.jobs.trend === 'up' ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                        {data.trends.jobs.change > 0 ? '+' : ''}{data.trends.jobs.change}%
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">{data.summary.activeJobs}</div>
                    <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">Vagas Ativas</div>
                    <div className="text-xs text-lia-text-secondary mt-1">
                      <span className="text-status-warning font-medium">{data.summary.urgentJobs}</span> urgentes,{" "}
                      <span className="text-status-error font-medium">{data.summary.criticalJobs}</span> críticas
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-status-success/10 dark:bg-status-success/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <Users className="w-8 h-8 text-status-success" />
                      <div className={`flex items-center text-xs font-medium ${data.trends.candidates.trend === 'up' ? 'text-status-success' : 'text-status-error'}`}>
                        {data.trends.candidates.trend === 'up' ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                        {data.trends.candidates.change > 0 ? '+' : ''}{data.trends.candidates.change}%
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">{data.summary.totalCandidates.toLocaleString()}</div>
                    <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">Candidatos no Período</div>
                  </CardContent>
                </Card>

                <Card className="bg-wedo-purple/10 dark:bg-wedo-purple/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <UserCheck className="w-8 h-8 text-wedo-purple" />
                      <div className={`flex items-center text-xs font-medium ${data.trends.hires.trend === 'up' ? 'text-status-success' : 'text-status-error'}`}>
                        {data.trends.hires.trend === 'up' ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                        {data.trends.hires.change > 0 ? '+' : ''}{data.trends.hires.change}%
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">{data.summary.totalHires}</div>
                    <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">Contratações</div>
                    <div className="text-xs text-lia-text-secondary mt-1">
                      <span className="text-status-success font-medium">{data.summary.conversionRate}%</span> taxa de conversão
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-wedo-orange/10 dark:bg-wedo-orange/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <Clock className="w-8 h-8 text-wedo-orange" />
                      <div className={`flex items-center text-xs font-medium ${data.trends.timeToHire.change < 0 ? 'text-status-success' : 'text-status-error'}`}>
                        {data.trends.timeToHire.change < 0 ? <TrendingDown className="w-3 h-3 mr-1" /> : <TrendingUp className="w-3 h-3 mr-1" />}
                        {Math.abs(data.trends.timeToHire.change)}%
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">{data.summary.averageTimeToHire}d</div>
                    <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">Tempo Médio de Contratação</div>
                    <div className="text-xs text-lia-text-secondary mt-1">
                      Mercado: <span className="font-medium">{data.benchmarks.industryAverages.timeToHire}d</span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Funil Visual + Performance por Departamento */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Funil Visual */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base font-sans flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                      Funil de Recrutamento
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {[
                        { stage: "Candidatos", count: data.recruitmentFunnel.total, color: "bg-gray-700 dark:bg-lia-text-tertiary", pct: 100 },
                        { stage: "Triagem", count: data.recruitmentFunnel.screening, color: "bg-gray-50 dark:bg-lia-bg-primary0", pct: Math.round((data.recruitmentFunnel.screening / data.recruitmentFunnel.total) * 100) },
                        { stage: "Entrevistas", count: data.recruitmentFunnel.interview, color: "bg-status-warning", pct: Math.round((data.recruitmentFunnel.interview / data.recruitmentFunnel.total) * 100) },
                        { stage: "Fase Final", count: data.recruitmentFunnel.final, color: "bg-wedo-orange", pct: Math.round((data.recruitmentFunnel.final / data.recruitmentFunnel.total) * 100) },
                        { stage: "Contratados", count: data.recruitmentFunnel.hired, color: "bg-status-success", pct: Math.round((data.recruitmentFunnel.hired / data.recruitmentFunnel.total) * 100) }
                      ].map((stage, index) => (
                        <div key={stage.stage} className="flex items-center gap-3">
                          <div className="w-20 text-xs font-medium text-lia-text-secondary dark:text-lia-text-tertiary text-right">{stage.stage}</div>
                          <div className="flex-1 relative h-7 bg-gray-100 dark:bg-lia-bg-elevated rounded-md overflow-hidden">
                            <div
                              className={`h-full ${stage.color} flex items-center px-2`}
                              style={{width: `${Math.max(stage.pct, 8)}%`}}
                            >
                              <span className="text-xs font-bold text-white">{stage.count}</span>
                            </div>
                          </div>
                          <div className="w-10 text-xs text-lia-text-secondary text-right">{stage.pct}%</div>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 pt-3 flex justify-between text-sm">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Taxa de Conversão:</span>
                      <span className="font-bold text-status-success">
                        {Math.round((data.recruitmentFunnel.hired / data.recruitmentFunnel.total) * 100)}%
                      </span>
                    </div>
                  </CardContent>
                </Card>

                {/* Performance por Departamento */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base font-sans flex items-center gap-2">
                      <Building className="w-5 h-5 text-lia-text-primary dark:text-lia-text-primary" />
                      Performance por Departamento
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {data.departmentMetrics.map((dept, index) => (
                        <div key={dept.department} className="flex items-center gap-3 p-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800">
                          <div className="w-24 font-medium text-sm text-lia-text-primary dark:text-lia-text-primary">{dept.department}</div>
                          <div className="flex-1 grid grid-cols-4 gap-2 text-center text-xs">
                            <div>
                              <div className="font-bold text-lia-text-primary dark:text-lia-text-primary">{dept.jobs}</div>
                              <div className="text-lia-text-secondary">vagas</div>
                            </div>
                            <div>
                              <div className="font-bold text-lia-text-primary dark:text-lia-text-primary">{dept.candidates}</div>
                              <div className="text-lia-text-secondary">candidatos</div>
                            </div>
                            <div>
                              <div className={`font-bold ${dept.avgTime <= 28 ? 'text-status-success' : dept.avgTime <= 35 ? 'text-status-warning' : 'text-status-error'}`}>
                                {dept.avgTime}d
                              </div>
                              <div className="text-lia-text-secondary">tempo</div>
                            </div>
                            <div>
                              <div className={`font-bold ${dept.conversion >= 60 ? 'text-status-success' : dept.conversion >= 40 ? 'text-status-warning' : 'text-status-error'}`}>
                                {dept.conversion}%
                              </div>
                              <div className="text-lia-text-secondary">conversão</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Top Vagas */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base font-sans flex items-center gap-2">
                    <Star className="w-5 h-5 text-status-warning" />
                    Vagas com Melhor Performance
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {data.topPerformingJobs.map((job, index) => (
                      <div key={job.id} className="p-4 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <div className="font-medium text-lia-text-primary dark:text-lia-text-primary text-sm">{job.title}</div>
                            <Badge variant="outline" className="text-xs mt-1">{job.department}</Badge>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold text-status-success">{job.conversion}%</div>
                            <div className="text-xs text-lia-text-secondary">conversão</div>
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-2 mt-3 text-center text-xs">
                          <div className="p-2 bg-gray-100 dark:bg-lia-bg-elevated rounded-md">
                            <div className="font-bold text-lia-text-primary dark:text-lia-text-primary">{job.candidates}</div>
                            <div className="text-lia-text-secondary">candidatos</div>
                          </div>
                          <div className="p-2 bg-gray-100 dark:bg-lia-bg-elevated rounded-md">
                            <div className="font-bold text-lia-text-primary dark:text-lia-text-primary">{job.hires}</div>
                            <div className="text-lia-text-secondary">contratados</div>
                          </div>
                          <div className="p-2 bg-gray-100 dark:bg-lia-bg-elevated rounded-md">
                            <div className="font-bold text-lia-text-primary dark:text-lia-text-primary">{job.avgTime}d</div>
                            <div className="text-lia-text-secondary">tempo</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* TAB 2: VISÃO ESTRATÉGICA */}
          <TabsContent value="strategic">
            <div className="space-y-6">
              {/* Métricas Estratégicas + Financeiro */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <Card className="bg-gray-100 dark:bg-lia-bg-secondary">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-lia-text-secondary dark:text-lia-text-secondary">{data.strategicMetrics.employeeSatisfaction}</div>
                    <div className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">Satisfação</div>
                    <div className="text-xs text-lia-text-secondary mt-1">de 5.0</div>
                  </CardContent>
                </Card>
                <Card className="bg-status-success/10 dark:bg-status-success/20">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-status-success">{data.strategicMetrics.retentionRate}%</div>
                    <div className="text-xs text-status-success">Retenção</div>
                    <div className="text-xs text-lia-text-secondary mt-1">12 meses</div>
                  </CardContent>
                </Card>
                <Card className="bg-wedo-purple/10 dark:bg-wedo-purple/20">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-wedo-purple">{data.strategicMetrics.diversityScore}%</div>
                    <div className="text-xs text-wedo-purple">Diversidade</div>
                    <div className="text-xs text-lia-text-secondary mt-1">meta: 75%</div>
                  </CardContent>
                </Card>
                <Card className="bg-wedo-orange/10 dark:bg-wedo-orange/20">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-wedo-orange">{data.summary.npsScore}</div>
                    <div className="text-xs text-wedo-orange">NPS Candidatos</div>
                    <div className="text-xs text-lia-text-secondary mt-1">mercado: {data.benchmarks.industryAverages.nps}</div>
                  </CardContent>
                </Card>
 <Card className="bg-gray-50 dark:bg-lia-bg-secondary">
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">{data.strategicMetrics.marketCompetitiveness}%</div>
                    <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">Competitividade</div>
                    <div className="text-xs text-lia-text-secondary mt-1">vs mercado</div>
                  </CardContent>
                </Card>
              </div>

              {/* Benchmark + Financeiro */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Comparação com Mercado */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base font-sans flex items-center gap-2">
                      <Trophy className="w-5 h-5 text-status-warning" />
                      Comparação com o Mercado
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                        <div className="flex items-center gap-3">
                          <Clock className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                          <span className="text-sm font-medium">Time to Hire</span>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold">{data.summary.averageTimeToHire}d</div>
                          <div className={`text-xs ${data.summary.averageTimeToHire < data.benchmarks.industryAverages.timeToHire ? 'text-status-success' : 'text-status-error'}`}>
                            {data.summary.averageTimeToHire < data.benchmarks.industryAverages.timeToHire ? '↑' : '↓'}
                            {Math.abs(data.summary.averageTimeToHire - data.benchmarks.industryAverages.timeToHire)}d vs mercado
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                        <div className="flex items-center gap-3">
                          <DollarSign className="w-5 h-5 text-status-success" />
                          <span className="text-sm font-medium">Custo por Hire</span>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold">R$ {data.summary.averageCostPerHire.toLocaleString()}</div>
                          <div className={`text-xs ${data.summary.averageCostPerHire < data.benchmarks.industryAverages.costPerHire ? 'text-status-success' : 'text-status-error'}`}>
                            {data.summary.averageCostPerHire < data.benchmarks.industryAverages.costPerHire ? '↑' : '↓'}
                            R$ {Math.abs(data.summary.averageCostPerHire - data.benchmarks.industryAverages.costPerHire).toLocaleString()} vs mercado
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                        <div className="flex items-center gap-3">
                          <Percent className="w-5 h-5 text-wedo-purple" />
                          <span className="text-sm font-medium">Taxa de Conversão</span>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold">{data.summary.conversionRate}%</div>
                          <div className={`text-xs ${data.summary.conversionRate > data.benchmarks.industryAverages.conversionRate ? 'text-status-success' : 'text-status-error'}`}>
                            {data.summary.conversionRate > data.benchmarks.industryAverages.conversionRate ? '↑' : '↓'}
                            {Math.abs(data.summary.conversionRate - data.benchmarks.industryAverages.conversionRate)}% vs mercado
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md text-center">
                      <div className="text-sm font-medium text-status-success">Posição no Mercado</div>
                      <div className="text-2xl font-bold text-status-success">Top 25%</div>
                    </div>
                  </CardContent>
                </Card>

                {/* Saúde Financeira */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base font-sans flex items-center gap-2">
                      <DollarSign className="w-5 h-5 text-status-success" />
                      Saúde Financeira
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
                          <div className="text-xs text-lia-text-secondary mb-1">Orçamento Total</div>
                          <div className="text-lg font-bold text-lia-text-primary dark:text-lia-text-primary">
                            R$ {data.financialMetrics.totalBudget.toLocaleString()}
                          </div>
                        </div>
                        <div className="p-3 bg-gray-100 dark:bg-lia-bg-secondary rounded-md">
                          <div className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mb-1">Utilizado</div>
                          <div className="text-lg font-bold text-lia-text-secondary dark:text-lia-text-secondary">
                            R$ {data.financialMetrics.spentToDate.toLocaleString()}
                          </div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs text-lia-text-secondary mb-2">
                          <span>Utilização do Orçamento</span>
                          <span className={data.financialMetrics.budgetUtilization > 90 ? 'text-status-error font-medium' : ''}>
                            {data.financialMetrics.budgetUtilization}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div
                            className={`h-3 rounded-full transition-[width,height] ${
                              data.financialMetrics.budgetUtilization > 90 ? 'bg-status-error' :
                              data.financialMetrics.budgetUtilization > 75 ? 'bg-status-warning' : 'bg-status-success'
                            }`}
                            style={{width: `${data.financialMetrics.budgetUtilization}%`}}
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md text-center">
                          <div className="text-2xl font-bold text-status-success">{data.financialMetrics.roi}%</div>
                          <div className="text-xs text-status-success">ROI</div>
                        </div>
                        <div className="p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md text-center">
                          <div className="text-2xl font-bold text-status-success">R$ {(data.financialMetrics.costSavings / 1000).toFixed(0)}k</div>
                          <div className="text-xs text-status-success">Economia</div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Riscos */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base font-sans flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-status-warning" />
                    Análise de Riscos
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {data.riskFactors.map((risk, index) => (
                      <div
                        key={risk.factor}
                        className={`p-4 rounded-md ${
                          risk.impact === 'High' ? 'bg-status-error/10 dark:bg-status-error/20' :
                          risk.impact === 'Medium' ? 'bg-status-warning/10 dark:bg-status-warning/20' :
                          'bg-gray-100 dark:bg-lia-bg-secondary'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary">{risk.factor}</span>
                          <Badge className={`text-xs ${
                            risk.impact === 'High' ? 'bg-status-error/15 text-status-error' :
                            risk.impact === 'Medium' ? 'bg-status-warning/15 text-status-warning' :
                            'bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary'
                          }`}>
                            {risk.probability}%
                          </Badge>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                          <div
                            className={`h-2 rounded-full ${
                              risk.probability > 50 ? 'bg-status-error' :
                              risk.probability > 30 ? 'bg-status-warning' : 'bg-status-success'
                            }`}
                            style={{width: `${risk.probability}%`}}
                          />
                        </div>
                        <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                          <strong>Mitigação:</strong> {risk.mitigation}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* TAB 3: ATIVIDADES DOS AGENTES */}
          <TabsContent value="agents">
            <AgentControlCenter />
          </TabsContent>

          {/* TAB 4: INTELIGÊNCIA LIA */}
          <TabsContent value="intelligence">
            <div className="space-y-6">
              <Tabs defaultValue="predictive" className="w-full">
                <TabsList className="mb-4 bg-gray-100 dark:bg-lia-bg-secondary">
                  <TabsTrigger value="predictive" className="gap-2">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    Analytics Preditivo
                  </TabsTrigger>
                  <TabsTrigger value="calibration" className="gap-2">
                    <Scale className="w-4 h-4" />
                    Calibração LIA
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="predictive">
                  <PredictiveAnalyticsTab />
                </TabsContent>

                <TabsContent value="calibration">
                  <CalibrationDashboard />
                </TabsContent>
              </Tabs>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
