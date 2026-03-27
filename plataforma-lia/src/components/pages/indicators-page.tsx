"use client"

import { useState, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ExpandableAIPrompt } from "@/components/expandable-ai-prompt"
import {
  ConversionFunnelChart,
  RecruiterPerformanceChart,
  WorkModelDistributionChart,
  PredictiveAnalyticsChart,
  InteractiveChart
} from "@/components/charts/interactive-charts"
import { AgentControlCenter } from "@/components/agent-control-center"
import {
  RecruitmentTrendsChart,
  RecruiterPerformanceRadar,
  DepartmentBudgetChart,
  DetailedFunnelChart,
  SourceEffectivenessChart,
  SkillsGapChart
} from "@/components/charts/advanced-interactive-charts"
import { KPIAlertSystem } from "@/components/alerts/kpi-alert-system"
import { AdvancedReportExporter } from "@/components/reports/advanced-report-exporter"
import { RecruitmentMLDashboard } from "@/components/ml/recruitment-ml-engine"
import {
  Users, TrendingUp, Calendar, Target, Building, Award,
  BarChart3, PieChart, LineChart, Download, Filter,
  Search, ArrowUp, ArrowDown, Trophy, Medal, Star,
  Clock, UserCheck, Zap, AlertTriangle, CheckCircle,
  ChevronDown, ChevronUp, Eye, Settings, RefreshCw,
  MapPin, Briefcase, Mail, Phone, TrendingDown,
  ChevronRight, Plus, Edit, Trash2, MoreVertical,
  Brain, Globe, Heart, Home, Mountain,
  Palette, Calculator, Accessibility, Shield,
  Layout, Activity, FileText, Archive, Save,
  Lightbulb, MessageSquare, Video, Calendar as CalendarIcon,
  DollarSign, Percent, Timer
} from "lucide-react"

// Dados dos recrutadores (mock data expandido)
const recruitersData = {
  ana_silva: {
    name: "Ana Silva",
    role: "Recrutadora Sênior",
    avatar: "/avatars/ana.jpg",
    department: "Tech",
    activeJobs: 8,
    totalJobs: 12,
    totalCandidates: 234,
    scheduledInterviews: 15,
    completedInterviews: 42,
    totalHires: 5,
    avgTimeToFill: 28,
    conversionRate: 2.1,
    npsScore: 88,
    interviewsPerWeek: 12,
    candidateResponseRate: 76,
    offerAcceptanceRate: 85,
    qualityOfHireScore: 4.2,
    // Novas métricas para ranking e metas
    ranking: 1,
    totalScore: 92.8,
    goals: {
      monthly: {
        hires: { target: 6, current: 5, status: 'on_track' },
        timeToFill: { target: 30, current: 28, status: 'achieved' },
        nps: { target: 85, current: 88, status: 'exceeded' },
        interviews: { target: 40, current: 42, status: 'exceeded' }
      },
      quarterly: {
        qualityScore: { target: 4.0, current: 4.2, status: 'exceeded' },
        conversionRate: { target: 2.0, current: 2.1, status: 'exceeded' }
      }
    },
    monthlyTrends: {
      interviews: [8, 12, 15, 18, 14, 16],
      hires: [2, 1, 3, 2, 1, 2],
      sourceQuality: [82, 85, 88, 84, 86, 89],
      nps: [85, 86, 87, 88, 87, 88],
      timeToFill: [32, 30, 29, 28, 27, 28]
    },
    sourcing: {
      linkedin: 45,
      referrals: 23,
      jobBoards: 18,
      headhunting: 14
    }
  },
  juliana_oliveira: {
    name: "Juliana Oliveira",
    role: "Recrutadora",
    avatar: "/avatars/juliana.jpg",
    department: "Design",
    activeJobs: 4,
    totalJobs: 7,
    totalCandidates: 98,
    scheduledInterviews: 6,
    completedInterviews: 24,
    totalHires: 4,
    avgTimeToFill: 25,
    conversionRate: 4.1,
    npsScore: 91,
    interviewsPerWeek: 6,
    candidateResponseRate: 84,
    offerAcceptanceRate: 92,
    qualityOfHireScore: 4.5,
    ranking: 2,
    totalScore: 89.3,
    goals: {
      monthly: {
        hires: { target: 3, current: 4, status: 'exceeded' },
        timeToFill: { target: 30, current: 25, status: 'exceeded' },
        nps: { target: 85, current: 91, status: 'exceeded' },
        interviews: { target: 20, current: 24, status: 'exceeded' }
      },
      quarterly: {
        qualityScore: { target: 4.0, current: 4.5, status: 'exceeded' },
        conversionRate: { target: 3.5, current: 4.1, status: 'exceeded' }
      }
    },
    monthlyTrends: {
      interviews: [4, 6, 8, 6, 5, 7],
      hires: [2, 1, 2, 2, 1, 2],
      sourceQuality: [85, 88, 91, 89, 87, 92],
      nps: [88, 89, 90, 91, 90, 91],
      timeToFill: [28, 27, 26, 25, 26, 25]
    },
    sourcing: {
      linkedin: 52,
      referrals: 28,
      jobBoards: 12,
      headhunting: 8
    }
  },
  carlos_mendes: {
    name: "Carlos Mendes",
    role: "Recrutador",
    avatar: "/avatars/carlos.jpg",
    department: "Sales",
    activeJobs: 6,
    totalJobs: 9,
    totalCandidates: 156,
    scheduledInterviews: 8,
    completedInterviews: 28,
    totalHires: 3,
    avgTimeToFill: 32,
    conversionRate: 1.9,
    npsScore: 82,
    interviewsPerWeek: 8,
    candidateResponseRate: 68,
    offerAcceptanceRate: 78,
    qualityOfHireScore: 3.9,
    ranking: 3,
    totalScore: 79.2,
    goals: {
      monthly: {
        hires: { target: 4, current: 3, status: 'behind' },
        timeToFill: { target: 30, current: 32, status: 'behind' },
        nps: { target: 85, current: 82, status: 'behind' },
        interviews: { target: 30, current: 28, status: 'behind' }
      },
      quarterly: {
        qualityScore: { target: 4.0, current: 3.9, status: 'behind' },
        conversionRate: { target: 2.0, current: 1.9, status: 'behind' }
      }
    },
    monthlyTrends: {
      interviews: [6, 8, 10, 8, 7, 9],
      hires: [1, 1, 2, 1, 0, 1],
      sourceQuality: [75, 78, 82, 79, 76, 81],
      nps: [78, 79, 80, 82, 81, 82],
      timeToFill: [35, 34, 33, 32, 33, 32]
    },
    sourcing: {
      linkedin: 38,
      referrals: 31,
      jobBoards: 22,
      headhunting: 9
    }
  },
  pedro_costa: {
    name: "Pedro Costa",
    role: "Head de Talent Acquisition",
    avatar: "/avatars/pedro.jpg",
    department: "Leadership",
    activeJobs: 3,
    totalJobs: 15,
    totalCandidates: 89,
    scheduledInterviews: 4,
    completedInterviews: 18,
    totalHires: 2,
    avgTimeToFill: 35,
    conversionRate: 2.2,
    npsScore: 85,
    interviewsPerWeek: 4,
    candidateResponseRate: 72,
    offerAcceptanceRate: 88,
    qualityOfHireScore: 4.3,
    ranking: 4,
    totalScore: 82.1,
    goals: {
      monthly: {
        hires: { target: 3, current: 2, status: 'behind' },
        timeToFill: { target: 30, current: 35, status: 'behind' },
        nps: { target: 85, current: 85, status: 'on_track' },
        interviews: { target: 20, current: 18, status: 'behind' }
      },
      quarterly: {
        qualityScore: { target: 4.0, current: 4.3, status: 'exceeded' },
        conversionRate: { target: 2.5, current: 2.2, status: 'behind' }
      }
    },
    monthlyTrends: {
      interviews: [3, 4, 5, 4, 3, 4],
      hires: [1, 0, 1, 1, 0, 1],
      sourceQuality: [80, 83, 85, 82, 81, 86],
      nps: [83, 84, 85, 85, 84, 85],
      timeToFill: [38, 37, 36, 35, 36, 35]
    },
    sourcing: {
      linkedin: 41,
      referrals: 35,
      jobBoards: 15,
      headhunting: 9
    }
  }
}

