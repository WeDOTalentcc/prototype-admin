"use client"

import { useState, useMemo, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  BarChart3, PieChart, TrendingUp, Users, Brain, Target,
  Award, AlertTriangle, CheckCircle, Download, RefreshCw,
  Building, Calendar, Filter, Eye, Zap, Activity, Star,
  ChevronDown, ArrowUpRight, ArrowDownRight, Minus,
  UserCheck, UserX, Clock, DollarSign, Percent
} from "lucide-react"
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Pie, Bar, Line, Radar } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
)

// Dados mock para o dashboard
const mockCompanyData = {
  totalEmployees: 247,
  totalCandidates: 1834,
  hiredLastMonth: 23,
  turnoverRate: 12.5,
  averageTimeToHire: 18,
  bigFiveDistribution: {
    openness: { avg: 68, high: 89, medium: 127, low: 31 },
    conscientiousness: { avg: 74, high: 112, medium: 98, low: 37 },
    extraversion: { avg: 61, high: 76, medium: 134, low: 37 },
    agreeableness: { avg: 72, high: 101, medium: 109, low: 37 },
    neuroticism: { avg: 45, high: 45, medium: 156, low: 46 }
  }
}

const departmentData = [
  { dept: "Tecnologia", openness: 78, conscientiousness: 81, extraversion: 58, agreeableness: 67, neuroticism: 38, employees: 67 },
  { dept: "Vendas", openness: 61, conscientiousness: 69, extraversion: 84, agreeableness: 79, neuroticism: 42, employees: 45 },
  { dept: "Marketing", openness: 82, conscientiousness: 71, extraversion: 78, agreeableness: 74, neuroticism: 41, employees: 28 },
  { dept: "RH", openness: 73, conscientiousness: 86, extraversion: 72, agreeableness: 89, neuroticism: 31, employees: 15 },
  { dept: "Financeiro", openness: 58, conscientiousness: 92, extraversion: 54, agreeableness: 68, neuroticism: 35, employees: 22 },
  { dept: "Operações", openness: 64, conscientiousness: 88, extraversion: 61, agreeableness: 71, neuroticism: 39, employees: 38 },
  { dept: "Produto", openness: 85, conscientiousness: 76, extraversion: 65, agreeableness: 72, neuroticism: 44, employees: 32 }
]

const performanceCorrelation = [
  { trait: "Abertura", performance: 8.2, correlation: 0.67, significance: "Alta" },
  { trait: "Conscienciosidade", performance: 8.8, correlation: 0.84, significance: "Muito Alta" },
  { trait: "Extroversão", performance: 7.9, correlation: 0.51, significance: "Moderada" },
  { trait: "Amabilidade", performance: 8.1, correlation: 0.63, significance: "Alta" },
  { trait: "Estabilidade", performance: 8.5, correlation: 0.71, significance: "Alta" }
]

const hiringOutcomes = [
  { month: "Jan", contratados: 12, performance: 8.1, fit: 78, turnover: 8 },
  { month: "Fev", contratados: 15, performance: 8.4, fit: 82, turnover: 6 },
  { month: "Mar", contratados: 18, performance: 8.6, fit: 85, turnover: 5 },
  { month: "Abr", contratados: 21, performance: 8.8, fit: 87, turnover: 4 },
  { month: "Mai", contratados: 19, performance: 8.9, fit: 89, turnover: 3 },
  { month: "Jun", contratados: 23, performance: 9.1, fit: 91, turnover: 2 }
]

const successPrediction = [
  { range: "0-3 meses", tradicional: 72, bigFive: 89, diferenca: 17 },
  { range: "3-6 meses", tradicional: 68, bigFive: 85, diferenca: 17 },
  { range: "6-12 meses", tradicional: 64, bigFive: 82, diferenca: 18 },
  { range: "12+ meses", tradicional: 59, bigFive: 78, diferenca: 19 }
]

const COLORS = ['rgb(3 7 18 / 0.8)', 'var(--wedo-green-pastel)', 'var(--status-warning)', 'rgb(3 7 18 / 0.4)', 'var(--status-error)']

