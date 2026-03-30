"use client"

import { useMemo, useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Brain, TrendingUp, TrendingDown, Target, AlertTriangle,
  CheckCircle, Clock, Users, DollarSign, BarChart3, Zap,
  Activity, Star, Calculator, Eye, Settings, RefreshCw
} from "lucide-react"

// Tipos para o sistema de ML
interface HistoricalDataPoint {
  date: string
  applications: number
  interviews: number
  hires: number
  timeToFill: number
  cost: number
  nps: number
  department: string
  source: string
  seasonality: number
}

interface MLPrediction {
  metric: string
  currentValue: number
  predictedValue: number
  confidence: number
  trend: 'up' | 'down' | 'stable'
  factors: string[]
  recommendation: string
}

interface MLInsight {
  type: 'pattern' | 'anomaly' | 'correlation' | 'seasonal'
  title: string
  description: string
  impact: 'high' | 'medium' | 'low'
  actionable: boolean
  suggestion?: string
}

interface CandidateScore {
  candidateId: string
  name: string
  overallScore: number
  skillsMatch: number
  experienceScore: number
  culturalFit: number
  successProbability: number
  timeToOnboard: number
  retentionRisk: number
}

// Tipo mínimo para candidatos usados no scoring ML
interface MLCandidate {
  id?: string
  name?: string
  skills?: string[]
  experience?: string
  [key: string]: unknown
}

// Gerador de dados históricos realistas
const generateHistoricalData = (): HistoricalDataPoint[] => {
  const data: HistoricalDataPoint[] = []
  const departments = ['Tech', 'Sales', 'Design', 'Marketing', 'Product']
  const sources = ['LinkedIn', 'Referrals', 'Job Boards', 'Website', 'Headhunting']

  // Gerar 24 meses de dados
  for (let month = 0; month < 24; month++) {
    const date = new Date()
    date.setMonth(date.getMonth() - (24 - month))

    const seasonality = Math.sin((month % 12) * Math.PI / 6) * 0.3 + 1
    const trend = month * 0.02 + 1

    departments.forEach(department => {
      sources.forEach(source => {
        const baseApplications = department === 'Tech' ? 180 :
                                department === 'Sales' ? 120 : 90

        data.push({
          date: date.toISOString().split('T')[0],
          applications: Math.round(baseApplications * seasonality * trend * (0.8 + Math.random() * 0.4)),
          interviews: Math.round(baseApplications * 0.4 * seasonality * (0.8 + Math.random() * 0.4)),
          hires: Math.round(baseApplications * 0.08 * seasonality * (0.8 + Math.random() * 0.4)),
          timeToFill: Math.round(28 + Math.random() * 14 + (department === 'Tech' ? 5 : 0)),
          cost: Math.round(3200 + Math.random() * 1000 + (department === 'Tech' ? 800 : 0)),
          nps: Math.round(80 + Math.random() * 15),
          department,
          source,
          seasonality
        })
      })
    })
  }

  return data
}

// Algoritmos de ML simplificados
class RecruitmentMLEngine {
  private data: HistoricalDataPoint[]

  constructor(data: HistoricalDataPoint[]) {
    this.data = data
  }

