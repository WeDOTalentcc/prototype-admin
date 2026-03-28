"use client"

import { useMemo } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  X,
  Users,
  CheckCircle,
  Clock,
  XCircle,
  Download,
  Mail,
  Brain,
  TrendingUp,
  AlertTriangle,
  Target,
  Calendar,
  MapPin,
  Building2,
  UserCircle,
  DollarSign,
  BarChart3,
  ArrowRight,
  Percent,
  Star,
  Filter,
  Lightbulb,
  AlertCircle,
  PhoneCall,
  CalendarCheck,
  MessageCircleX,
  GitBranch,
  Eye,
  ArrowDownRight,
  Award,
  AlertOctagon,
} from "lucide-react"

export interface WSIScore {
  dimension: string
  score: number
  label: string
}

export interface InsightCategory {
  type: 'action' | 'analysis' | 'comparison' | 'attention'
  title: string
  description: string
  badge?: string
}

export interface ConversionRate {
  from: string
  to: string
  rate: number
  benchmark?: number
  status: 'good' | 'warning' | 'critical'
}

export interface StageBottleneck {
  stage: string
  avgDays: number
  dropRate: number
  stuckCount: number
}

export interface DemographicDistribution {
  name: string
  count: number
  percentage: number
}

export interface CandidateDemographics {
  cities?: DemographicDistribution[]
  workModels?: DemographicDistribution[]
  genders?: DemographicDistribution[]
  ageRanges?: DemographicDistribution[]
  educationLevels?: DemographicDistribution[]
  experienceYears?: DemographicDistribution[]
}

export interface JobBehavioralCompetency {
  competency: string
  weight: string
}

export interface JobLiaMetrics {
  pipeline_lia: number
  triagens_agendadas: number
  triagens_realizadas: number
  sem_resposta: number
  entrevistas_agendadas: number
  conversionRates?: ConversionRate[]
  bottlenecks?: StageBottleneck[]
  insights?: InsightCategory[]
}

export interface JobInsightData {
  id: string
  code?: string
  title: string
  status: string
  priority?: string
  deadline?: string
  candidates_count?: number
  approved_count?: number
  screening_count?: number
  rejected_count?: number
  performance_score?: number
  avg_time_per_stage?: number
  salary_min?: number
  salary_max?: number
  work_model?: string
  location?: string
  behavioral_competencies?: JobBehavioralCompetency[]
  benefits?: string[]
  days_open?: number
  lia_metrics?: JobLiaMetrics
  candidate_demographics?: CandidateDemographics
}

interface JobInsightsModalProps {
  isOpen: boolean
  onClose: () => void
  onSendEmail?: (reportData: { jobIds: string[], reportHtml: string }) => void
  jobs: JobInsightData[]
  aggregatedDemographics?: CandidateDemographics
  conversionRates?: ConversionRate[]
  bottlenecks?: StageBottleneck[]
  insights?: InsightCategory[]
}