export function BigFiveDashboardPage() {
  const [selectedDepartment, setSelectedDepartment] = useState<string>("Todos")
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>("6 meses")
  const [selectedMetric, setSelectedMetric] = useState<string>("performance")

  // Calcular KPIs principais
  const kpis = useMemo(() => {
    const totalHired = hiringOutcomes.reduce((sum, month) => sum + month.contratados, 0)
    const avgPerformance = hiringOutcomes.reduce((sum, month) => sum + month.performance, 0) / hiringOutcomes.length
    const avgFit = hiringOutcomes.reduce((sum, month) => sum + month.fit, 0) / hiringOutcomes.length
    const avgTurnover = hiringOutcomes.reduce((sum, month) => sum + month.turnover, 0) / hiringOutcomes.length

    return {
      totalHired,
      avgPerformance: avgPerformance.toFixed(1),
      avgFit: Math.round(avgFit),
      avgTurnover: avgTurnover.toFixed(1),
      roiImprovement: 24,
      accuracyGain: 18
    }
  }, [])

  // Dados para gráfico de pizza - Distribuição Big Five
  const pieChartData = {
    labels: ['Abertura', 'Conscienciosidade', 'Extroversão', 'Amabilidade', 'Estabilidade'],
    datasets: [{
      data: [
        mockCompanyData.bigFiveDistribution.openness.avg,
        mockCompanyData.bigFiveDistribution.conscientiousness.avg,
        mockCompanyData.bigFiveDistribution.extraversion.avg,
        mockCompanyData.bigFiveDistribution.agreeableness.avg,
        100 - mockCompanyData.bigFiveDistribution.neuroticism.avg
      ],
      backgroundColor: COLORS,
      borderWidth: 2,
      borderColor: 'var(--white)'
    }]
  }

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          padding: 15,
          font: { size: 11 }
        }
      },
      tooltip: {
        callbacks: {
          label: (context: Record<string, unknown>) => {
            const label = context.label || ''
            const value = context.parsed || 0
            return `${label}: ${value}%`
          }
        }
      }
    }
  }

  // Dados para gráfico de barras - Correlação Performance
  const correlationChartData = {
    labels: performanceCorrelation.map(d => d.trait),
    datasets: [
      {
        label: 'Performance (1-10)',
        data: performanceCorrelation.map(d => d.performance),
        backgroundColor: 'var(--wedo-green-pastel)',
        borderColor: 'var(--wedo-green-pastel)',
        borderWidth: 1
      },
      {
        label: 'Correlação (0-1)',
        data: performanceCorrelation.map(d => d.correlation),
        backgroundColor: 'var(--gray-400)',
        borderColor: 'var(--gray-400)',
        borderWidth: 1
      }
    ]
  }

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          padding: 10,
          font: { size: 11 }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'var(--overlay-05)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  }

  // Dados para gráfico de linha - Evolução Temporal
  const evolutionChartData = {
    labels: hiringOutcomes.map(d => d.month),
    datasets: [
      {
        label: 'Performance',
        data: hiringOutcomes.map(d => d.performance),
        borderColor: 'var(--wedo-green-pastel)',
        backgroundColor: 'var(--wedo-green-bg-10)',
        borderWidth: 3,
        tension: 0.4,
        fill: true
      },
      {
        label: 'Fit Cultural %',
        data: hiringOutcomes.map(d => d.fit),
        borderColor: 'var(--gray-400)',
        backgroundColor: 'var(--wedo-blue-bg-10)',
        borderWidth: 3,
        tension: 0.4,
        fill: true
      },
      {
        label: 'Turnover %',
        data: hiringOutcomes.map(d => d.turnover),
        borderColor: 'var(--status-error)',
        backgroundColor: 'var(--status-error-bg)',
        borderWidth: 3,
        tension: 0.4,
        fill: true
      }
    ]
  }

  const lineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          padding: 10,
          font: { size: 11 }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'var(--overlay-05)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  }

  // Dados para gráfico de barras - Predição
  const predictionChartData = {
    labels: successPrediction.map(d => d.range),
    datasets: [
      {
        label: 'Métodos Tradicionais',
        data: successPrediction.map(d => d.tradicional),
        backgroundColor: 'var(--gray-200)',
        borderColor: 'var(--gray-200)',
        borderWidth: 1
      },
      {
        label: 'Big Five + IA',
        data: successPrediction.map(d => d.bigFive),
        backgroundColor: 'var(--gray-400)',
        borderColor: 'var(--gray-400)',
        borderWidth: 1
      }
    ]
  }

  // Dados para gráfico de radar - Departamentos
  const radarChartData = {
    labels: departmentData.map(d => d.dept),
    datasets: [
      {
        label: 'Abertura',
        data: departmentData.map(d => d.openness),
        borderColor: 'var(--gray-400)',
        backgroundColor: 'var(--wedo-blue-bg-20)',
        borderWidth: 2
      },
      {
        label: 'Conscienciosidade',
        data: departmentData.map(d => d.conscientiousness),
        borderColor: 'var(--wedo-green-pastel)',
        backgroundColor: 'var(--wedo-green-bg-20)',
        borderWidth: 2
      },
      {
        label: 'Extroversão',
        data: departmentData.map(d => d.extraversion),
        borderColor: 'var(--status-warning)',
        backgroundColor: 'var(--status-warning-border-light)',
        borderWidth: 2
      },
      {
        label: 'Amabilidade',
        data: departmentData.map(d => d.agreeableness),
        borderColor: 'var(--wedo-cyan-light)',
        backgroundColor: 'var(--wedo-cyan-bg-15)',
        borderWidth: 2
      },
      {
        label: 'Estabilidade',
        data: departmentData.map(d => d.neuroticism),
        borderColor: 'var(--status-error)',
        backgroundColor: 'var(--status-error-bg-20)',
        borderWidth: 2
      }
    ]
  }

  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          padding: 10,
          font: { size: 11 }
        }
      }
    },
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        ticks: {
          stepSize: 20
        },
        grid: {
          color: 'var(--overlay-10)'
        }
      }
    }
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-lia-text-primary flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-lia-text-disabled" />
            Dashboard Analytics Big Five
          </h1>
          <p className="text-lia-text-secondary mt-1">
            Análise científica de personalidades e predição de sucesso organizacional
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="gap-2">
            <Download className="w-4 h-4" />
            Exportar Relatório
          </Button>
          <Button variant="outline" className="gap-2">
            <RefreshCw className="w-4 h-4" />
            Atualizar Dados
          </Button>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-lia-text-primary" />
          <span className="text-sm font-medium text-lia-text-primary">Filtros:</span>
        </div>
        <select
          value={selectedDepartment}
          onChange={(e) => setSelectedDepartment(e.target.value)}
          className="px-3 py-1 rounded-md border border-lia-border-default dark:border-lia-border-default bg-white dark:bg-lia-bg-elevated text-sm"
        >
          <option value="Todos">Todos os Departamentos</option>
          {departmentData.map(dept => (
            <option key={dept.dept} value={dept.dept}>{dept.dept}</option>
          ))}
        </select>
        <select
          value={selectedTimeRange}
          onChange={(e) => setSelectedTimeRange(e.target.value)}
          className="px-3 py-1 rounded-md border border-lia-border-default dark:border-lia-border-default bg-white dark:bg-lia-bg-elevated text-sm"
        >
          <option value="3 meses">Últimos 3 meses</option>
          <option value="6 meses">Últimos 6 meses</option>
          <option value="12 meses">Último ano</option>
        </select>
      </div>

      {/* KPIs Principais */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        <Card style={{borderColor: 'var(--gray-400)'}} className="dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-lia-text-secondary">Contratações</p>
                <p className="text-2xl font-bold text-lia-text-primary">{kpis.totalHired}</p>
                <p className="text-xs text-status-success flex items-center gap-1">
                  <ArrowUpRight className="w-3 h-3" />
                  +15% vs anterior
                </p>
              </div>
              <UserCheck className="w-8 h-8 text-lia-text-disabled" />
            </div>
          </CardContent>
        </Card>

        <Card style={{borderColor: 'var(--wedo-green-pastel)'}} className="dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-lia-text-secondary">Performance Média</p>
                <p className="text-2xl font-bold text-lia-text-primary">{kpis.avgPerformance}</p>
                <p className="text-xs text-status-success flex items-center gap-1">
                  <ArrowUpRight className="w-3 h-3" />
                  +0.8 vs tradicional
                </p>
              </div>
              <Star className="w-8 h-8 text-wedo-green-pastel" />
            </div>
          </CardContent>
        </Card>

        <Card style={{borderColor: 'var(--status-warning)'}} className="dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-lia-text-secondary">Fit Cultural</p>
                <p className="text-2xl font-bold text-lia-text-primary">{kpis.avgFit}%</p>
                <p className="text-xs text-status-success flex items-center gap-1">
                  <ArrowUpRight className="w-3 h-3" />
                  +{kpis.accuracyGain}% precisão
                </p>
              </div>
              <Target className="w-8 h-8 text-status-warning" />
            </div>
          </CardContent>
        </Card>

        <Card style={{borderColor: 'var(--gray-300)'}} className="dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-lia-text-secondary">Turnover</p>
                <p className="text-2xl font-bold text-lia-text-primary">{kpis.avgTurnover}%</p>
                <p className="text-xs text-status-success flex items-center gap-1">
                  <ArrowDownRight className="w-3 h-3" />
                  -67% vs tradicional
                </p>
              </div>
              <UserX className="w-8 h-8 text-lia-text-disabled" />
            </div>
          </CardContent>
        </Card>

        <Card style={{borderColor: 'var(--status-error)'}} className="dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-lia-text-secondary">ROI Melhoria</p>
                <p className="text-2xl font-bold text-lia-text-primary">{kpis.roiImprovement}%</p>
                <p className="text-xs text-status-success flex items-center gap-1">
                  <DollarSign className="w-3 h-3" />
                  vs métodos tradicionais
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-status-error" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-lia-border-default dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-lia-text-secondary">Tempo p/ Contratar</p>
                <p className="text-2xl font-bold text-lia-text-primary">{mockCompanyData.averageTimeToHire}d</p>
                <p className="text-xs text-status-success flex items-center gap-1">
                  <ArrowDownRight className="w-3 h-3" />
                  -23% vs anterior
                </p>
              </div>
              <Clock className="w-8 h-8 text-lia-text-primary" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Gráficos Principais */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribuição Big Five da Empresa */}
        <Card className="dark:border-lia-border-default">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="w-5 h-5 text-lia-text-disabled" />
              Distribuição Big Five - Empresa
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{height: '300px'}}>
              <Pie data={pieChartData} options={pieOptions as any} />
            </div>
          </CardContent>
        </Card>

        {/* Performance vs Big Five */}
        <Card className="dark:border-lia-border-default">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-wedo-green-pastel" />
              Correlação Performance x Big Five
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{height: '300px'}}>
              <Bar data={correlationChartData} options={barOptions} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Análises Avançadas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Evolução Temporal */}
        <Card className="dark:border-lia-border-default">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-status-warning" />
              Evolução de Resultados (6 meses)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{height: '300px'}}>
              <Line data={evolutionChartData} options={lineOptions} />
            </div>
          </CardContent>
        </Card>

        {/* Predição vs Métodos Tradicionais */}
        <Card className="dark:border-lia-border-default">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-lia-text-disabled" />
              Precisão: Big Five vs Métodos Tradicionais
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{height: '300px'}}>
              <Bar data={predictionChartData} options={barOptions} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Análise por Departamento */}
      <Card className="dark:border-lia-border-default">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="w-5 h-5 text-status-error" />
            Perfil Big Five por Departamento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div style={{height: '400px'}}>
            <Radar data={radarChartData} options={radarOptions} />
          </div>
        </CardContent>
      </Card>

      {/* Insights Executivos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card style={{borderColor: 'var(--gray-400)'}} className="dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 mt-1 text-wedo-green-pastel" />
              <div>
                <h4 className="font-semibold text-lia-text-primary mb-1">
                  💡 Insight Principal
                </h4>
                <p className="text-sm text-lia-text-secondary">
                  Candidatos com alta Conscienciosidade têm <strong>84% mais probabilidade</strong> de sucesso nos primeiros 6 meses.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card style={{borderColor: 'var(--status-warning)'}} className="dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <TrendingUp className="w-5 h-5 mt-1 text-wedo-green-pastel" />
              <div>
                <h4 className="font-semibold text-lia-text-primary mb-1">
                  📈 Tendência Detectada
                </h4>
                <p className="text-sm text-lia-text-secondary">
                  Departamento de <strong>Tecnologia</strong> precisa de candidatos com maior Abertura para inovação.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card style={{borderColor: 'var(--status-error)'}} className="dark:border-lia-border-default">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 mt-1 text-status-warning" />
              <div>
                <h4 className="font-semibold text-lia-text-primary mb-1">
                  ⚠️ Recomendação
                </h4>
                <p className="text-sm text-lia-text-secondary">
                  Implementar filtros Big Five nas vagas de <strong>Vendas</strong> pode reduzir turnover em 45%.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
