"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Brain, TrendingUp, TrendingDown, AlertTriangle, CheckCircle,
  Target, Users, BarChart3, PieChart, Zap, Star, Award,
  Eye, Settings, Download, RefreshCw, Filter, Search,
  Calendar, Clock, DollarSign, MapPin, Briefcase, User,
  Lightbulb, ArrowRight, ArrowUp, ArrowDown, Minus
} from "lucide-react"

interface PredictionModel {
  id: string
  name: string
  type: 'success_prediction' | 'retention_risk' | 'performance_forecast' | 'cultural_fit'
  accuracy: number
  lastTrained: string
  status: 'active' | 'training' | 'outdated'
  samplesUsed: number
  features: string[]
}

interface CandidatePrediction {
  candidateId: string
  name: string
  position: string
  department: string
  predictions: {
    successScore: number
    retentionRisk: 'low' | 'medium' | 'high'
    performanceLevel: 'below_average' | 'average' | 'above_average' | 'exceptional'
    culturalFit: number
    timeToProductivity: number // dias
    salaryRecommendation: {
      min: number
      max: number
      optimal: number
    }
  }
  confidenceLevel: number
  factors: {
    positive: string[]
    negative: string[]
    neutral: string[]
  }
  recommendations: string[]
  riskFactors: string[]
}

interface HistoricalAnalysis {
  totalHires: number
  period: string
  successRate: number
  averageRetention: number
  averagePerformance: number
  trends: {
    hiring: 'up' | 'down' | 'stable'
    quality: 'up' | 'down' | 'stable'
    retention: 'up' | 'down' | 'stable'
  }
  departmentMetrics: {
    department: string
    hires: number
    successRate: number
    avgTimeToProductivity: number
    topSkills: string[]
  }[]
}

// Mock data para modelos ML
const mlModels: PredictionModel[] = [
  {
    id: 'success-v3',
    name: 'Predição de Sucesso v3.0',
    type: 'success_prediction',
    accuracy: 87.3,
    lastTrained: '2024-01-15',
    status: 'active',
    samplesUsed: 2847,
    features: ['experiência', 'skills', 'formação', 'fit_cultural', 'entrevistas', 'testes_técnicos']
  },
  {
    id: 'retention-v2',
    name: 'Modelo de Retenção v2.1',
    type: 'retention_risk',
    accuracy: 82.1,
    lastTrained: '2024-01-10',
    status: 'active',
    samplesUsed: 1923,
    features: ['satisfação', 'salário', 'crescimento', 'manager_feedback', 'workload']
  },
  {
    id: 'performance-v1',
    name: 'Previsão de Performance v1.5',
    type: 'performance_forecast',
    accuracy: 79.8,
    lastTrained: '2024-01-05',
    status: 'training',
    samplesUsed: 1654,
    features: ['habilidades_técnicas', 'soft_skills', 'experiência_anterior', 'projetos']
  },
  {
    id: 'culture-v2',
    name: 'Análise de Fit Cultural v2.0',
    type: 'cultural_fit',
    accuracy: 91.2,
    lastTrained: '2024-01-12',
    status: 'active',
    samplesUsed: 3241,
    features: ['valores', 'comportamento', 'comunicação', 'colaboração', 'adaptabilidade']
  }
]