  // Regressão linear simples
  private linearRegression(x: number[], y: number[]): { slope: number, intercept: number, r2: number } {
    const n = x.length
    const sumX = x.reduce((a, b) => a + b, 0)
    const sumY = y.reduce((a, b) => a + b, 0)
    const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0)
    const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0)

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX)
    const intercept = (sumY - slope * sumX) / n

    // Calcular R²
    const yMean = sumY / n
    const yPred = x.map(xi => slope * xi + intercept)
    const ssRes = y.reduce((sum, yi, i) => sum + Math.pow(yi - yPred[i], 2), 0)
    const ssTot = y.reduce((sum, yi) => sum + Math.pow(yi - yMean, 2), 0)
    const r2 = 1 - (ssRes / ssTot)

    return { slope, intercept, r2 }
  }

  // Detectar tendências
  private detectTrend(values: number[]): 'up' | 'down' | 'stable' {
    const firstHalf = values.slice(0, Math.floor(values.length / 2))
    const secondHalf = values.slice(Math.floor(values.length / 2))

    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length

    const change = (secondAvg - firstAvg) / firstAvg

    if (change > 0.05) return 'up'
    if (change < -0.05) return 'down'
    return 'stable'
  }

  // Análise de sazonalidade
  private analyzeSeasonality(metric: string): { peak: number, trough: number, amplitude: number } {
    const monthlyData: { [key: number]: number[] } = {}

    this.data.forEach(point => {
      const month = new Date(point.date).getMonth()
      if (!monthlyData[month]) monthlyData[month] = []
      monthlyData[month].push(point[metric as keyof HistoricalDataPoint] as number)
    })

    const monthlyAvgs = Object.keys(monthlyData).map(month => {
      const values = monthlyData[parseInt(month)]
      return values.reduce((a, b) => a + b, 0) / values.length
    })

    const peak = Math.max(...monthlyAvgs)
    const trough = Math.min(...monthlyAvgs)
    const amplitude = (peak - trough) / ((peak + trough) / 2)

    return { peak, trough, amplitude }
  }

  // Predições
  predictMetric(metric: string, daysAhead: number = 30): MLPrediction {
    const metricData = this.data
      .filter(d => d[metric as keyof HistoricalDataPoint] !== undefined)
      .map((d, index) => ({
        x: index,
        y: d[metric as keyof HistoricalDataPoint] as number
      }))

    const x = metricData.map(d => d.x)
    const y = metricData.map(d => d.y)

    const regression = this.linearRegression(x, y)
    const futureX = x.length + (daysAhead / 30) // Aproximação mensal
    const predictedValue = regression.slope * futureX + regression.intercept
    const currentValue = y[y.length - 1]

    const confidence = Math.min(Math.max(regression.r2 * 100, 60), 95)
    const trend = this.detectTrend(y.slice(-6)) // Últimos 6 pontos

    const factors = this.identifyFactors(metric)
    const recommendation = this.generateRecommendation(metric, trend, confidence)

    return {
      metric,
      currentValue,
      predictedValue: Math.round(predictedValue),
      confidence: Math.round(confidence),
      trend,
      factors,
      recommendation
    }
  }

  // Identificar fatores que influenciam a métrica
  private identifyFactors(metric: string): string[] {
    const factors: string[] = []

    switch (metric) {
      case 'applications':
        factors.push('Sazonalidade', 'Publicações no LinkedIn', 'Mercado de trabalho')
        break
      case 'hires':
        factors.push('Qualidade do pipeline', 'Processo de entrevistas', 'Competitividade salarial')
        break
      case 'timeToFill':
        factors.push('Complexidade da vaga', 'Número de etapas', 'Disponibilidade de candidatos')
        break
      case 'cost':
        factors.push('Fontes de recrutamento', 'Senioridade da vaga', 'Urgência da contratação')
        break
      default:
        factors.push('Tendências históricas', 'Fatores externos')
    }

    return factors
  }

  // Gerar recomendações
  private generateRecommendation(metric: string, trend: string, confidence: number): string {
    if (confidence < 70) {
      return "Dados insuficientes para recomendação precisa. Colete mais informações."
    }

    const baseRecommendations: { [key: string]: { [key: string]: string } } = {
      applications: {
        up: "Prepare-se para aumento de volume. Otimize processo de triagem.",
        down: "Intensifique sourcing ativo e revise estratégia de atração.",
        stable: "Mantenha estratégia atual e monitore tendências."
      },
      hires: {
        up: "Excelente! Documente boas práticas e replique em outras áreas.",
        down: "Analise gargalos no funil e melhore taxa de conversão.",
        stable: "Busque oportunidades de otimização incremental."
      },
      timeToFill: {
        up: "Revise processo para reduzir tempo. Considere automação.",
        down: "Ótimo progresso! Mantenha foco na eficiência.",
        stable: "Benchmarke com mercado e identifique melhorias."
      }
    }

    return baseRecommendations[metric]?.[trend] || "Monitore tendência e ajuste estratégia conforme necessário."
  }

  // Detectar anomalias
  detectAnomalies(): MLInsight[] {
    const insights: MLInsight[] = []

    // Detectar picos anômalos
    const recentData = this.data.slice(-30)
    const applications = recentData.map(d => d.applications)
    const avgApplications = applications.reduce((a, b) => a + b, 0) / applications.length
    const maxApplications = Math.max(...applications)

    if (maxApplications > avgApplications * 1.5) {
      insights.push({
        type: 'anomaly',
        title: 'Pico Anômalo de Candidaturas',
        description: `Detectado aumento de ${Math.round((maxApplications / avgApplications - 1) * 100)}% nas candidaturas`,
        impact: 'high',
        actionable: true,
        suggestion: 'Investigar causa e preparar recursos para triagem'
      })
    }

    // Detectar correlações
    const timeVsCost = this.analyzeCorrelation('timeToFill', 'cost')
    if (timeVsCost > 0.7) {
      insights.push({
        type: 'correlation',
        title: 'Correlação: Tempo vs Custo',
        description: `Alta correlação (${(timeVsCost * 100).toFixed(0)}%) entre tempo de contratação e custo`,
        impact: 'medium',
        actionable: true,
        suggestion: 'Reduzir tempo pode diminuir custos significativamente'
      })
    }

    return insights
  }

  // Análise de correlação simples
  private analyzeCorrelation(metric1: string, metric2: string): number {
    const data1 = this.data.map(d => d[metric1 as keyof HistoricalDataPoint] as number)
    const data2 = this.data.map(d => d[metric2 as keyof HistoricalDataPoint] as number)

    const n = data1.length
    const sum1 = data1.reduce((a, b) => a + b, 0)
    const sum2 = data2.reduce((a, b) => a + b, 0)
    const sum1Sq = data1.reduce((sum, val) => sum + val * val, 0)
    const sum2Sq = data2.reduce((sum, val) => sum + val * val, 0)
    const pSum = data1.reduce((sum, val, i) => sum + val * data2[i], 0)

    const num = pSum - (sum1 * sum2 / n)
    const den = Math.sqrt((sum1Sq - sum1 * sum1 / n) * (sum2Sq - sum2 * sum2 / n))

    return den === 0 ? 0 : num / den
  }

  // Scoring de candidatos
  scoreCandidates(candidates: MLCandidate[]): CandidateScore[] {
    return candidates.map(candidate => {
      // Algoritmo de scoring baseado em múltiplos fatores
      const experienceScore = this.calculateExperienceScore(candidate)
      const skillsMatch = this.calculateSkillsMatch(candidate)
      const culturalFit = this.calculateCulturalFit(candidate)

      const overallScore = (experienceScore * 0.4 + skillsMatch * 0.4 + culturalFit * 0.2)
      const successProbability = overallScore * 0.85 + Math.random() * 0.3

      return {
        candidateId: candidate.id || Math.random().toString(),
        name: candidate.name || 'Candidato',
        overallScore: Math.round(overallScore),
        skillsMatch: Math.round(skillsMatch),
        experienceScore: Math.round(experienceScore),
        culturalFit: Math.round(culturalFit),
        successProbability: Math.round(Math.min(successProbability, 100)),
        timeToOnboard: Math.round(15 + Math.random() * 20),
        retentionRisk: Math.round(20 + Math.random() * 30)
      }
    })
  }

  private calculateExperienceScore(candidate: MLCandidate): number {
    // Simulação de scoring de experiência
    const baseScore = 70
    const variation = Math.random() * 30
    return Math.min(baseScore + variation, 100)
  }

  private calculateSkillsMatch(candidate: MLCandidate): number {
    // Simulação de matching de skills
    const baseScore = 75
    const variation = Math.random() * 25
    return Math.min(baseScore + variation, 100)
  }

  private calculateCulturalFit(candidate: MLCandidate): number {
    // Simulação de fit cultural
    const baseScore = 80
    const variation = Math.random() * 20
    return Math.min(baseScore + variation, 100)
  }
}