export function IndicatorsPage() {
  const [activeTab, setActiveTab] = useState<'strategic' | 'recruiters' | 'alerts' | 'work_models' | 'predictions' | 'agent_control'>('recruiters')
  const [selectedPeriod, setSelectedPeriod] = useState('current_month')
  const [selectedDepartments, setSelectedDepartments] = useState<string[]>([])
  const [selectedRecruiters, setSelectedRecruiters] = useState<string[]>([])
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [viewMode, setViewMode] = useState<'cards' | 'ranking' | 'goals' | 'comparison'>('cards')
  const [sortBy, setSortBy] = useState('totalScore')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [selectedCandidates, setSelectedCandidates] = useState<any[]>([])
  const [showExportModal, setShowExportModal] = useState(false)

  // Filtros específicos para recrutadores
  const recruiters = Object.values(recruitersData)
  const departments = [...new Set(recruiters.map(r => r.department))]

  // Aplicar filtros
  const filteredRecruiters = useMemo(() => {
    const filtered = recruiters
      // Filtrar por departamento
      .filter(r => selectedDepartments.length === 0 || selectedDepartments.includes(r.department))
      // Filtrar por recrutadores específicos
      .filter(r => selectedRecruiters.length === 0 || selectedRecruiters.includes(r.name))

    // Ordenar (criar cópia para não mutar)
    return [...filtered].sort((a, b) => {
      const aVal = a[sortBy as keyof typeof a] as number
      const bVal = b[sortBy as keyof typeof b] as number
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal
    })
  }, [selectedDepartments, selectedRecruiters, sortBy, sortOrder, recruiters])

  // Métricas consolidadas da equipe
  const teamMetrics = useMemo(() => {
    const total = recruiters.reduce((acc, r) => ({
      activeJobs: acc.activeJobs + r.activeJobs,
      totalCandidates: acc.totalCandidates + r.totalCandidates,
      totalHires: acc.totalHires + r.totalHires,
      completedInterviews: acc.completedInterviews + r.completedInterviews
    }), { activeJobs: 0, totalCandidates: 0, totalHires: 0, completedInterviews: 0 })

    const avgConversionRate = (recruiters.reduce((acc, r) => acc + r.conversionRate, 0) / recruiters.length).toFixed(1)
    const avgTimeToFill = Math.round(recruiters.reduce((acc, r) => acc + r.avgTimeToFill, 0) / recruiters.length)
    const avgNPS = Math.round(recruiters.reduce((acc, r) => acc + r.npsScore, 0) / recruiters.length)
    const avgQualityScore = (recruiters.reduce((acc, r) => acc + r.qualityOfHireScore, 0) / recruiters.length).toFixed(1)

    return {
      ...total,
      avgConversionRate,
      avgTimeToFill,
      avgNPS,
      avgQualityScore,
      totalRecruiters: recruiters.length
    }
  }, [recruiters])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'exceeded': return 'text-green-600 bg-green-100'
      case 'achieved': return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800'
      case 'on_track': return 'text-yellow-600 bg-yellow-100'
      case 'behind': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getRankingIcon = (ranking: number) => {
    switch (ranking) {
      case 1: return <Trophy className="w-5 h-5 text-yellow-500" />
      case 2: return <Medal className="w-5 h-5 text-gray-600" />
      case 3: return <Medal className="w-5 h-5 text-amber-600" />
      default: return <div className="w-5 h-5 flex items-center justify-center text-sm font-bold text-gray-800 dark:text-gray-200">{ranking}</div>
    }
  }

  const tabs = [
    { id: 'strategic', label: 'Indicadores Estratégicos', icon: TrendingUp },
    { id: 'recruiters', label: 'Performance dos Recrutadores', icon: Users },
    { id: 'alerts', label: 'Alertas e Monitoramento', icon: AlertTriangle },
    { id: 'work_models', label: 'Modelos de Trabalho', icon: Globe },
    { id: 'predictions', label: 'Previsões e Tendências', icon: Brain },
    { id: 'agent_control', label: 'Centro de Controle IA', icon: Brain }
  ]

  const viewModes = [
    { id: 'cards', label: 'Cards Individuais', icon: Layout },
    { id: 'ranking', label: 'Ranking Geral', icon: Trophy },
    { id: 'goals', label: 'Metas e Objetivos', icon: Target },
    { id: 'comparison', label: 'Comparação', icon: BarChart3 }
  ]

  const handleCommandAction = (command: string, action: string) => {
    console.log('Executando comando LIA:', { command, action })
    // Implementar ações da LIA aqui
  }

  const handleAlertAction = (alertId: string, action: string) => {
    console.log('Ação do alerta:', { alertId, action })
    // Implementar ações específicas do sistema de alertas
    switch (action) {
      case 'mark_read':
        console.log('Marcando alerta como lido:', alertId)
        break
      case 'archive':
        console.log('Arquivando alerta:', alertId)
        break
      case 'delete':
        console.log('Deletando alerta:', alertId)
        break
      case 'send_notification':
        console.log('Enviando notificação para:', alertId)
        break
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-950 dark:text-gray-50">
            Indicadores e Analytics
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Dashboard executivo com insights estratégicos e performance de recrutadores
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            className="gap-2"
            onClick={() => setShowExportModal(true)}
          >
            <Download className="w-4 h-4" />
            Exportar Relatório
          </Button>
          <Button variant="outline" className="gap-2">
            <RefreshCw className="w-4 h-4" />
            Atualizar Dados
          </Button>
        </div>
      </div>

      {/* LIA Prompt */}
      <ExpandableAIPrompt
        selectedCandidates={selectedCandidates}
        onCommand={handleCommandAction}
        filteredCount={filteredRecruiters.length}
        totalCount={recruiters.length}
      />

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex space-x-8">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-1 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-gray-900 dark:border-gray-50 text-gray-600 dark:text-gray-400'
 : 'border-transparent text-gray-800 hover:text-gray-800 dark:hover:text-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Performance dos Recrutadores Tab */}
      {activeTab === 'recruiters' && (
        <div className="space-y-6">
          {/* Filtros Avançados */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Filter className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  Filtros Avançados
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                  className="gap-2"
                >
                  {showAdvancedFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  {showAdvancedFilters ? 'Ocultar' : 'Expandir'}
                </Button>
              </div>
            </CardHeader>
            {showAdvancedFilters && (
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {/* Período */}
                  <div>
                    <label className="text-sm font-medium mb-2 block text-gray-950 dark:text-gray-50">
                      Período
                    </label>
                    <select
                      value={selectedPeriod}
                      onChange={(e) => setSelectedPeriod(e.target.value)}
                      className="w-full p-2 rounded-md text-sm bg-gray-50 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 text-gray-800 dark:text-gray-200"
                    >
                      <option value="current_month">Este Mês</option>
                      <option value="last_month">Mês Passado</option>
                      <option value="quarter">Este Trimestre</option>
                      <option value="year">Este Ano</option>
                    </select>
                  </div>

                  {/* Departamentos */}
                  <div>
                    <label className="text-sm font-medium mb-2 block text-gray-950 dark:text-gray-50">
                      Departamentos
                    </label>
                    <div className="space-y-2">
                      {departments.map(dept => (
                        <label key={dept} className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={selectedDepartments.includes(dept)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedDepartments([...selectedDepartments, dept])
                              } else {
                                setSelectedDepartments(selectedDepartments.filter(d => d !== dept))
                              }
                            }}
                            className="rounded"
                          />
                          {dept}
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Ordenação */}
                  <div>
                    <label className="text-sm font-medium mb-2 block text-gray-950 dark:text-gray-50">
                      Ordenar por
                    </label>
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value)}
                      className="w-full p-2 rounded-md text-sm mb-2 bg-gray-50 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 text-gray-800 dark:text-gray-200"
                    >
                      <option value="totalScore">Score Total</option>
                      <option value="npsScore">NPS</option>
                      <option value="conversionRate">Taxa Conversão</option>
                      <option value="avgTimeToFill">Time to Fill</option>
                      <option value="totalHires">Total Contratações</option>
                    </select>
                    <select
                      value={sortOrder}
                      onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
                      className="w-full p-2 rounded-md text-sm bg-gray-50 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 text-gray-800 dark:text-gray-200"
                    >
                      <option value="desc">Maior para Menor</option>
                      <option value="asc">Menor para Maior</option>
                    </select>
                  </div>

                  {/* Ações Rápidas */}
                  <div>
                    <label className="text-sm font-medium mb-2 block text-gray-950 dark:text-gray-50">
                      Ações Rápidas
                    </label>
                    <div className="space-y-2">
                      <Button variant="outline" size="sm" className="w-full gap-2">
                        <Eye className="w-3 h-3" />
                        Ver Top Performers
                      </Button>
                      <Button variant="outline" size="sm" className="w-full gap-2">
                        <AlertTriangle className="w-3 h-3" />
                        Alertas de Performance
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Badges de Filtros Aplicados */}
                {(selectedDepartments.length > 0 || selectedRecruiters.length > 0) && (
                  <div className="flex flex-wrap gap-2 pt-4 border-t">
                    {selectedDepartments.map(dept => (
                      <Badge key={dept} variant="outline" className="gap-1">
                        {dept}
                        <button
                          onClick={() => setSelectedDepartments(selectedDepartments.filter(d => d !== dept))}
                          className="ml-1 hover:text-red-600"
                        >
                          ×
                        </button>
                      </Badge>
                    ))}
                    {selectedRecruiters.map(name => (
                      <Badge key={name} variant="outline" className="gap-1">
                        {name}
                        <button
                          onClick={() => setSelectedRecruiters(selectedRecruiters.filter(n => n !== name))}
                          className="ml-1 hover:text-red-600"
                        >
                          ×
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            )}
          </Card>

          {/* Métricas Consolidadas da Equipe */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="border-gray-300 dark:border-gray-600">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">Total Recrutadores</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-50">{teamMetrics.totalRecruiters}</p>
                  </div>
                  <Users className="w-8 h-8 text-gray-600 dark:text-gray-400" />
                </div>
                <div className="mt-2 flex items-center gap-1 text-xs">
                  <TrendingUp className="w-3 h-3 text-green-600" />
                  <span className="text-green-600">+12% vs mês anterior</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-green-200 dark:border-green-800">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-green-600 font-medium">Contratações Total</p>
                    <p className="text-2xl font-bold text-green-700">{teamMetrics.totalHires}</p>
                  </div>
                  <UserCheck className="w-8 h-8 text-green-600" />
                </div>
                <div className="mt-2 flex items-center gap-1 text-xs">
                  <TrendingUp className="w-3 h-3 text-green-600" />
                  <span className="text-green-600">Taxa: {teamMetrics.avgConversionRate}%</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-purple-200 dark:border-purple-800">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-purple-600 font-medium">Time to Fill Médio</p>
                    <p className="text-2xl font-bold text-purple-700">{teamMetrics.avgTimeToFill} dias</p>
                  </div>
                  <Timer className="w-8 h-8 text-purple-600" />
                </div>
                <div className="mt-2 flex items-center gap-1 text-xs">
                  <TrendingDown className="w-3 h-3 text-green-600" />
                  <span className="text-green-600">-3 dias vs meta</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-orange-200 dark:border-orange-800">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-orange-600 font-medium">NPS Médio Equipe</p>
                    <p className="text-2xl font-bold text-orange-700">{teamMetrics.avgNPS}%</p>
                  </div>
                  <Star className="w-8 h-8 text-orange-600" />
                </div>
                <div className="mt-2 flex items-center gap-1 text-xs">
                  <TrendingUp className="w-3 h-3 text-green-600" />
                  <span className="text-green-600">+5% vs trimestre</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Modos de Visualização */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Modos de Visualização</CardTitle>
                <div className="flex gap-2">
                  {viewModes.map(mode => (
                    <Button
                      key={mode.id}
                      variant={viewMode === mode.id ? "default" : "outline"}
                      size="sm"
                      onClick={() => setViewMode(mode.id as any)}
                      className="gap-2"
                    >
                      <mode.icon className="w-4 h-4" />
                      {mode.label}
                    </Button>
                  ))}
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Alertas Rápidos */}
          <Card className="border-l-4 border-l-orange-500">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
                Alertas Rápidos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-red-50 rounded-md">
                  <div className="text-2xl font-bold text-red-600">2</div>
                  <div className="text-sm text-red-700">Alertas Críticos</div>
                  <div className="text-xs text-red-600 mt-1">Time to Fill &gt; 45 dias</div>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-md">
                  <div className="text-2xl font-bold text-yellow-600">5</div>
                  <div className="text-sm text-yellow-700">Avisos</div>
                  <div className="text-xs text-yellow-600 mt-1">NPS abaixo da meta</div>
                </div>
                <div className="text-center p-4 bg-gray-100 dark:bg-gray-800 rounded-md">
                  <div className="text-2xl font-bold text-gray-900 dark:text-gray-50">12</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Monitoramentos</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">KPIs em observação</div>
                </div>
              </div>
              <div className="mt-4">
                <Button
                  variant="outline"
                  className="w-full gap-2"
                  onClick={() => setActiveTab('alerts')}
                >
                  <AlertTriangle className="w-4 h-4" />
                  Ver Todos os Alertas
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Gráficos Avançados de Performance */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RecruiterPerformanceRadar />
            <RecruitmentTrendsChart />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <DetailedFunnelChart />
            <SourceEffectivenessChart />
          </div>

          {/* Conteúdo baseado no modo de visualização */}
          {viewMode === 'cards' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
              {filteredRecruiters.map((recruiter) => (
                <Card key={recruiter.name} className="relative">
                  <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Avatar className="w-12 h-12">
                          <AvatarImage src={recruiter.avatar} alt={recruiter.name} />
                          <AvatarFallback className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium">
                            {recruiter.name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-gray-950 dark:text-gray-50">
                              {recruiter.name}
                            </h3>
                            {getRankingIcon(recruiter.ranking)}
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{recruiter.role}</p>
                          <Badge variant="outline" className="mt-1 text-xs">
                            {recruiter.department}
                          </Badge>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-gray-900 dark:text-gray-50">
                          {recruiter.totalScore}
                        </div>
                        <div className="text-xs text-gray-800 dark:text-gray-200">Score Total</div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* KPIs Principais */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                        <div className="text-lg font-bold text-gray-950 dark:text-gray-50">
                          {recruiter.totalHires}
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">Contratações</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                        <div className="text-lg font-bold text-gray-950 dark:text-gray-50">
                          {recruiter.avgTimeToFill}d
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">Time to Fill</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                        <div className="text-lg font-bold text-gray-950 dark:text-gray-50">
                          {recruiter.npsScore}%
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">NPS Score</div>
                      </div>
                      <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                        <div className="text-lg font-bold text-gray-950 dark:text-gray-50">
                          {recruiter.conversionRate}%
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">Conversão</div>
                      </div>
                    </div>

                    {/* Metas Mensais */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-950 dark:text-gray-50 mb-2">
                        Metas Mensais
                      </h4>
                      <div className="space-y-2">
                        {Object.entries(recruiter.goals.monthly).map(([key, goal]) => (
                          <div key={key} className="flex items-center justify-between text-sm">
                            <span className="text-gray-600 dark:text-gray-400 capitalize">
                              {key === 'hires' ? 'Contratações' :
                               key === 'timeToFill' ? 'Time to Fill' :
                               key === 'nps' ? 'NPS' : 'Entrevistas'}:
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="text-gray-950 dark:text-gray-50">
                                {goal.current}/{goal.target}
                              </span>
                              <Badge className={`text-xs ${getStatusColor(goal.status)}`}>
                                {goal.status === 'exceeded' ? 'Superou' :
                                 goal.status === 'achieved' ? 'Atingiu' :
                                 goal.status === 'on_track' ? 'No prazo' : 'Atrasado'}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Distribuição de Sourcing */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-950 dark:text-gray-50 mb-2">
                        Fontes de Candidatos
                      </h4>
                      <div className="grid grid-cols-4 gap-2 text-xs">
                        <div className="text-center">
                          <div className="font-medium text-gray-600 dark:text-gray-400">{recruiter.sourcing.linkedin}%</div>
                          <div className="text-gray-800 dark:text-gray-200">LinkedIn</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium text-green-600">{recruiter.sourcing.referrals}%</div>
                          <div className="text-gray-800 dark:text-gray-200">Indicações</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium text-orange-600">{recruiter.sourcing.jobBoards}%</div>
                          <div className="text-gray-800 dark:text-gray-200">Job Boards</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium text-purple-600">{recruiter.sourcing.headhunting}%</div>
                          <div className="text-gray-800 dark:text-gray-200">Headhunt</div>
                        </div>
                      </div>
                    </div>

                    {/* Ações */}
                    <div className="flex gap-2 pt-2 border-t">
                      <Button variant="outline" size="sm" className="flex-1 gap-2">
                        <Eye className="w-3 h-3" />
                        Ver Detalhes
                      </Button>
                      <Button variant="outline" size="sm" className="gap-2">
                        <Settings className="w-3 h-3" />
                        Metas
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {viewMode === 'ranking' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="w-5 h-5 text-yellow-500" />
                  Ranking Geral dos Recrutadores
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {filteredRecruiters.map((recruiter, index) => (
                    <div key={recruiter.name} className={`flex items-center gap-4 p-4 rounded-md border ${
                      index === 0 ? 'bg-yellow-50 border-yellow-200' :
                      index === 1 ? 'bg-gray-50 border-gray-200' :
                      index === 2 ? 'bg-amber-50 border-amber-200' :
                      'bg-white border-gray-100'
                    }`}>
                      <div className="flex items-center gap-3">
                        {getRankingIcon(recruiter.ranking)}
                        <Avatar className="w-10 h-10">
                          <AvatarImage src={recruiter.avatar} alt={recruiter.name} />
                          <AvatarFallback className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium">
                            {recruiter.name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-semibold text-gray-950 dark:text-gray-50">{recruiter.name}</div>
                          <div className="text-sm text-gray-600">{recruiter.role} • {recruiter.department}</div>
                        </div>
                      </div>

                      <div className="flex-1 grid grid-cols-5 gap-4 text-center">
                        <div>
                          <div className="text-lg font-bold text-gray-900 dark:text-gray-50">{recruiter.totalScore}</div>
                          <div className="text-xs text-gray-800 dark:text-gray-200">Score Total</div>
                        </div>
                        <div>
                          <div className="text-lg font-bold text-green-600">{recruiter.totalHires}</div>
                          <div className="text-xs text-gray-800 dark:text-gray-200">Contratações</div>
                        </div>
                        <div>
                          <div className="text-lg font-bold text-purple-600">{recruiter.avgTimeToFill}d</div>
                          <div className="text-xs text-gray-800 dark:text-gray-200">Time to Fill</div>
                        </div>
                        <div>
                          <div className="text-lg font-bold text-orange-600">{recruiter.npsScore}%</div>
                          <div className="text-xs text-gray-800 dark:text-gray-200">NPS</div>
                        </div>
                        <div>
                          <div className="text-lg font-bold text-red-600">{recruiter.conversionRate}%</div>
                          <div className="text-xs text-gray-800 dark:text-gray-200">Conversão</div>
                        </div>
                      </div>

                      <div className="text-right">
                        {index < 3 && (
                          <Badge className={`${
                            index === 0 ? 'bg-yellow-100 text-yellow-800' :
                            index === 1 ? 'bg-gray-100 text-gray-800' :
                            'bg-amber-100 text-amber-800'
                          }`}>
                            #{recruiter.ranking}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {viewMode === 'goals' && (
            <div className="space-y-6">
              {filteredRecruiters.map((recruiter) => (
                <Card key={recruiter.name}>
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <Avatar className="w-10 h-10">
                        <AvatarImage src={recruiter.avatar} alt={recruiter.name} />
                        <AvatarFallback className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium">
                          {recruiter.name.split(' ').map(n => n[0]).join('')}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <CardTitle>{recruiter.name}</CardTitle>
                        <p className="text-sm text-gray-600">{recruiter.role} • {recruiter.department}</p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Metas Mensais */}
                      <div>
                        <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-4 flex items-center gap-2">
                          <CalendarIcon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                          Metas Mensais
                        </h4>
                        <div className="space-y-4">
                          {Object.entries(recruiter.goals.monthly).map(([key, goal]) => (
                            <div key={key} className="space-y-2">
                              <div className="flex items-center justify-between text-sm">
                                <span className="font-medium capitalize">
                                  {key === 'hires' ? 'Contratações' :
                                   key === 'timeToFill' ? 'Time to Fill (dias)' :
                                   key === 'nps' ? 'NPS Score' : 'Entrevistas'}
                                </span>
                                <div className="flex items-center gap-2">
                                  <span className="text-gray-950 dark:text-gray-50">{goal.current}/{goal.target}</span>
                                  <Badge className={`text-xs ${getStatusColor(goal.status)}`}>
                                    {goal.status === 'exceeded' ? 'Superou' :
                                     goal.status === 'achieved' ? 'Atingiu' :
                                     goal.status === 'on_track' ? 'No prazo' : 'Atrasado'}
                                  </Badge>
                                </div>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full transition-all duration-300 ${
                                    goal.status === 'exceeded' ? 'bg-green-500' :
                                    goal.status === 'achieved' ? 'bg-blue-500' :
                                    goal.status === 'on_track' ? 'bg-yellow-500' : 'bg-red-500'
                                  }`}
                                  style={{
                                    width: `${Math.min((goal.current / goal.target) * 100, 100)}%`
                                  }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Metas Trimestrais */}
                      <div>
                        <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-4 flex items-center gap-2">
                          <Target className="w-4 h-4 text-purple-600" />
                          Metas Trimestrais
                        </h4>
                        <div className="space-y-4">
                          {Object.entries(recruiter.goals.quarterly).map(([key, goal]) => (
                            <div key={key} className="space-y-2">
                              <div className="flex items-center justify-between text-sm">
                                <span className="font-medium capitalize">
                                  {key === 'qualityScore' ? 'Score de Qualidade' : 'Taxa de Conversão (%)'}
                                </span>
                                <div className="flex items-center gap-2">
                                  <span className="text-gray-950 dark:text-gray-50">{goal.current}/{goal.target}</span>
                                  <Badge className={`text-xs ${getStatusColor(goal.status)}`}>
                                    {goal.status === 'exceeded' ? 'Superou' :
                                     goal.status === 'achieved' ? 'Atingiu' :
                                     goal.status === 'on_track' ? 'No prazo' : 'Atrasado'}
                                  </Badge>
                                </div>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full transition-all duration-300 ${
                                    goal.status === 'exceeded' ? 'bg-green-500' :
                                    goal.status === 'achieved' ? 'bg-blue-500' :
                                    goal.status === 'on_track' ? 'bg-yellow-500' : 'bg-red-500'
                                  }`}
                                  style={{
                                    width: `${Math.min((goal.current / goal.target) * 100, 100)}%`
                                  }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Ações para Metas */}
                    <div className="flex gap-2 mt-6 pt-4 border-t">
                      <Button variant="outline" size="sm" className="gap-2">
                        <Edit className="w-3 h-3" />
                        Editar Metas
                      </Button>
                      <Button variant="outline" size="sm" className="gap-2">
                        <Plus className="w-3 h-3" />
                        Nova Meta
                      </Button>
                      <Button variant="outline" size="sm" className="gap-2">
                        <BarChart3 className="w-3 h-3" />
                        Ver Histórico
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {viewMode === 'comparison' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-purple-600" />
                  Comparação de Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Comparação por Métricas */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-4">Contratações por Recrutador</h4>
                      <div className="space-y-3">
                        {filteredRecruiters.map((recruiter) => (
                          <div key={recruiter.name} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Avatar className="w-6 h-6">
                                <AvatarFallback className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs">
                                  {recruiter.name.split(' ').map(n => n[0]).join('')}
                                </AvatarFallback>
                              </Avatar>
                              <span className="text-sm">{recruiter.name}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="w-20 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-gray-700 dark:bg-gray-300 h-2 rounded-full"
                                  style={{
                                    width: `${(recruiter.totalHires / Math.max(...filteredRecruiters.map(r => r.totalHires))) * 100}%`
                                  }}
                                />
                              </div>
                              <span className="text-sm font-medium w-8 text-right">{recruiter.totalHires}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-4">NPS Score por Recrutador</h4>
                      <div className="space-y-3">
                        {filteredRecruiters.map((recruiter) => (
                          <div key={recruiter.name} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Avatar className="w-6 h-6">
                                <AvatarFallback className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-xs">
                                  {recruiter.name.split(' ').map(n => n[0]).join('')}
                                </AvatarFallback>
                              </Avatar>
                              <span className="text-sm">{recruiter.name}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="w-20 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-green-500 h-2 rounded-full"
                                  style={{
                                    width: `${recruiter.npsScore}%`
                                  }}
                                />
                              </div>
                              <span className="text-sm font-medium w-8 text-right">{recruiter.npsScore}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Gráfico de Tendências (simulado) */}
                  <div>
                    <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-4">Tendências de Performance (Últimos 6 Meses)</h4>
                    <div className="bg-gray-50 p-6 rounded-md text-center">
                      <LineChart className="w-12 h-12 text-gray-600 mx-auto mb-2" />
                      <p className="text-gray-600 text-sm">
                        Gráfico interativo de tendências seria exibido aqui
                      </p>
                      <p className="text-xs text-gray-800 dark:text-gray-200 mt-1">
                        Mostrando evolução de KPIs, sazonalidades e comparações
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Alertas e Monitoramento Tab */}
      {activeTab === 'alerts' && (
        <div className="space-y-6">
          <KPIAlertSystem
            recruiterData={recruiters}
            onAlertAction={handleAlertAction}
          />
        </div>
      )}

      {/* Indicadores Estratégicos Tab */}
      {activeTab === 'strategic' && (
        <div className="space-y-6">
          {/* KPIs Estratégicos Principais */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="border-green-200">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-green-600" />
                  Taxa de Crescimento
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-700">+24.8%</div>
                <div className="text-xs text-green-600 mt-1">vs trimestre anterior</div>
                <div className="mt-3 text-xs text-gray-600">
                  Contratações cresceram 35% e pipeline aumentou 18%
                </div>
              </CardContent>
            </Card>

            <Card className="border-gray-300 dark:border-gray-600">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Target className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  Eficiência Operacional
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-50">87.3%</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Metas atingidas</div>
                <div className="mt-3 text-xs text-gray-600">
                  94% das vagas preenchidas dentro do prazo
                </div>
              </CardContent>
            </Card>

            <Card className="border-purple-200">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Users className="w-4 h-4 text-purple-600" />
                  Qualidade da Contratação
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-700">4.6/5.0</div>
                <div className="text-xs text-purple-600 mt-1">Score médio</div>
                <div className="mt-3 text-xs text-gray-600">
                  89% dos contratados ainda na empresa após 6 meses
                </div>
              </CardContent>
            </Card>

            <Card className="border-orange-200">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-orange-600" />
                  ROI em Recrutamento
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-700">325%</div>
                <div className="text-xs text-orange-600 mt-1">Retorno sobre investimento</div>
                <div className="mt-3 text-xs text-gray-600">
                  Economia de R$ 2.4M em terceirização
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Indicadores de Performance Avançados */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Gráfico Interativo de Funil de Conversão */}
            <ConversionFunnelChart />

            {/* Análise de Skills Gap */}
            <SkillsGapChart />

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-green-600" />
                  Time to Fill por Senioridade
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { level: 'Júnior', days: 18, color: 'bg-green-500', target: 20 },
                    { level: 'Pleno', days: 28, color: 'bg-gray-700 dark:bg-gray-300', target: 30 },
                    { level: 'Sênior', days: 42, color: 'bg-yellow-500', target: 45 },
                    { level: 'Liderança', days: 67, color: 'bg-red-500', target: 60 }
                  ].map((item, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>{item.level}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{item.days} dias</span>
                          <Badge className={item.days <= item.target ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}>
                            {item.days <= item.target ? '✓' : '!'}
                          </Badge>
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`${item.color} h-2 rounded-full transition-all duration-300`}
                          style={{width: `${Math.min((item.days / 70) * 100, 100)}%`}}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Análise de Orçamento por Departamento */}
          <DepartmentBudgetChart />

          {/* Análise de Diversidade e Inclusão */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Heart className="w-5 h-5 text-pink-600" />
                Diversidade e Inclusão
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-3">Distribuição por Gênero</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Feminino</span>
                      <span className="font-medium">47%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-pink-500 h-2 rounded-full" style={{width: '47%'}}></div>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Masculino</span>
                      <span className="font-medium">51%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-gray-700 dark:bg-gray-300 h-2 rounded-full" style={{width: '51%'}}></div>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Não-binário</span>
                      <span className="font-medium">2%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-purple-500 h-2 rounded-full" style={{width: '2%'}}></div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-3">Representatividade Étnica</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Branca</span>
                      <span className="font-medium">52%</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Parda</span>
                      <span className="font-medium">31%</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Preta</span>
                      <span className="font-medium">14%</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Outras</span>
                      <span className="font-medium">3%</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-3">Inclusão PCD</h4>
                  <div className="text-center p-4 bg-gray-100 dark:bg-gray-800 rounded-md">
                    <div className="text-2xl font-bold text-gray-900 dark:text-gray-50">8.2%</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Pessoas com Deficiência</div>
                    <div className="text-xs text-gray-600 mt-2">
                      Acima da cota legal de 5%
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Analytics de Modelos de Trabalho Tab */}
      {activeTab === 'work_models' && (
        <div className="space-y-6">
          {/* Gráficos Interativos de Modelos de Trabalho */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <WorkModelDistributionChart />
            <SourceEffectivenessChart />
          </div>

          {/* KPIs de Modelos de Trabalho */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="border-gray-300 dark:border-gray-600">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">Remoto</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-50">42%</p>
                  </div>
                  <Home className="w-8 h-8 text-gray-600 dark:text-gray-400" />
                </div>
                <div className="mt-2 flex items-center gap-1 text-xs">
                  <TrendingUp className="w-3 h-3 text-green-600" />
                  <span className="text-green-600">+8% vs trimestre anterior</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-purple-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-purple-600 font-medium">Híbrido</p>
                    <p className="text-2xl font-bold text-purple-700">35%</p>
                  </div>
                  <Mountain className="w-8 h-8 text-purple-600" />
                </div>
                <div className="mt-2 flex items-center gap-1 text-xs">
                  <TrendingUp className="w-3 h-3 text-green-600" />
                  <span className="text-green-600">+3% vs trimestre anterior</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-orange-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-orange-600 font-medium">Presencial</p>
                    <p className="text-2xl font-bold text-orange-700">23%</p>
                  </div>
                  <Building className="w-8 h-8 text-orange-600" />
                </div>
                <div className="mt-2 flex items-center gap-1 text-xs">
                  <TrendingDown className="w-3 h-3 text-red-600" />
                  <span className="text-red-600">-11% vs trimestre anterior</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-green-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-green-600 font-medium">Satisfação Média</p>
                    <p className="text-2xl font-bold text-green-700">8.4/10</p>
                  </div>
                  <Star className="w-8 h-8 text-green-600" />
                </div>
                <div className="mt-2 flex items-center gap-1 text-xs">
                  <TrendingUp className="w-3 h-3 text-green-600" />
                  <span className="text-green-600">+0.3 vs mês anterior</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Análise por Departamento */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  Modelos por Departamento
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { dept: 'Tecnologia', remote: 65, hybrid: 25, office: 10 },
                    { dept: 'Design', remote: 70, hybrid: 20, office: 10 },
                    { dept: 'Marketing', remote: 45, hybrid: 40, office: 15 },
                    { dept: 'Vendas', remote: 20, hybrid: 50, office: 30 },
                    { dept: 'Operações', remote: 15, hybrid: 35, office: 50 }
                  ].map((item, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-gray-950 dark:text-gray-50">{item.dept}</span>
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-gray-600 dark:text-gray-400">{item.remote}% Remoto</span>
                          <span className="text-purple-600">{item.hybrid}% Híbrido</span>
                          <span className="text-orange-600">{item.office}% Presencial</span>
                        </div>
                      </div>
                      <div className="flex w-full h-3 rounded-full overflow-hidden">
                        <div className="bg-gray-700 dark:bg-gray-300" style={{width: `${item.remote}%`}}></div>
                        <div className="bg-purple-500" style={{width: `${item.hybrid}%`}}></div>
                        <div className="bg-orange-500" style={{width: `${item.office}%`}}></div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-green-600" />
                  Distribuição Regional
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { region: 'São Paulo', count: 234, percentage: 42 },
                    { region: 'Rio de Janeiro', count: 156, percentage: 28 },
                    { region: 'Minas Gerais', count: 89, percentage: 16 },
                    { region: 'Outros Estados', count: 78, percentage: 14 }
                  ].map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <span className="text-sm font-medium">{item.region}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold">{item.count}</div>
                        <div className="text-xs text-gray-800 dark:text-gray-200">{item.percentage}%</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Insights e Recomendações */}
          <Card className="border-l-4 border-l-gray-400 dark:border-l-gray-500">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-yellow-600" />
                Insights e Recomendações Estratégicas
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-md">
                  <h4 className="font-medium text-wedo-cyan-dark mb-2">🚀 Tendência Crescente</h4>
                  <p className="text-sm text-wedo-cyan-dark">
                    Modelo remoto cresceu 8% no trimestre, especialmente em Tech e Design.
                    Considere expandir políticas de trabalho remoto.
                  </p>
                </div>
                <div className="p-4 bg-green-50 rounded-md">
                  <h4 className="font-medium text-green-900 mb-2">💡 Oportunidade</h4>
                  <p className="text-sm text-green-800">
                    Híbrido tem alta satisfação (8.7/10) e pode ser expandido para
                    departamentos tradicionalmente presenciais.
                  </p>
                </div>
                <div className="p-4 bg-yellow-50 rounded-md">
                  <h4 className="font-medium text-yellow-900 mb-2">⚠️ Atenção</h4>
                  <p className="text-sm text-yellow-800">
                    Presencial em declínio (-11%). Avaliar necessidade real vs
                    preferência dos colaboradores em Vendas e Operações.
                  </p>
                </div>
                <div className="p-4 bg-purple-50 rounded-md">
                  <h4 className="font-medium text-purple-900 mb-2">📊 Benchmark</h4>
                  <p className="text-sm text-purple-800">
                    Empresa está 15% acima da média do mercado em satisfação
                    com modelos flexíveis de trabalho.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Previsões e Tendências Tab */}
      {activeTab === 'predictions' && (
        <div className="space-y-6">
          {/* Sistema de Machine Learning */}
          <RecruitmentMLDashboard
            candidates={recruiters}
          />

          {/* KPIs Preditivos */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="border-green-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-green-600 font-medium">Previsão Q4</p>
                    <p className="text-2xl font-bold text-green-700">156</p>
                    <p className="text-xs text-gray-800 dark:text-gray-200">Contratações</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-green-600" />
                </div>
                <div className="mt-2 text-xs text-green-600">
                  +12% vs Q3 (IA: 89% confiança)
                </div>
              </CardContent>
            </Card>

            <Card className="border-gray-300 dark:border-gray-600">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">Time to Fill</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-50">24 dias</p>
                    <p className="text-xs text-gray-800 dark:text-gray-200">Previsão média</p>
                  </div>
                  <Clock className="w-8 h-8 text-gray-600 dark:text-gray-400" />
                </div>
                <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                  -8% vs atual (IA: 92% confiança)
                </div>
              </CardContent>
            </Card>

            <Card className="border-purple-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-purple-600 font-medium">Turnover Risk</p>
                    <p className="text-2xl font-bold text-purple-700">8.2%</p>
                    <p className="text-xs text-gray-800 dark:text-gray-200">Próximos 6 meses</p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-purple-600" />
                </div>
                <div className="mt-2 text-xs text-purple-600">
                  87 funcionários em risco
                </div>
              </CardContent>
            </Card>

            <Card className="border-orange-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-orange-600 font-medium">Budget Impact</p>
                    <p className="text-2xl font-bold text-orange-700">R$ 2.8M</p>
                    <p className="text-xs text-gray-800 dark:text-gray-200">Economia prevista</p>
                  </div>
                  <DollarSign className="w-8 h-8 text-orange-600" />
                </div>
                <div className="mt-2 text-xs text-orange-600">
                  Otimizações em TA
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Análise Preditiva de Demanda */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-600" />
                  Previsão de Demanda por Área
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { area: 'Tecnologia', current: 45, predicted: 62, confidence: 94 },
                    { area: 'Vendas', current: 23, predicted: 31, confidence: 87 },
                    { area: 'Marketing', current: 18, predicted: 22, confidence: 91 },
                    { area: 'Design', current: 12, predicted: 16, confidence: 89 },
                    { area: 'Operações', current: 15, predicted: 18, confidence: 85 }
                  ].map((item, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-gray-950 dark:text-gray-50">{item.area}</span>
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-gray-600">{item.current} → {item.predicted}</span>
                          <Badge className="bg-purple-100 text-purple-700 text-xs">
                            {item.confidence}% confiança
                          </Badge>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-gray-500 h-2 rounded-full"
                            style={{width: `${(item.current / 70) * 100}%`}}
                          ></div>
                        </div>
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-purple-500 h-2 rounded-full"
                            style={{width: `${(item.predicted / 70) * 100}%`}}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-green-600" />
                  Skills em Alta Demanda
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { skill: 'Inteligência Artificial', growth: '+127%', urgency: 'alta' },
                    { skill: 'React/Next.js', growth: '+89%', urgency: 'alta' },
                    { skill: 'DevOps/K8s', growth: '+76%', urgency: 'média' },
                    { skill: 'Product Management', growth: '+65%', urgency: 'média' },
                    { skill: 'Data Science', growth: '+54%', urgency: 'média' },
                    { skill: 'UX Research', growth: '+43%', urgency: 'baixa' }
                  ].map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                      <div>
                        <div className="font-medium text-gray-950 dark:text-gray-50">{item.skill}</div>
                        <div className="text-sm text-green-600">{item.growth} crescimento</div>
                      </div>
                      <Badge className={
                        item.urgency === 'alta' ? 'bg-red-100 text-red-700' :
                        item.urgency === 'média' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                      }>
                        {item.urgency === 'alta' ? '🔴 Alta' :
                         item.urgency === 'média' ? '🟡 Média' : '🟢 Baixa'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Alertas e Recomendações de IA */}
          <Card className="border-l-4 border-l-red-500">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-red-600" />
                Alertas Inteligentes e Ações Recomendadas
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    type: 'urgente',
                    title: 'Escassez crítica em IA/ML',
                    description: 'Demanda crescerá 127% nos próximos 3 meses, mas pipeline tem apenas 12 candidatos.',
                    action: 'Iniciar campanha agressiva de sourcing e aumentar budget em 40%',
                    confidence: 94
                  },
                  {
                    type: 'atencao',
                    title: 'Risco de turnover em Tech',
                    description: '23 desenvolvedores sêniores com padrão de saída detectado.',
                    action: 'Implementar programa de retenção e revisar pacotes salariais',
                    confidence: 87
                  },
                  {
                    type: 'oportunidade',
                    title: 'Otimização de processo',
                    description: 'IA detectou 8 etapas desnecessárias no funil que aumentam time to fill em 12 dias.',
                    action: 'Simplificar processo e automatizar triagem inicial',
                    confidence: 91
                  }
                ].map((alert, index) => (
                  <div key={index} className={`p-4 rounded-md border-l-4 ${
                    alert.type === 'urgente' ? 'bg-red-50 border-l-red-500' :
                    alert.type === 'atencao' ? 'bg-yellow-50 border-l-yellow-500' :
                    'bg-green-50 border-l-green-500'
                  }`}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className={`font-medium mb-1 ${
                          alert.type === 'urgente' ? 'text-red-900' :
                          alert.type === 'atencao' ? 'text-yellow-900' :
                          'text-green-900'
                        }`}>
                          {alert.type === 'urgente' ? '🚨' :
                           alert.type === 'atencao' ? '⚠️' : '💡'} {alert.title}
                        </h4>
                        <p className={`text-sm mb-2 ${
                          alert.type === 'urgente' ? 'text-red-800' :
                          alert.type === 'atencao' ? 'text-yellow-800' :
                          'text-green-800'
                        }`}>
                          {alert.description}
                        </p>
                        <p className={`text-sm font-medium ${
                          alert.type === 'urgente' ? 'text-red-900' :
                          alert.type === 'atencao' ? 'text-yellow-900' :
                          'text-green-900'
                        }`}>
                          💡 Ação recomendada: {alert.action}
                        </p>
                      </div>
                      <Badge className="ml-4 bg-gray-100 text-gray-800 dark:text-gray-200">
                        {alert.confidence}% confiança
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Centro de Controle IA Tab */}
      {activeTab === 'agent_control' && (
        <AgentControlCenter className="mt-0 -mx-6 -mb-6" />
      )}

      {/* Modal de Exportação Avançada */}
      <AdvancedReportExporter
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        data={{
          recruiters: filteredRecruiters,
          teamMetrics,
          selectedPeriod,
          selectedDepartments,
          alertStats: {}
        }}
        userRole="hr"
      />
    </div>
  )
}