const candidatePredictions: CandidatePrediction[] = [
  {
    candidateId: '1',
    name: 'Carlos Santos',
    position: 'Frontend Developer Sênior',
    department: 'Tecnologia',
    predictions: {
      successScore: 92,
      retentionRisk: 'low',
      performanceLevel: 'above_average',
      culturalFit: 88,
      timeToProductivity: 21,
      salaryRecommendation: {
        min: 12000,
        max: 15000,
        optimal: 13500
      }
    },
    confidenceLevel: 89,
    factors: {
      positive: ['Experiência sólida em React', 'Histórico de liderança', 'Skills alinhadas', 'Boa comunicação'],
      negative: ['Expectativa salarial alta', 'Mudança de stack tecnológica'],
      neutral: ['Localização', 'Disponibilidade']
    },
    recommendations: [
      'Oferecer mentoria em tecnologias específicas da empresa',
      'Incluir em projetos de alta visibilidade',
      'Considerar plano de carreira acelerado'
    ],
    riskFactors: ['Possível counter-offer da empresa atual', 'Mercado aquecido para frontend']
  },
  {
    candidateId: '2',
    name: 'Maria Oliveira',
    position: 'UX Designer',
    department: 'Design',
    predictions: {
      successScore: 85,
      retentionRisk: 'medium',
      performanceLevel: 'above_average',
      culturalFit: 94,
      timeToProductivity: 18,
      salaryRecommendation: {
        min: 8000,
        max: 11000,
        optimal: 9500
      }
    },
    confidenceLevel: 82,
    factors: {
      positive: ['Excelente fit cultural', 'Portfolio diversificado', 'Experiência em startups', 'Design thinking'],
      negative: ['Pouca experiência em produtos enterprise', 'Mudança de setor'],
      neutral: ['Formação acadêmica', 'Inglês intermediário']
    },
    recommendations: [
      'Programa de ambientação específico para produtos enterprise',
      'Pareamento com designer sênior',
      'Curso de inglês corporativo'
    ],
    riskFactors: ['Adaptação ao ambiente corporativo', 'Mudança de metodologias']
  },
  {
    candidateId: '3',
    name: 'Ana Pereira',
    position: 'Data Scientist',
    department: 'Dados',
    predictions: {
      successScore: 78,
      retentionRisk: 'high',
      performanceLevel: 'exceptional',
      culturalFit: 76,
      timeToProductivity: 35,
      salaryRecommendation: {
        min: 14000,
        max: 18000,
        optimal: 16000
      }
    },
    confidenceLevel: 76,
    factors: {
      positive: ['PhD em Data Science', 'Experiência internacional', 'Papers publicados', 'Conhecimento avançado'],
      negative: ['Overqualified', 'Expectativas muito altas', 'Baixo fit cultural inicial'],
      neutral: ['Experiência em consultoria', 'Idiomas']
    },
    recommendations: [
      'Definir projetos desafiadores desde o início',
      'Maior autonomia e flexibilidade',
      'Conexão com universidades e comunidade acadêmica'
    ],
    riskFactors: ['Risk de turnover por overqualification', 'Competição por talentos sêniores']
  }
]

const historicalAnalysis: HistoricalAnalysis = {
  totalHires: 847,
  period: 'Últimos 24 meses',
  successRate: 84.2,
  averageRetention: 23.4,
  averagePerformance: 78.6,
  trends: {
    hiring: 'up',
    quality: 'up',
    retention: 'down'
  },
  departmentMetrics: [
    {
      department: 'Tecnologia',
      hires: 324,
      successRate: 87.8,
      avgTimeToProductivity: 28,
      topSkills: ['React', 'Node.js', 'Python', 'AWS', 'Docker']
    },
    {
      department: 'Design',
      hires: 156,
      successRate: 91.2,
      avgTimeToProductivity: 21,
      topSkills: ['Figma', 'Design System', 'User Research', 'Prototyping', 'UI/UX']
    },
    {
      department: 'Produto',
      hires: 89,
      successRate: 79.1,
      avgTimeToProductivity: 35,
      topSkills: ['Product Strategy', 'Analytics', 'Roadmapping', 'Agile', 'SQL']
    },
    {
      department: 'Dados',
      hires: 134,
      successRate: 82.1,
      avgTimeToProductivity: 42,
      topSkills: ['Python', 'SQL', 'Machine Learning', 'Statistics', 'Tableau']
    }
  ]
}