interface RecruitmentMLDashboardProps {
  candidates?: MLCandidate[]
  historicalData?: HistoricalDataPoint[]
}

export function RecruitmentMLDashboard({
  candidates = [],
  historicalData
}: RecruitmentMLDashboardProps) {
  const [mlEngine, setMLEngine] = useState<RecruitmentMLEngine | null>(null)
  const [predictions, setPredictions] = useState<MLPrediction[]>([])
  const [insights, setInsights] = useState<MLInsight[]>([])
  const [candidateScores, setCandidateScores] = useState<CandidateScore[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedTimeframe, setSelectedTimeframe] = useState<30 | 60 | 90>(30)

  useEffect(() => {
    const initializeML = async () => {
      setIsLoading(true)

      // Simular carregamento
      await new Promise(resolve => setTimeout(resolve, 1500))

      const data = historicalData || generateHistoricalData()
      const engine = new RecruitmentMLEngine(data)
      setMLEngine(engine)

      // Gerar predições
      const newPredictions = [
        engine.predictMetric('applications', selectedTimeframe),
        engine.predictMetric('hires', selectedTimeframe),
        engine.predictMetric('timeToFill', selectedTimeframe),
        engine.predictMetric('cost', selectedTimeframe)
      ]
      setPredictions(newPredictions)

      // Detectar insights
      const newInsights = engine.detectAnomalies()
      setInsights(newInsights)

      // Scoring de candidatos
      if (candidates.length > 0) {
        const scores = engine.scoreCandidates(candidates)
        setCandidateScores(scores)
      }

      setIsLoading(false)
    }

    initializeML()
  }, [selectedTimeframe, candidates, historicalData])

  const getPredictionIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-5 h-5 text-status-success" />
      case 'down': return <TrendingDown className="w-5 h-5 text-status-error" />
      default: return <Activity className="w-5 h-5 lia-text-base" />
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 85) return 'text-status-success bg-status-success/10'
    if (confidence >= 70) return 'text-status-warning bg-status-warning/10'
    return 'text-status-error bg-status-error/10'
  }

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardContent className="p-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            <span className="ml-3 lia-text-base">Processando dados com ML...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="border-l-4 border-l-purple-500">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="font-sans flex items-center gap-2">
                <Brain className="w-5 h-5 text-wedo-cyan" />
                Inteligência Artificial em Recrutamento
              </CardTitle>
              <p className="text-sm text-gray-800 dark:text-lia-text-primary mt-1">
                Análises preditivas e insights baseados em Machine Learning
              </p>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={selectedTimeframe}
                onChange={(e) => setSelectedTimeframe(Number(e.target.value) as 30 | 60 | 90)}
                className="px-3 py-2 border border-lia-border-default rounded-md text-sm"
              >
                <option value={30}>Próximos 30 dias</option>
                <option value={60}>Próximos 60 dias</option>
                <option value={90}>Próximos 90 dias</option>
              </select>
              <Button variant="outline" size="sm" className="gap-2">
                <RefreshCw className="w-4 h-4" />
                Retreinar
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Predições */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {predictions.map((prediction, index) => (
          <Card key={index} className="relative overflow-hidden">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  {getPredictionIcon(prediction.trend)}
                  <h3 className="font-medium capitalize">{prediction.metric}</h3>
                </div>
                <Badge className={`text-xs ${getConfidenceColor(prediction.confidence)}`}>
                  {prediction.confidence}% confiança
                </Badge>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="lia-text-base">Atual:</span>
                  <span className="font-medium">{prediction.currentValue}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="lia-text-base">Previsto:</span>
                  <span className={`font-bold ${
 prediction.trend === 'up' ? 'text-status-success' :
                    prediction.trend === 'down' ? 'text-status-error' : 'lia-text-base'
                  }`}>
                    {prediction.predictedValue}
                  </span>
                </div>
                <div className="text-xs text-gray-800 dark:text-lia-text-primary">
                  Variação: {prediction.trend === 'up' ? '+' : prediction.trend === 'down' ? '-' : ''}
                  {Math.abs(prediction.predictedValue - prediction.currentValue)}
                </div>
              </div>

              <div className="mt-3 pt-3 border-t">
                <p className="text-xs lia-text-base">{prediction.recommendation}</p>
              </div>

              {/* Fatores influenciadores */}
              <div className="mt-2">
                <p className="text-xs font-medium text-gray-800 dark:text-lia-text-primary mb-1">Fatores chave:</p>
                <div className="flex flex-wrap gap-1">
                  {prediction.factors.slice(0, 2).map((factor, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {factor}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Insights de ML */}
      <Card>
        <CardHeader>
          <CardTitle className="font-sans flex items-center gap-2">
            <Zap className="w-5 h-5 text-status-warning" />
            Insights de Machine Learning
          </CardTitle>
        </CardHeader>
        <CardContent>
          {insights.length > 0 ? (
            <div className="space-y-4">
              {insights.map((insight, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-md border-l-4 ${
 insight.impact === 'high' ? 'bg-status-error/10 border-status-error' :
                    insight.impact === 'medium' ? 'bg-status-warning/10 border-status-warning' :
                    'bg-gray-100 dark:bg-lia-bg-secondary border-gray-900'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className={`font-medium mb-1 ${
 insight.impact === 'high' ? 'text-status-error/90' :
                        insight.impact === 'medium' ? 'text-status-warning/90' :
                        'text-wedo-cyan-dark'
                      }`}>
                        {insight.title}
                      </h4>
                      <p className={`text-sm mb-2 ${
 insight.impact === 'high' ? 'text-status-error' :
                        insight.impact === 'medium' ? 'text-status-warning' :
                        'text-wedo-cyan-dark'
                      }`}>
                        {insight.description}
                      </p>
                      {insight.suggestion && (
                        <p className={`text-sm font-medium ${
 insight.impact === 'high' ? 'text-status-error/90' :
                          insight.impact === 'medium' ? 'text-status-warning/90' :
                          'text-wedo-cyan-dark'
                        }`}>
                          💡 {insight.suggestion}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <Badge className={`text-xs ${
 insight.impact === 'high' ? 'bg-status-error/10 text-status-error' :
                        insight.impact === 'medium' ? 'bg-status-warning/10 text-status-warning' :
                        'bg-gray-100 dark:bg-lia-bg-secondary text-wedo-cyan-dark'
                      }`}>
                        {insight.type}
                      </Badge>
                      <Badge className={`text-xs ${
 insight.impact === 'high' ? 'bg-status-error text-white' :
                        insight.impact === 'medium' ? 'bg-status-warning text-white' :
                        'bg-gray-900 text-white'
                      }`}>
                        {insight.impact}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6 lia-text-base">
              <Brain className="w-12 h-12 mx-auto mb-4 text-wedo-cyan" />
              <p>Nenhuma anomalia detectada</p>
              <p className="text-sm">Tudo funcionando dentro dos padrões esperados</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Scoring de Candidatos */}
      {candidateScores.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="font-sans flex items-center gap-2">
              <Star className="w-5 h-5 text-wedo-orange" />
              Scoring Inteligente de Candidatos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {candidateScores.slice(0, 6).map((score, index) => (
                <div key={index} className="p-4 border border-lia-border-subtle rounded-md">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-gray-950">{score.name}</h4>
                    <Badge className={`${
 score.overallScore >= 85 ? 'bg-status-success/10 text-status-success' :
                      score.overallScore >= 70 ? 'bg-status-warning/10 text-status-warning' :
                      'bg-status-error/10 text-status-error'
                    }`}>
                      {score.overallScore}
                    </Badge>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="lia-text-base">Skills Match:</span>
                      <span className="font-medium">{score.skillsMatch}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="lia-text-base">Experiência:</span>
                      <span className="font-medium">{score.experienceScore}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="lia-text-base">Fit Cultural:</span>
                      <span className="font-medium">{score.culturalFit}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="lia-text-base">Prob. Sucesso:</span>
                      <span className="font-medium text-status-success">{score.successProbability}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