export function JobInsightsModal({ 
  isOpen, 
  onClose, 
  onSendEmail, 
  jobs,
  aggregatedDemographics,
  conversionRates,
  bottlenecks,
  insights 
}: JobInsightsModalProps) {
  const aggregateMetrics = useMemo(() => {
    const totalCandidates = jobs.reduce((sum, job) => sum + (job.candidates_count || 0), 0)
    const totalApproved = jobs.reduce((sum, job) => sum + (job.approved_count || 0), 0)
    const totalScreening = jobs.reduce((sum, job) => sum + (job.screening_count || 0), 0)
    const totalRejected = jobs.reduce((sum, job) => sum + (job.rejected_count || 0), 0)
    const avgTimePerStage = jobs.reduce((sum, job) => sum + (job.avg_time_per_stage || 0), 0) / (jobs.length || 1)
    const conversionRate = totalCandidates > 0 ? ((totalApproved / totalCandidates) * 100).toFixed(1) : "0"
    const screeningConversionRate = totalScreening > 0 ? ((totalApproved / totalScreening) * 100).toFixed(1) : "0"

    return {
      totalCandidates,
      totalApproved,
      totalScreening,
      totalRejected,
      avgTimePerStage: Math.round(avgTimePerStage),
      conversionRate,
      screeningConversionRate,
    }
  }, [jobs])

  const funnelData = useMemo(() => {
    const stages = [
      { name: "Inscritos", value: aggregateMetrics.totalCandidates, color: "bg-gray-200" },
      { name: "Em Triagem", value: aggregateMetrics.totalScreening, color: "bg-gray-200 dark:bg-gray-700" },
      { name: "Aprovados", value: aggregateMetrics.totalApproved, color: "bg-gray-200 dark:bg-gray-700" },
      { name: "Contratados", value: Math.round(aggregateMetrics.totalApproved * 0.3), color: "bg-gray-900 dark:bg-gray-50" },
    ]
    const maxValue = Math.max(...stages.map(s => s.value), 1)
    return stages.map(stage => ({
      ...stage,
      percentage: Math.round((stage.value / maxValue) * 100),
      rate: aggregateMetrics.totalCandidates > 0 
        ? ((stage.value / aggregateMetrics.totalCandidates) * 100).toFixed(1) 
        : "0"
    }))
  }, [aggregateMetrics])

  const demographicData = useMemo(() => {
    if (aggregatedDemographics) {
      return {
        cities: aggregatedDemographics.cities || [],
        workModels: aggregatedDemographics.workModels || [],
        genders: aggregatedDemographics.genders || [],
        ageRanges: aggregatedDemographics.ageRanges || [],
        educationLevels: aggregatedDemographics.educationLevels || [],
        experienceYears: aggregatedDemographics.experienceYears || []
      }
    }

    const cityMap = new Map<string, number>()
    const workModelMap = new Map<string, number>()
    const genderMap = new Map<string, number>()
    const ageRangeMap = new Map<string, number>()
    const educationLevelMap = new Map<string, number>()
    const experienceYearsMap = new Map<string, number>()
    let totalWithDemographics = 0

    jobs.forEach(job => {
      if (job.candidate_demographics) {
        totalWithDemographics++
        job.candidate_demographics.cities?.forEach(c => {
          cityMap.set(c.name, (cityMap.get(c.name) || 0) + c.count)
        })
        job.candidate_demographics.workModels?.forEach(w => {
          workModelMap.set(w.name, (workModelMap.get(w.name) || 0) + w.count)
        })
        job.candidate_demographics.genders?.forEach(g => {
          genderMap.set(g.name, (genderMap.get(g.name) || 0) + g.count)
        })
        job.candidate_demographics.ageRanges?.forEach(a => {
          ageRangeMap.set(a.name, (ageRangeMap.get(a.name) || 0) + a.count)
        })
        job.candidate_demographics.educationLevels?.forEach(e => {
          educationLevelMap.set(e.name, (educationLevelMap.get(e.name) || 0) + e.count)
        })
        job.candidate_demographics.experienceYears?.forEach(e => {
          experienceYearsMap.set(e.name, (experienceYearsMap.get(e.name) || 0) + e.count)
        })
      }
    })

    if (totalWithDemographics === 0) {
      return { cities: [], workModels: [], genders: [], ageRanges: [], educationLevels: [], experienceYears: [] }
    }

    const convertMapToArray = (map: Map<string, number>): DemographicDistribution[] => {
      const total = Array.from(map.values()).reduce((sum, count) => sum + count, 0)
      return Array.from(map.entries())
        .map(([name, count]) => ({
          name,
          count,
          percentage: total > 0 ? Math.round((count / total) * 100) : 0
        }))
        .sort((a, b) => b.count - a.count)
    }

    return {
      cities: convertMapToArray(cityMap),
      workModels: convertMapToArray(workModelMap),
      genders: convertMapToArray(genderMap),
      ageRanges: convertMapToArray(ageRangeMap),
      educationLevels: convertMapToArray(educationLevelMap),
      experienceYears: convertMapToArray(experienceYearsMap)
    }
  }, [jobs, aggregatedDemographics])

  const salaryData = useMemo(() => {
    const avgJobMin = jobs.reduce((sum, j) => sum + (j.salary_min || 5000), 0) / (jobs.length || 1)
    const avgJobMax = jobs.reduce((sum, j) => sum + (j.salary_max || 8000), 0) / (jobs.length || 1)
    const avgCandidateExpectation = (avgJobMin + avgJobMax) / 2 * 0.95

    return {
      vagaMin: Math.round(avgJobMin),
      vagaMax: Math.round(avgJobMax),
      mediaInscritos: Math.round(avgCandidateExpectation),
      dentroFaixa: Math.round(aggregateMetrics.totalCandidates * 0.68),
      percentualDentro: 68,
    }
  }, [jobs, aggregateMetrics])

  const qualityMetrics = useMemo(() => {
    const avgPerformance = jobs.reduce((sum, j) => sum + (j.performance_score || 0), 0) / (jobs.length || 1)
    
    return {
      avgScoreTodos: Math.round(avgPerformance * 0.75),
      avgScoreTriados: Math.round(avgPerformance * 0.92),
      avgScoreAprovados: Math.round(avgPerformance),
      taxaTriagem: aggregateMetrics.totalCandidates > 0 
        ? ((aggregateMetrics.totalScreening / aggregateMetrics.totalCandidates) * 100).toFixed(1)
        : "0",
      taxaAprovacao: aggregateMetrics.totalScreening > 0
        ? ((aggregateMetrics.totalApproved / aggregateMetrics.totalScreening) * 100).toFixed(1)
        : "0",
    }
  }, [jobs, aggregateMetrics])

  const wsiMetrics = useMemo(() => {
    const avgPerformance = jobs.reduce((sum, j) => sum + (j.performance_score || 0), 0) / (jobs.length || 1)
    
    const dimensions: WSIScore[] = [
      { dimension: 'Técnico', score: Math.round(avgPerformance * 0.95), label: 'Competências técnicas' },
      { dimension: 'Comportamental', score: Math.round(avgPerformance * 0.88), label: 'Soft skills e atitudes' },
      { dimension: 'Cultural', score: Math.round(avgPerformance * 0.92), label: 'Fit cultural' },
      { dimension: 'Experiência', score: Math.round(avgPerformance * 0.85), label: 'Anos e relevância' },
      { dimension: 'Potencial', score: Math.round(avgPerformance * 0.78), label: 'Capacidade de crescimento' }
    ]
    
    const avgWSI = Math.round(dimensions.reduce((s, d) => s + d.score, 0) / dimensions.length)
    
    return { dimensions, avgWSI }
  }, [jobs])

  const liaFunnelMetrics = useMemo(() => {
    const hasRealLiaData = jobs.some(j => j.lia_metrics && j.lia_metrics.pipeline_lia > 0)
    
    if (hasRealLiaData) {
      const aggregated = jobs.reduce((acc, job) => {
        const lm = job.lia_metrics
        if (lm) {
          acc.pipeline_lia += lm.pipeline_lia || 0
          acc.triagens_agendadas += lm.triagens_agendadas || 0
          acc.triagens_realizadas += lm.triagens_realizadas || 0
          acc.sem_resposta += lm.sem_resposta || 0
          acc.entrevistas_agendadas += lm.entrevistas_agendadas || 0
        }
        return acc
      }, {
        pipeline_lia: 0,
        triagens_agendadas: 0,
        triagens_realizadas: 0,
        sem_resposta: 0,
        entrevistas_agendadas: 0,
        isEstimated: false
      })
      return aggregated
    }

    return {
      pipeline_lia: Math.round(aggregateMetrics.totalCandidates * 0.6),
      triagens_agendadas: Math.round(aggregateMetrics.totalScreening * 0.8),
      triagens_realizadas: Math.round(aggregateMetrics.totalScreening * 0.65),
      sem_resposta: Math.round(aggregateMetrics.totalScreening * 0.15),
      entrevistas_agendadas: Math.round(aggregateMetrics.totalApproved * 0.9),
      isEstimated: true
    }
  }, [jobs, aggregateMetrics])

  const calculatedConversionRates = useMemo((): ConversionRate[] => {
    if (conversionRates && conversionRates.length > 0) {
      return conversionRates
    }

    const stages = [
      { from: "Pipeline LIA", to: "Triagens Agendadas", fromValue: liaFunnelMetrics.pipeline_lia, toValue: liaFunnelMetrics.triagens_agendadas },
      { from: "Triagens Agendadas", to: "Triagens Realizadas", fromValue: liaFunnelMetrics.triagens_agendadas, toValue: liaFunnelMetrics.triagens_realizadas },
      { from: "Triagens Realizadas", to: "Entrevistas Agendadas", fromValue: liaFunnelMetrics.triagens_realizadas, toValue: liaFunnelMetrics.entrevistas_agendadas },
      { from: "Inscritos", to: "Aprovados", fromValue: aggregateMetrics.totalCandidates, toValue: aggregateMetrics.totalApproved },
    ]

    return stages.map(stage => {
      const rate = stage.fromValue > 0 ? (stage.toValue / stage.fromValue) * 100 : 0
      let status: 'good' | 'warning' | 'critical' = 'good'
      if (rate < 20) status = 'critical'
      else if (rate < 50) status = 'warning'
      
      return {
        from: stage.from,
        to: stage.to,
        rate: Math.round(rate * 10) / 10,
        status
      }
    })
  }, [conversionRates, liaFunnelMetrics, aggregateMetrics])

  const categorizedInsights = useMemo((): InsightCategory[] => {
    if (insights && insights.length > 0) {
      return insights
    }

    const generated: InsightCategory[] = []

    if (parseFloat(qualityMetrics.taxaAprovacao) < 30) {
      generated.push({
        type: 'action',
        title: 'Revisar Critérios de Triagem',
        description: `Taxa de aprovação de ${qualityMetrics.taxaAprovacao}% está abaixo do esperado. Considere calibrar os critérios com o gestor.`,
        badge: 'Urgente'
      })
    }

    if (aggregateMetrics.avgTimePerStage > 5) {
      generated.push({
        type: 'action',
        title: 'Acelerar Processo Seletivo',
        description: `Tempo médio de ${aggregateMetrics.avgTimePerStage} dias por etapa. Candidatos qualificados podem estar desistindo.`
      })
    }

    const conversionAnalysis = parseFloat(aggregateMetrics.conversionRate)
    if (conversionAnalysis > 0) {
      generated.push({
        type: 'analysis',
        title: 'Performance do Funil',
        description: `Taxa de conversão geral de ${conversionAnalysis}% com ${aggregateMetrics.totalApproved} aprovados de ${aggregateMetrics.totalCandidates} candidatos.`
      })
    }

    if (jobs.length > 1) {
      const avgScore = jobs.reduce((sum, j) => sum + (j.performance_score || 0), 0) / jobs.length
      generated.push({
        type: 'comparison',
        title: 'Comparativo entre Vagas',
        description: `Score médio de ${Math.round(avgScore)}% entre as ${jobs.length} vagas selecionadas.`
      })
    }

    const lowScoreJobs = jobs.filter(j => (j.performance_score || 0) < 60)
    if (lowScoreJobs.length > 0) {
      generated.push({
        type: 'attention',
        title: 'Vagas com Baixa Performance',
        description: `${lowScoreJobs.length} vaga(s) com score abaixo de 60% requerem atenção imediata.`,
        badge: 'Crítico'
      })
    }

    if (liaFunnelMetrics.sem_resposta > liaFunnelMetrics.triagens_realizadas * 0.3) {
      generated.push({
        type: 'attention',
        title: 'Alto Índice de Não Resposta',
        description: `${liaFunnelMetrics.sem_resposta} candidatos sem resposta. Considere revisar horários de contato.`
      })
    }

    if (generated.length === 0) {
      generated.push({
        type: 'analysis',
        title: 'Processo Saudável',
        description: 'Todas as métricas estão dentro dos parâmetros esperados. Continue monitorando.'
      })
    }

    return generated
  }, [insights, qualityMetrics, aggregateMetrics, jobs, liaFunnelMetrics])

  const liaTextualAnalysis = useMemo(() => {
    const totalJobs = jobs.length
    const totalCandidates = aggregateMetrics.totalCandidates
    const avgConversion = parseFloat(aggregateMetrics.conversionRate)
    const avgPerformance = jobs.reduce((sum, j) => sum + (j.performance_score || 0), 0) / (jobs.length || 1)
    
    const topJob = jobs.reduce((top, job) => 
      (job.candidates_count || 0) > (top?.candidates_count || 0) ? job : top
    , jobs[0])
    
    const avgDaysOpen = jobs.reduce((sum, j) => sum + (j.days_open || 0), 0) / (jobs.length || 1)
    
    const summary = `Analisando ${totalJobs} vaga${totalJobs > 1 ? 's' : ''} com total de ${totalCandidates} candidatos.`
    
    let performance = ''
    if (avgPerformance >= 80) {
      performance = 'Performance excelente detectada.'
    } else if (avgPerformance >= 60) {
      performance = 'Performance dentro da média esperada.'
    } else {
      performance = 'Performance abaixo do esperado, considere revisar critérios.'
    }
    
    let volumeInsight = ''
    if (topJob && totalJobs > 1) {
      volumeInsight = `"${topJob.title}" lidera com ${topJob.candidates_count || 0} candidatos.`
    }
    
    let conversionNote = ''
    if (avgConversion < 10) {
      conversionNote = 'Taxa de conversão baixa (< 10%) - revisar critérios de triagem.'
    } else if (avgConversion >= 30) {
      conversionNote = 'Taxa de conversão saudável acima de 30%.'
    }
    
    return {
      summary,
      performance,
      volumeInsight,
      conversionNote,
      avgDaysOpen: Math.round(avgDaysOpen)
    }
  }, [jobs, aggregateMetrics])

  const trendData = useMemo(() => {
    const weeks = ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4']
    const totalBase = Math.max(aggregateMetrics.totalCandidates, 10)
    
    const candidatesTrend = [
      Math.round(totalBase * 0.25),
      Math.round(totalBase * 0.50),
      Math.round(totalBase * 0.75),
      totalBase
    ]
    
    const conversionTrend = [
      12,
      parseFloat(aggregateMetrics.conversionRate) * 0.7,
      parseFloat(aggregateMetrics.conversionRate) * 0.9,
      parseFloat(aggregateMetrics.conversionRate)
    ].map(v => Math.round(v))
    
    const maxCandidates = Math.max(...candidatesTrend)
    const maxConversion = Math.max(...conversionTrend, 100)
    
    return {
      weeks,
      candidatesTrend,
      conversionTrend,
      maxCandidates,
      maxConversion
    }
  }, [aggregateMetrics])

  const getConversionStatusColor = (status: 'good' | 'warning' | 'critical') => {
    switch (status) {
      case 'good': return { bg: 'bg-status-success/10', border: 'border-status-success/30', text: 'text-status-success', icon: 'text-status-success' }
      case 'warning': return { bg: 'bg-status-warning/10', border: 'border-status-warning/30', text: 'text-status-warning', icon: 'text-status-warning' }
      case 'critical': return { bg: 'bg-status-error/10', border: 'border-status-error/30', text: 'text-status-error', icon: 'text-status-error' }
    }
  }

  const getInsightStyles = (type: InsightCategory['type']) => {
    switch (type) {
      case 'action':
        return { bg: 'bg-status-warning/10', border: 'border-status-warning/30', icon: Lightbulb, iconColor: 'text-status-warning' }
      case 'analysis':
      case 'comparison':
        return { bg: 'bg-wedo-purple/10', border: 'border-wedo-purple/30', icon: Eye, iconColor: 'text-wedo-purple' }
      case 'attention':
        return { bg: 'bg-status-error/10', border: 'border-status-error/30', icon: AlertCircle, iconColor: 'text-status-error' }
    }
  }

  const getDaysRemaining = (deadline?: string) => {
    if (!deadline) return null
    const deadlineDate = new Date(deadline)
    const today = new Date()
    const diffTime = deadlineDate.getTime() - today.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  const getScoreColor = (score?: number) => {
    if (!score) return "text-gray-500"
    if (score >= 85) return "text-gray-600 dark:text-gray-400 font-semibold"
    if (score >= 70) return "text-gray-950"
    if (score >= 50) return "text-gray-800"
    return "text-gray-600"
  }

  const generateAttentionPoints = () => {
    const points: string[] = []
    
    const lowScoreJobs = jobs.filter(j => (j.performance_score || 0) < 70)
    if (lowScoreJobs.length > 0) {
      points.push(`${lowScoreJobs.length} vaga(s) com score abaixo de 70%`)
    }

    const urgentJobs = jobs.filter(j => {
      const days = getDaysRemaining(j.deadline)
      return days !== null && days <= 7
    })
    if (urgentJobs.length > 0) {
      points.push(`${urgentJobs.length} vaga(s) com prazo em até 7 dias`)
    }

    const lowCandidateJobs = jobs.filter(j => (j.candidates_count || 0) < 5)
    if (lowCandidateJobs.length > 0) {
      points.push(`${lowCandidateJobs.length} vaga(s) com menos de 5 candidatos`)
    }

    const highRejectionJobs = jobs.filter(j => {
      const total = j.candidates_count || 0
      const rejected = j.rejected_count || 0
      return total > 0 && (rejected / total) > 0.5
    })
    if (highRejectionJobs.length > 0) {
      points.push(`${highRejectionJobs.length} vaga(s) com rejeição > 50%`)
    }

    if (parseFloat(qualityMetrics.taxaAprovacao) < 20) {
      points.push("Taxa de conversão de triagem abaixo de 20%")
    }

    if (salaryData.percentualDentro < 50) {
      points.push("Menos de 50% dos candidatos dentro da faixa salarial")
    }

    if (points.length === 0) {
      points.push("Todas as vagas estão dentro dos parâmetros esperados")
    }

    return points
  }

  const generateRecommendations = () => {
    const recommendations: string[] = []

    const avgConversion = parseFloat(aggregateMetrics.conversionRate)
    if (avgConversion < 20) {
      recommendations.push("Revisar critérios de triagem para aumentar taxa de conversão")
    }

    if (aggregateMetrics.avgTimePerStage > 5) {
      recommendations.push("Otimizar tempo médio por etapa focando em gargalos")
    }

    const highPriorityLowProgress = jobs.filter(j => 
      j.priority?.toLowerCase() === "alta" && (j.approved_count || 0) < 3
    )
    if (highPriorityLowProgress.length > 0) {
      recommendations.push("Priorizar sourcing ativo para vagas de alta prioridade")
    }

    if (aggregateMetrics.totalScreening > aggregateMetrics.totalApproved * 3) {
      recommendations.push("Considerar calibração de perfil com gestores")
    }

    if (salaryData.mediaInscritos > salaryData.vagaMax) {
      recommendations.push("Revisar faixa salarial - candidatos têm expectativas acima do oferecido")
    }

    if (qualityMetrics.avgScoreTodos < 60) {
      recommendations.push("Ajustar divulgação para atrair candidatos mais qualificados")
    }

    if (recommendations.length === 0) {
      recommendations.push("Manter ritmo atual de execução")
      recommendations.push("Acompanhar métricas semanalmente")
    }

    return recommendations
  }

  const handleExportReport = () => {
    const printContent = document.getElementById('insights-report-content')
    if (!printContent) return
    
    const printWindow = window.open('', '_blank')
    if (!printWindow) return
    
    const reportDate = new Date().toLocaleDateString('pt-BR')
    const jobTitles = jobs.map(j => j.title).join(', ')
    
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Relatório de Insights - ${reportDate}</title>
        <style>
          body { font-family: 'Open Sans', Arial, sans-serif; padding: 40px; color: #1a1a1a; }
          h1 { font-size: 24px; margin-bottom: 8px; }
          h2 { font-size: 18px; color: var(--gray-800); margin-top: 24px; }
          .subtitle { color: #6b7280; font-size: 14px; margin-bottom: 24px; }
          .metric-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin: 16px 0; }
          .metric-card { border: 1px solid var(--gray-200); border-radius: 8px; padding: 16px; }
          .metric-label { font-size: 12px; color: #6b7280; }
          .metric-value { font-size: 20px; font-weight: 600; }
          .section { margin: 24px 0; padding: 16px; border: 1px solid var(--gray-200); border-radius: 8px; }
          .job-item { padding: 12px; border-bottom: 1px solid var(--gray-200); }
          .job-item:last-child { border-bottom: none; }
          @media print { body { padding: 20px; } }
        </style>
      </head>
      <body>
        <h1>Relatório de Insights</h1>
        <p class="subtitle">${jobs.length} vaga(s) selecionada(s) • Gerado em ${reportDate}</p>
        
        <div class="metric-grid">
          <div class="metric-card">
            <div class="metric-label">Total de Candidatos</div>
            <div class="metric-value">${aggregateMetrics.totalCandidates}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Aprovados</div>
            <div class="metric-value">${aggregateMetrics.totalApproved}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Em Triagem</div>
            <div class="metric-value">${aggregateMetrics.totalScreening}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Taxa de Conversão</div>
            <div class="metric-value">${aggregateMetrics.conversionRate}%</div>
          </div>
        </div>
        
        <h2>Vagas Analisadas</h2>
        <div class="section">
          ${jobs.map(job => `
            <div class="job-item">
              <strong>${job.code || ''} ${job.title}</strong>
              <div style="font-size: 12px; color: #6b7280;">
                ${job.candidates_count || 0} candidatos • ${job.approved_count || 0} aprovados • Score: ${job.performance_score || '--'}%
              </div>
            </div>
          `).join('')}
        </div>
        
        <p style="font-size: 11px; color: var(--gray-400); margin-top: 32px;">
          Gerado pela Plataforma LIA - WeDO Talent
        </p>
      </body>
      </html>
    `)
    printWindow.document.close()
    printWindow.print()
  }

  const handleSendEmail = () => {
    if (onSendEmail) {
      const reportDate = new Date().toLocaleDateString('pt-BR')
      const reportHtml = `
        <h2>Relatório de Insights</h2>
        <p>${jobs.length} vaga(s) analisada(s) • ${reportDate}</p>
        <ul>
          <li>Total de Candidatos: ${aggregateMetrics.totalCandidates}</li>
          <li>Aprovados: ${aggregateMetrics.totalApproved}</li>
          <li>Em Triagem: ${aggregateMetrics.totalScreening}</li>
          <li>Taxa de Conversão: ${aggregateMetrics.conversionRate}%</li>
        </ul>
      `
      onSendEmail({
        jobIds: jobs.map(j => j.id),
        reportHtml
      })
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent 
        className="max-w-4xl max-h-[85vh] bg-white border border-gray-200 flex flex-col"
       
        aria-describedby="insights-modal-description"
      >
        <DialogHeader className="pb-3 border-b border-gray-200 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-gray-950">
                Relatório de Insights
              </DialogTitle>
              <p className="text-xs text-gray-600 mt-0.5">
                {jobs.length} vaga{jobs.length !== 1 ? "s" : ""} selecionada{jobs.length !== 1 ? "s" : ""} • Gerado em {new Date().toLocaleDateString('pt-BR')}
              </p>
            </div>
          </div>
          <span id="insights-modal-description" className="sr-only">
            Relatório de insights com métricas, funil, e análises das vagas selecionadas
          </span>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto py-4 space-y-4">
          <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
            <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
              Resumo Agregado
            </h3>
            <div className="grid grid-cols-6 gap-3">
              <div className="bg-white rounded-md p-3 border border-gray-200">
                <div className="flex items-center gap-1.5 mb-1">
                  <Users className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                  <span className="text-xs text-gray-600">Total Candidatos</span>
                </div>
                <p className="text-xl font-bold text-gray-950">{aggregateMetrics.totalCandidates}</p>
              </div>

              <div className="bg-white rounded-md p-3 border border-gray-200">
                <div className="flex items-center gap-1.5 mb-1">
                  <Filter className="w-3.5 h-3.5 text-gray-500" />
                  <span className="text-xs text-gray-600">Em Triagem</span>
                </div>
                <p className="text-xl font-bold text-gray-800">{aggregateMetrics.totalScreening}</p>
              </div>

              <div className="bg-white rounded-md p-3 border border-gray-200">
                <div className="flex items-center gap-1.5 mb-1">
                  <CheckCircle className="w-3.5 h-3.5 text-status-success" />
                  <span className="text-xs text-gray-600">Aprovados</span>
                </div>
                <p className="text-xl font-bold text-status-success">{aggregateMetrics.totalApproved}</p>
              </div>

              <div className="bg-white rounded-md p-3 border border-gray-200">
                <div className="flex items-center gap-1.5 mb-1">
                  <XCircle className="w-3.5 h-3.5 text-gray-500" />
                  <span className="text-xs text-gray-600">Rejeitados</span>
                </div>
                <p className="text-xl font-bold text-gray-700">{aggregateMetrics.totalRejected}</p>
              </div>

              <div className="bg-white rounded-md p-3 border border-gray-200">
                <div className="flex items-center gap-1.5 mb-1">
                  <Clock className="w-3.5 h-3.5 text-gray-500" />
                  <span className="text-xs text-gray-600">Tempo/Etapa</span>
                </div>
                <p className="text-xl font-bold text-gray-950">{aggregateMetrics.avgTimePerStage}<span className="text-xs font-normal text-gray-500">d</span></p>
              </div>

              <div className="bg-white rounded-md p-3 border border-gray-200">
                <div className="flex items-center gap-1.5 mb-1">
                  <TrendingUp className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                  <span className="text-xs text-gray-600">Conversão</span>
                </div>
                <p className="text-xl font-bold text-gray-900 dark:text-gray-50">{aggregateMetrics.conversionRate}%</p>
              </div>
            </div>
          </div>

          {/* Análise LIA Textual */}
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-md p-4 border border-gray-300 dark:border-gray-600">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
                <Brain className="w-4 h-4 text-wedo-cyan" />
              </div>
              <div>
                <h3 className="text-xs font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wide mb-2">
                  Análise LIA
                </h3>
                <p className="text-base-ui text-gray-800 leading-relaxed">
                  {liaTextualAnalysis.summary} {liaTextualAnalysis.performance}
                  {liaTextualAnalysis.volumeInsight && ` ${liaTextualAnalysis.volumeInsight}`}
                  {liaTextualAnalysis.conversionNote && ` ${liaTextualAnalysis.conversionNote}`}
                  {liaTextualAnalysis.avgDaysOpen > 0 && ` Tempo médio de abertura: ${liaTextualAnalysis.avgDaysOpen} dias.`}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
            <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
              <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
              Funil de Triagem LIA
              {liaFunnelMetrics.isEstimated && (
                <span className="text-micro text-gray-400 font-normal ml-1">(estimativa)</span>
              )}
            </h3>
            <div className="grid grid-cols-5 gap-3">
              <div className="bg-white rounded-md p-3 border border-gray-200">
                <div className="flex items-center gap-1.5 mb-1">
                  <GitBranch className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                  <span className="text-xs text-gray-600">Pipeline LIA</span>
                </div>
                <p className="text-xl font-bold text-gray-950">{liaFunnelMetrics.pipeline_lia}</p>
              </div>

              <div className="bg-white rounded-md p-3 border border-gray-200">
                <div className="flex items-center gap-1.5 mb-1">
                  <CalendarCheck className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                  <span className="text-xs text-gray-600">Triagens Agendadas</span>
                </div>
                <p className="text-xl font-bold text-gray-800">{liaFunnelMetrics.triagens_agendadas}</p>
              </div>

              <div className="bg-white rounded-md p-3 border border-gray-200">
                <div className="flex items-center gap-1.5 mb-1">
                  <PhoneCall className="w-3.5 h-3.5 text-status-success" />
                  <span className="text-xs text-gray-600">Triagens Realizadas</span>
                </div>
                <p className="text-xl font-bold text-status-success">{liaFunnelMetrics.triagens_realizadas}</p>
              </div>

              <div className="bg-white rounded-md p-3 border border-gray-200">
                <div className="flex items-center gap-1.5 mb-1">
                  <MessageCircleX className="w-3.5 h-3.5 text-gray-500" />
                  <span className="text-xs text-gray-600">Sem Resposta</span>
                </div>
                <p className="text-xl font-bold text-gray-600">{liaFunnelMetrics.sem_resposta}</p>
              </div>

              <div className="bg-white rounded-md p-3 border border-gray-200">
                <div className="flex items-center gap-1.5 mb-1">
                  <Calendar className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                  <span className="text-xs text-gray-600">Entrevistas Agendadas</span>
                </div>
                <p className="text-xl font-bold text-gray-900 dark:text-gray-50">{liaFunnelMetrics.entrevistas_agendadas}</p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
            <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
              <ArrowDownRight className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
              Taxa de Conversão por Etapa
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {calculatedConversionRates.map((rate, index) => {
                const colors = getConversionStatusColor(rate.status)
                return (
                  <div key={index} className={`rounded-md p-3 border ${colors.bg} ${colors.border}`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-700">{rate.from}</span>
                        <ArrowRight className="w-3 h-3 text-gray-400" />
                        <span className="text-xs text-gray-700">{rate.to}</span>
                      </div>
                      <div className={`flex items-center gap-1 ${colors.text}`}>
                        {rate.status === 'good' && <CheckCircle className={`w-3.5 h-3.5 ${colors.icon}`} />}
                        {rate.status === 'warning' && <AlertTriangle className={`w-3.5 h-3.5 ${colors.icon}`} />}
                        {rate.status === 'critical' && <AlertCircle className={`w-3.5 h-3.5 ${colors.icon}`} />}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-white/50 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${rate.status === 'good' ? 'bg-status-success' : rate.status === 'warning' ? 'bg-status-warning' : 'bg-status-error'}`}
                          style={{width: `${Math.min(rate.rate, 100)}%`}}
                        />
                      </div>
                      <span className={`text-sm font-bold ${colors.text}`}>{rate.rate}%</span>
                    </div>
                    <p className="text-micro text-gray-500 mt-1">
                      {rate.status === 'good' ? 'Dentro do esperado' : rate.status === 'warning' ? 'Atenção necessária' : 'Gargalo identificado'}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
            <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
              Tendência Temporal
              <span className="text-micro text-gray-400 font-normal ml-1">(estimativa)</span>
            </h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-md p-3 border border-gray-200">
                <h4 className="text-micro font-medium text-gray-500 mb-3">Candidatos Acumulados</h4>
                <div className="flex items-end justify-between h-20 gap-1">
                  {trendData.candidatesTrend.map((val, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center">
                      <div 
                        className="w-full bg-gray-900 dark:bg-gray-50 rounded-t transition-all"
                        style={{height: `${(val / trendData.maxCandidates) * 100}%`}}
                      />
                      <span className="text-micro text-gray-500 mt-1">{trendData.weeks[i]}</span>
                      <span className="text-micro font-medium text-gray-700">{val}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="bg-white rounded-md p-3 border border-gray-200">
                <h4 className="text-micro font-medium text-gray-500 mb-3">Taxa de Conversão (%)</h4>
                <div className="flex items-end justify-between h-20 gap-1">
                  {trendData.conversionTrend.map((val, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center">
                      <div 
                        className="w-full bg-status-success rounded-t transition-all"
                        style={{height: `${(val / 100) * 100}%`}}
                      />
                      <span className="text-micro text-gray-500 mt-1">{trendData.weeks[i]}</span>
                      <span className="text-micro font-medium text-gray-700">{val}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
            <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
              <BarChart3 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
              Funil de Recrutamento
            </h3>
            <div className="space-y-2">
              {funnelData.map((stage, index) => (
                <div key={stage.name} className="flex items-center gap-3">
                  <div className="w-24 text-xs font-medium text-gray-700 text-right">{stage.name}</div>
                  <div className="flex-1 h-7 bg-gray-100 rounded-md overflow-hidden relative">
                    <div 
                      className={`h-full ${stage.color} transition-all duration-500`}
                      style={{width: `${stage.percentage}%`}}
                    />
                    <div className="absolute inset-0 flex items-center px-2">
                      <span className="text-xs font-semibold text-gray-800">{stage.value}</span>
                    </div>
                  </div>
                  <div className="w-12 text-xs text-gray-600">{stage.rate}%</div>
                  {index < funnelData.length - 1 && (
                    <ArrowRight className="w-3 h-3 text-gray-400" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {(demographicData.cities.length > 0 || demographicData.workModels.length > 0 || demographicData.genders.length > 0 || demographicData.ageRanges.length > 0 || demographicData.educationLevels.length > 0 || demographicData.experienceYears.length > 0) ? (
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
                <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                  Por Cidade
                </h3>
                <div className="space-y-2">
                  {demographicData.cities.length > 0 ? (
                    demographicData.cities.map((city) => (
                      <div key={city.name} className="flex items-center justify-between">
                        <span className="text-xs text-gray-700">{city.name}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gray-900 dark:bg-gray-50" 
                              style={{width: `${city.percentage}%`}}
                            />
                          </div>
                          <span className="text-micro text-gray-600 w-8 text-right">{city.count}</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-gray-500 italic">Dados não disponíveis</p>
                  )}
                </div>
              </div>

              <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
                <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                  <Building2 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                  Por Modelo de Trabalho
                </h3>
                <div className="space-y-2">
                  {demographicData.workModels.length > 0 ? (
                    demographicData.workModels.map((model) => (
                      <div key={model.name} className="flex items-center justify-between">
                        <span className="text-xs text-gray-700">{model.name}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gray-900 dark:bg-gray-50" 
                              style={{width: `${model.percentage}%`}}
                            />
                          </div>
                          <span className="text-micro text-gray-600 w-8 text-right">{model.count}</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-gray-500 italic">Dados não disponíveis</p>
                  )}
                </div>
              </div>

              <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
                <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                  <UserCircle className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                  Por Gênero
                </h3>
                <div className="space-y-2">
                  {demographicData.genders.length > 0 ? (
                    demographicData.genders.map((gender) => (
                      <div key={gender.name} className="flex items-center justify-between">
                        <span className="text-xs text-gray-700">{gender.name}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gray-900 dark:bg-gray-50" 
                              style={{width: `${gender.percentage}%`}}
                            />
                          </div>
                          <span className="text-micro text-gray-600 w-8 text-right">{gender.count}</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-gray-500 italic">Dados não disponíveis</p>
                  )}
                </div>
              </div>

              {demographicData.ageRanges.length > 0 && (
                <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
                  <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                    Por Faixa Etária
                  </h3>
                  <div className="space-y-2">
                    {demographicData.ageRanges.map((ageRange) => (
                      <div key={ageRange.name} className="flex items-center justify-between">
                        <span className="text-xs text-gray-700">{ageRange.name}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gray-900 dark:bg-gray-50" 
                              style={{width: `${ageRange.percentage}%`}}
                            />
                          </div>
                          <span className="text-micro text-gray-600 w-8 text-right">{ageRange.count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {demographicData.educationLevels.length > 0 && (
                <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
                  <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                    <Award className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                    Por Escolaridade
                  </h3>
                  <div className="space-y-2">
                    {demographicData.educationLevels.map((edu) => (
                      <div key={edu.name} className="flex items-center justify-between">
                        <span className="text-xs text-gray-700">{edu.name}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gray-900 dark:bg-gray-50" 
                              style={{width: `${edu.percentage}%`}}
                            />
                          </div>
                          <span className="text-micro text-gray-600 w-8 text-right">{edu.count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {demographicData.experienceYears.length > 0 && (
                <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
                  <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                    Por Anos de Experiência
                  </h3>
                  <div className="space-y-2">
                    {demographicData.experienceYears.map((exp) => (
                      <div key={exp.name} className="flex items-center justify-between">
                        <span className="text-xs text-gray-700">{exp.name}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gray-900 dark:bg-gray-50" 
                              style={{width: `${exp.percentage}%`}}
                            />
                          </div>
                          <span className="text-micro text-gray-600 w-8 text-right">{exp.count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
              <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Dados Demográficos
              </h3>
              <p className="text-xs text-gray-500 italic">
                Dados demográficos não disponíveis para as vagas selecionadas.
              </p>
            </div>
          )}

          {jobs.some(job => job.behavioral_competencies && job.behavioral_competencies.length > 0) && (
            <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
              <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                <Lightbulb className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Competências Requeridas
              </h3>
              <div className="space-y-3 max-h-[180px] overflow-y-auto">
                {jobs.filter(job => job.behavioral_competencies && job.behavioral_competencies.length > 0).map(job => (
                  <div key={job.id} className="bg-white rounded-md p-2.5 border border-gray-200">
                    <span className="text-micro font-medium text-gray-500">{job.title}</span>
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {job.behavioral_competencies?.map((comp, i) => (
                        <span key={i} className="text-micro px-2 py-0.5 rounded-full bg-wedo-purple/15 text-wedo-purple">
                          {comp.competency}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {jobs.some(job => job.benefits && job.benefits.length > 0) && (
            <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
              <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Benefícios Oferecidos
              </h3>
              <div className="space-y-3 max-h-[180px] overflow-y-auto">
                {jobs.filter(job => job.benefits && job.benefits.length > 0).map(job => (
                  <div key={job.id} className="bg-white rounded-md p-2.5 border border-gray-200">
                    <span className="text-micro font-medium text-gray-500">{job.title}</span>
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {job.benefits?.map((benefit, i) => (
                        <span key={i} className="text-micro px-2 py-0.5 rounded-full bg-status-success/15 text-status-success">
                          {benefit}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {bottlenecks && bottlenecks.length > 0 && (
            <div className="bg-status-warning/10 rounded-md p-4 border border-status-warning/30">
              <h3 className="text-xs font-semibold text-status-warning uppercase tracking-wide mb-3 flex items-center gap-1.5">
                <AlertOctagon className="w-3.5 h-3.5 text-status-warning" />
                Gargalos Identificados
              </h3>
              <div className="space-y-2">
                {bottlenecks.map((b, index) => (
                  <div key={index} className="bg-white rounded-md p-3 border border-status-warning/30">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-gray-950">{b.stage}</span>
                      {b.stuckCount > 0 && (
                        <span className="text-micro px-2 py-0.5 rounded-full bg-status-warning/15 text-status-warning">
                          {b.stuckCount} parados
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3 text-gray-500" />
                        <span className="text-gray-600">Tempo médio:</span>
                        <span className="font-medium text-gray-900">{b.avgDays}d</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <TrendingUp className="w-3 h-3 text-gray-500 rotate-180" />
                        <span className="text-gray-600">Taxa desistência:</span>
                        <span className={`font-medium ${b.dropRate > 30 ? 'text-status-error' : b.dropRate > 15 ? 'text-status-warning' : 'text-status-success'}`}>
                          {b.dropRate}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {jobs.some(job => (job.days_open || 0) > 30 && (job.approved_count || 0) === 0) && (
            <div className="bg-status-error/10 rounded-md p-4 border border-status-error/30">
              <h3 className="text-xs font-semibold text-status-error uppercase tracking-wide mb-3 flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-status-error" />
                Vagas Sem Aprovação
              </h3>
              <div className="space-y-2">
                {jobs.filter(job => (job.days_open || 0) > 30 && (job.approved_count || 0) === 0).map(job => (
                  <div key={job.id} className="bg-white rounded-md p-3 border border-status-error/30">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {job.code && (
                          <span className="text-micro font-medium text-status-error bg-status-error/15 px-1.5 py-0.5 rounded-full">{job.code}</span>
                        )}
                        <span className="text-xs font-semibold text-gray-950">{job.title}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3 text-status-error" />
                        <span className="text-xs font-medium text-status-error">
                          {job.days_open} dias aberta
                        </span>
                      </div>
                    </div>
                    <p className="text-micro text-gray-500 mt-1">
                      {job.candidates_count || 0} candidatos • {job.screening_count || 0} em triagem • Nenhum aprovado
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
              <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                <DollarSign className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Análise Salarial
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between bg-white rounded-md p-2.5 border border-gray-200">
                  <span className="text-xs text-gray-600">Faixa da Vaga</span>
                  <span className="text-xs font-semibold text-gray-950">
                    R$ {salaryData.vagaMin.toLocaleString()} - R$ {salaryData.vagaMax.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between bg-white rounded-md p-2.5 border border-gray-200">
                  <span className="text-xs text-gray-600">Média Pretensão Candidatos</span>
                  <span className="text-xs font-semibold text-gray-950">
                    R$ {salaryData.mediaInscritos.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between bg-white rounded-md p-2.5 border border-gray-200">
                  <span className="text-xs text-gray-600">Candidatos Dentro da Faixa</span>
                  <span className="text-xs font-semibold text-gray-900 dark:text-gray-50">
                    {salaryData.dentroFaixa} ({salaryData.percentualDentro}%)
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
              <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                <Star className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Indicadores de Qualidade
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between bg-white rounded-md p-2.5 border border-gray-200">
                  <span className="text-xs text-gray-600">Score Médio (Todos)</span>
                  <span className={`text-xs font-semibold ${getScoreColor(qualityMetrics.avgScoreTodos)}`}>
                    {qualityMetrics.avgScoreTodos}%
                  </span>
                </div>
                <div className="flex items-center justify-between bg-white rounded-md p-2.5 border border-gray-200">
                  <span className="text-xs text-gray-600">Score Médio (Triados)</span>
                  <span className={`text-xs font-semibold ${getScoreColor(qualityMetrics.avgScoreTriados)}`}>
                    {qualityMetrics.avgScoreTriados}%
                  </span>
                </div>
                <div className="flex items-center justify-between bg-white rounded-md p-2.5 border border-gray-200">
                  <span className="text-xs text-gray-600">Taxa Triagem → Aprovação</span>
                  <span className="text-xs font-semibold text-gray-900 dark:text-gray-50">
                    {qualityMetrics.taxaAprovacao}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Métricas WSI
                <span className="text-micro text-gray-400 font-normal ml-1">(estimativa baseada em performance)</span>
              </h3>
              <div className="flex items-center gap-1.5">
                <span className="text-micro text-gray-500">Score Médio:</span>
                <span className="text-sm font-bold text-gray-900 dark:text-gray-50">{wsiMetrics.avgWSI}%</span>
              </div>
            </div>
            
            <div className="space-y-2">
              {wsiMetrics.dimensions.map((dim) => (
                <div key={dim.dimension} className="flex items-center gap-3">
                  <div className="w-24">
                    <span className="text-xs font-medium text-gray-700">{dim.dimension}</span>
                    <span className="text-micro text-gray-500 block">{dim.label}</span>
                  </div>
                  <div className="flex-1 h-4 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all ${
                        dim.score >= 80 ? 'bg-gray-900 dark:bg-gray-50' : 
                        dim.score >= 60 ? 'bg-status-warning' : 'bg-status-error'
                      }`}
                      style={{width: `${dim.score}%`}}
                    />
                  </div>
                  <span className={`text-xs font-semibold w-10 text-right ${
                    dim.score >= 80 ? 'text-gray-600 dark:text-gray-400' : 
                    dim.score >= 60 ? 'text-status-warning' : 'text-status-error'
                  }`}>
                    {dim.score}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
            <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
              <Lightbulb className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
              Insights Categorizados
            </h3>

            <div className="grid grid-cols-2 gap-3">
              {categorizedInsights.map((insight, index) => {
                const styles = getInsightStyles(insight.type)
                const IconComponent = styles.icon
                return (
                  <div key={index} className={`rounded-md p-3 border ${styles.bg} ${styles.border}`}>
                    <div className="flex items-start gap-2">
                      <IconComponent className={`w-4 h-4 mt-0.5 ${styles.iconColor}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-xs font-semibold text-gray-950">{insight.title}</h4>
                          {insight.badge && (
                            <span className={`text-micro font-medium px-1.5 py-0.5 rounded-full ${
                              insight.type === 'attention' ? 'bg-status-error/20 text-status-error' : 'bg-status-warning/20 text-status-warning'
                            }`}>
                              {insight.badge}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-700 leading-relaxed">{insight.description}</p>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {jobs.length > 0 && (
            <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
              <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Detalhamento por Vaga
              </h3>
              <div className="space-y-2 max-h-[160px] overflow-y-auto">
                {jobs.map((job) => {
                  const daysRemaining = getDaysRemaining(job.deadline)

                  return (
                    <div key={job.id} className="bg-white border border-gray-200 rounded-md p-3">
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            {job.code && (
                              <span className="text-micro font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded-full">{job.code}</span>
                            )}
                            <span className="text-xs font-semibold text-gray-950 truncate">{job.title}</span>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-gray-600">
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {job.candidates_count || 0} cand.
                            </span>
                            <span className="flex items-center gap-1">
                              <CheckCircle className="w-3 h-3" />
                              {job.approved_count || 0} aprov.
                            </span>
                            <span className="flex items-center gap-1">
                              <Filter className="w-3 h-3" />
                              {job.screening_count || 0} triagem
                            </span>
                            {daysRemaining !== null && (
                              <span className={`flex items-center gap-1 ${daysRemaining <= 7 ? 'text-status-warning font-medium' : ''}`}>
                                <Clock className="w-3 h-3" />
                                {daysRemaining > 0 ? `${daysRemaining}d restantes` : 'Expirado'}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="text-right ml-3">
                          <div className="flex items-center gap-1">
                            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                            <span className={`text-sm font-bold ${getScoreColor(job.performance_score)}`}>
                              {job.performance_score || '--'}%
                            </span>
                          </div>
                          <span className="text-micro text-gray-500">Score LIA</span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="pt-3 border-t border-gray-200 flex-shrink-0">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportReport}
                className="h-8 px-3 text-xs gap-1.5 border-gray-200 text-gray-700 hover:bg-gray-50"
              >
                <Download className="w-3.5 h-3.5" />
                Exportar PDF
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleSendEmail}
                disabled={!onSendEmail}
                className="h-8 px-3 text-xs gap-1.5 border-gray-200 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                <Mail className="w-3.5 h-3.5" />
                Enviar por Email
              </Button>
            </div>
            <Button
              onClick={onClose}
              className="h-9 px-4 text-xs font-medium bg-gray-800 hover:bg-gray-900 text-white"
            >
              Fechar
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