export function SuccessPredictionAnalytics() {
  const [selectedView, setSelectedView] = useState<'overview' | 'models' | 'predictions' | 'insights'>('overview')
  const [selectedCandidate, setSelectedCandidate] = useState<CandidatePrediction | null>(null)
  const [isTraining, setIsTraining] = useState(false)

  const handleRetrainModel = (modelId: string) => {
    setIsTraining(true)
    setTimeout(() => {
      setIsTraining(false)
      alert('Modelo retreinado com sucesso!')
    }, 3000)
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <ArrowUp className="w-4 h-4 text-status-success" />
      case 'down': return <ArrowDown className="w-4 h-4 text-status-error" />
      default: return <Minus className="w-4 h-4 text-gray-600" />
    }
  }

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'up': return 'text-status-success'
      case 'down': return 'text-status-error'
      default: return 'text-gray-600'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-status-success'
    if (score >= 70) return 'text-status-warning'
    return 'text-status-error'
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'bg-status-success/10 text-status-success border-status-success/30'
      case 'medium': return 'bg-status-warning/10 text-status-warning border-status-warning/30'
      case 'high': return 'bg-status-error/10 text-status-error border-status-error/30'
      default: return 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200'
    }
  }

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Taxa de Sucesso Prevista</p>
                <p className="text-2xl font-bold text-status-success">87.3%</p>
                <div className="flex items-center gap-1 mt-1">
                  {getTrendIcon(historicalAnalysis.trends.quality)}
                  <span className={`text-sm ${getTrendColor(historicalAnalysis.trends.quality)}`}>
                    +2.1% vs anterior
                  </span>
                </div>
              </div>
              <div className="w-12 h-12 bg-status-success/10 rounded-md flex items-center justify-center">
                <Target className="w-6 h-6 text-status-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Retenção Média</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-50">{historicalAnalysis.averageRetention} meses</p>
                <div className="flex items-center gap-1 mt-1">
                  {getTrendIcon(historicalAnalysis.trends.retention)}
                  <span className={`text-sm ${getTrendColor(historicalAnalysis.trends.retention)}`}>
                    -1.2 vs anterior
                  </span>
                </div>
              </div>
              <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-md flex items-center justify-center">
                <Users className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Performance Média</p>
                <p className="text-2xl font-bold text-wedo-purple">{historicalAnalysis.averagePerformance}%</p>
                <div className="flex items-center gap-1 mt-1">
                  {getTrendIcon('up')}
                  <span className="text-sm text-status-success">+3.4% vs anterior</span>
                </div>
              </div>
              <div className="w-12 h-12 bg-wedo-purple/10 rounded-md flex items-center justify-center">
                <Award className="w-6 h-6 text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Modelos Ativos</p>
                <p className="text-2xl font-bold text-wedo-orange">{mlModels.filter(m => m.status === 'active').length}</p>
                <p className="text-sm text-gray-800 dark:text-gray-200">de {mlModels.length} total</p>
              </div>
              <div className="w-12 h-12 bg-wedo-orange/10 rounded-md flex items-center justify-center">
                <Brain className="w-6 h-6 text-wedo-cyan" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Predictions Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Zap className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            Predições Recentes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {candidatePredictions.map(prediction => (
              <div key={prediction.candidateId} className="p-4 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gray-100 rounded-md flex items-center justify-center">
                      <User className="w-6 h-6 text-gray-800 dark:text-gray-200" />
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-950 dark:text-gray-50">{prediction.name}</h4>
                      <p className="text-sm text-gray-600">{prediction.position} • {prediction.department}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6 text-sm">
                    <div className="text-center">
                      <p className="font-medium text-gray-600">Score de Sucesso</p>
                      <p className={`text-xl font-bold ${getScoreColor(prediction.predictions.successScore)}`}>
                        {prediction.predictions.successScore}%
                      </p>
                    </div>

                    <div className="text-center">
                      <p className="font-medium text-gray-600">Risco de Retenção</p>
                      <Badge className={getRiskColor(prediction.predictions.retentionRisk)}>
                        {prediction.predictions.retentionRisk === 'low' ? 'Baixo' :
                         prediction.predictions.retentionRisk === 'medium' ? 'Médio' : 'Alto'}
                      </Badge>
                    </div>

                    <div className="text-center">
                      <p className="font-medium text-gray-600">Fit Cultural</p>
                      <p className={`text-xl font-bold ${getScoreColor(prediction.predictions.culturalFit)}`}>
                        {prediction.predictions.culturalFit}%
                      </p>
                    </div>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedCandidate(prediction)}
                      className="gap-2"
                    >
                      <Eye className="w-4 h-4" />
                      Ver Detalhes
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Department Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Performance por Departamento</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-950 dark:text-gray-50">Departamento</th>
                  <th className="text-center py-3 px-4 font-medium text-gray-950 dark:text-gray-50">Contratações</th>
                  <th className="text-center py-3 px-4 font-medium text-gray-950 dark:text-gray-50">Taxa de Sucesso</th>
                  <th className="text-center py-3 px-4 font-medium text-gray-950 dark:text-gray-50">Tempo para Produtividade</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-950 dark:text-gray-50">Top Skills</th>
                </tr>
              </thead>
              <tbody>
                {historicalAnalysis.departmentMetrics.map((dept, index) => (
                  <tr key={index} className="border-b border-gray-100">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <Briefcase className="w-4 h-4 text-gray-600" />
                        <span className="font-medium">{dept.department}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">{dept.hires}</td>
                    <td className="py-3 px-4 text-center">
                      <span className={`font-medium ${getScoreColor(dept.successRate)}`}>
                        {dept.successRate}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">{dept.avgTimeToProductivity} dias</td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {dept.topSkills.slice(0, 3).map((skill, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                        {dept.topSkills.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{dept.topSkills.length - 3}
                          </Badge>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderModels = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-950 dark:text-gray-50">Modelos de Machine Learning</h3>
          <p className="text-sm text-gray-600">Gerencie e monitore os modelos de predição</p>
        </div>
        <Button className="gap-2" disabled={isTraining}>
          <RefreshCw className={`w-4 h-4 ${isTraining ? 'animate-spin' : ''}`} />
          {isTraining ? 'Treinando...' : 'Retreinar Todos'}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {mlModels.map(model => (
          <Card key={model.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">{model.name}</CardTitle>
                  <p className="text-sm text-gray-600 mt-1">
                    {model.type === 'success_prediction' ? 'Predição de Sucesso' :
                     model.type === 'retention_risk' ? 'Risco de Retenção' :
                     model.type === 'performance_forecast' ? 'Previsão de Performance' : 'Fit Cultural'}
                  </p>
                </div>
                <Badge variant={model.status === 'active' ? 'default' : model.status === 'training' ? 'secondary' : 'outline'}>
                  {model.status === 'active' ? 'Ativo' : model.status === 'training' ? 'Treinando' : 'Desatualizado'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Acurácia</p>
                    <p className={`text-2xl font-bold ${getScoreColor(model.accuracy)}`}>
                      {model.accuracy}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Amostras</p>
                    <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                      {model.samplesUsed.toLocaleString()}
                    </p>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-600 mb-2">Último Treinamento</p>
                  <p className="text-sm text-gray-950 dark:text-gray-50">
                    {new Date(model.lastTrained).toLocaleDateString('pt-BR')}
                  </p>
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-600 mb-2">Features Utilizadas</p>
                  <div className="flex flex-wrap gap-1">
                    {model.features.map((feature, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 gap-2"
                    onClick={() => handleRetrainModel(model.id)}
                    disabled={isTraining || model.status === 'training'}
                  >
                    <RefreshCw className="w-4 h-4" />
                    Retreinar
                  </Button>
                  <Button size="sm" variant="outline" className="gap-2">
                    <Settings className="w-4 h-4" />
                    Configurar
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-semibold font-sans text-gray-950 dark:text-gray-50 mb-2 flex items-center gap-2">
                <Brain className="w-6 h-6 text-wedo-cyan" />
                Analytics com Machine Learning
              </h1>
              <p className="text-gray-600">
                Predição inteligente de sucesso e analytics avançado de contratações
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" className="gap-2">
                <Download className="w-4 h-4" />
                Exportar Insights
              </Button>
              <Button variant="outline" className="gap-2">
                <Settings className="w-4 h-4" />
                Configurações ML
              </Button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-md w-fit">
            {[
              { id: 'overview', label: 'Visão Geral', icon: BarChart3 },
              { id: 'models', label: 'Modelos ML', icon: Brain },
              { id: 'predictions', label: 'Predições', icon: Target },
              { id: 'insights', label: 'Insights', icon: Lightbulb }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setSelectedView(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  selectedView === tab.id
                    ? 'bg-white text-gray-950 dark:text-gray-50'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        {selectedView === 'overview' && renderOverview()}
        {selectedView === 'models' && renderModels()}
        {selectedView === 'predictions' && (
          <div className="text-center py-12">
            <Target className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium font-sans text-gray-950 dark:text-gray-50 mb-2">Predições Detalhadas</h3>
            <p className="text-gray-600">Interface de predições em desenvolvimento</p>
          </div>
        )}
        {selectedView === 'insights' && (
          <div className="text-center py-12">
            <Lightbulb className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium font-sans text-gray-950 dark:text-gray-50 mb-2">Insights Avançados</h3>
            <p className="text-gray-600">Painel de insights em desenvolvimento</p>
          </div>
        )}

        {/* Candidate Detail Modal */}
        {selectedCandidate && (
          <CandidatePredictionModal
            candidate={selectedCandidate}
            onClose={() => setSelectedCandidate(null)}
          />
        )}
      </div>
    </div>
  )
}

// Modal de detalhes de predição
interface CandidatePredictionModalProps {
  candidate: CandidatePrediction
  onClose: () => void
}

function CandidatePredictionModal({ candidate, onClose }: CandidatePredictionModalProps) {
  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-status-success'
    if (score >= 70) return 'text-status-warning'
    return 'text-status-error'
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'bg-status-success/10 text-status-success border-status-success/30'
      case 'medium': return 'bg-status-warning/10 text-status-warning border-status-warning/30'
      case 'high': return 'bg-status-error/10 text-status-error border-status-error/30'
      default: return 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200'
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-md w-full max-w-5xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-950 dark:text-gray-50 flex items-center gap-2">
              <Brain className="w-5 h-5 text-wedo-cyan" />
              Análise Preditiva - {candidate.name}
            </h2>
            <p className="text-gray-600">{candidate.position} • {candidate.department}</p>
          </div>
          <Button variant="ghost" onClick={onClose}>×</Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Predictions Summary */}
            <div className="lg:col-span-2 space-y-6">
              {/* Score Cards */}
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-sm font-medium text-gray-600 mb-2">Score de Sucesso</p>
                    <p className={`text-3xl font-bold ${getScoreColor(candidate.predictions.successScore)}`}>
                      {candidate.predictions.successScore}%
                    </p>
                    <p className="text-xs text-gray-800 dark:text-gray-200 mt-1">Confiança: {candidate.confidenceLevel}%</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-sm font-medium text-gray-600 mb-2">Fit Cultural</p>
                    <p className={`text-3xl font-bold ${getScoreColor(candidate.predictions.culturalFit)}`}>
                      {candidate.predictions.culturalFit}%
                    </p>
                    <Badge className={`mt-2 ${getRiskColor(candidate.predictions.retentionRisk)}`}>
                      Risco: {candidate.predictions.retentionRisk === 'low' ? 'Baixo' :
                             candidate.predictions.retentionRisk === 'medium' ? 'Médio' : 'Alto'}
                    </Badge>
                  </CardContent>
                </Card>
              </div>

              {/* Performance & Productivity */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Previsões de Performance</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Nível de Performance</p>
                      <p className="text-lg font-bold text-wedo-purple capitalize">
                        {candidate.predictions.performanceLevel.replace('_', ' ')}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Tempo para Produtividade</p>
                      <p className="text-lg font-bold text-gray-900 dark:text-gray-50">
                        {candidate.predictions.timeToProductivity} dias
                      </p>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-2">Recomendação Salarial</p>
                    <div className="bg-gray-50 p-3 rounded-md">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Faixa:</span>
                        <span className="font-medium">
                          R$ {candidate.predictions.salaryRecommendation.min.toLocaleString()} -
                          R$ {candidate.predictions.salaryRecommendation.max.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between items-center mt-1">
                        <span className="text-sm">Ofertas Ótima:</span>
                        <span className="font-bold text-status-success">
                          R$ {candidate.predictions.salaryRecommendation.optimal.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Factors Analysis */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Análise de Fatores</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-medium text-status-success mb-2 flex items-center gap-1">
                        <CheckCircle className="w-4 h-4" />
                        Fatores Positivos
                      </h4>
                      <div className="space-y-1">
                        {candidate.factors.positive.map((factor, index) => (
                          <div key={index} className="text-sm text-gray-800 dark:text-gray-200 bg-status-success/10 p-2 rounded-md">
                            • {factor}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-status-error mb-2 flex items-center gap-1">
                        <AlertTriangle className="w-4 h-4" />
                        Pontos de Atenção
                      </h4>
                      <div className="space-y-1">
                        {candidate.factors.negative.map((factor, index) => (
                          <div key={index} className="text-sm text-gray-800 dark:text-gray-200 bg-status-error/10 p-2 rounded-md">
                            • {factor}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recommendations & Risks */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-status-warning" />
                    Recomendações
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {candidate.recommendations.map((rec, index) => (
                      <div key={index} className="p-3 bg-gray-100 dark:bg-gray-800 rounded-md">
                        <p className="text-sm text-wedo-cyan-dark">{rec}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-wedo-orange" />
                    Fatores de Risco
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {candidate.riskFactors.map((risk, index) => (
                      <div key={index} className="p-3 bg-wedo-orange/10 rounded-md">
                        <p className="text-sm text-wedo-orange">{risk}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <div className="space-y-2">
                <Button className="w-full gap-2">
                  <Download className="w-4 h-4" />
                  Exportar Análise
                </Button>
                <Button variant="outline" className="w-full gap-2">
                  <Target className="w-4 h-4" />
                  Criar Plano de Ação
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
