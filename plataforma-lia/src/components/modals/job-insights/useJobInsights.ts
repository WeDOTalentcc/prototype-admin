import { useMemo, useCallback } from "react"
import { getJobScoreClass } from "@/lib/score-utils"
import type {
  JobInsightData,
  CandidateDemographics,
  ConversionRate,
  StageBottleneck,
  InsightCategory,
  DemographicDistribution,
  WSIScore,
} from "./job-insights.types"
import { TREND_WEEKS } from "./job-insights.constants"

interface UseJobInsightsProps {
  jobs: JobInsightData[]
  aggregatedDemographics?: CandidateDemographics
  conversionRates?: ConversionRate[]
  bottlenecks?: StageBottleneck[]
  insights?: InsightCategory[]
  onSendEmail?: (reportData: { jobIds: string[]; reportHtml: string }) => void
}

export function useJobInsights({
  jobs,
  aggregatedDemographics,
  conversionRates,
  bottlenecks,
  insights,
  onSendEmail,
}: UseJobInsightsProps) {
  // ── aggregate pipeline metrics ──────────────────────────────────────────
  const aggregateMetrics = useMemo(() => {
    const totalCandidates = jobs.reduce((sum, job) => sum + (job.candidates_count || 0), 0)
    const totalApproved = jobs.reduce((sum, job) => sum + (job.approved_count || 0), 0)
    const totalScreening = jobs.reduce((sum, job) => sum + (job.screening_count || 0), 0)
    const totalRejected = jobs.reduce((sum, job) => sum + (job.rejected_count || 0), 0)
    const avgTimePerStage =
      jobs.reduce((sum, job) => sum + (job.avg_time_per_stage || 0), 0) / (jobs.length || 1)
    const conversionRate =
      totalCandidates > 0 ? ((totalApproved / totalCandidates) * 100).toFixed(1) : "0"
    const screeningConversionRate =
      totalScreening > 0 ? ((totalApproved / totalScreening) * 100).toFixed(1) : "0"

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

  // ── recruitment funnel bars ─────────────────────────────────────────────
  const funnelData = useMemo(() => {
    const stages = [
      { name: "Inscritos", value: aggregateMetrics.totalCandidates, color: "bg-lia-interactive-active" },
      { name: "Em Triagem", value: aggregateMetrics.totalScreening, color: "bg-lia-interactive-active" },
      { name: "Aprovados", value: aggregateMetrics.totalApproved, color: "bg-lia-interactive-active" },
      { name: "Contratados", value: Math.round(aggregateMetrics.totalApproved * 0.3), color: "bg-lia-btn-primary-bg" },
    ]
    const maxValue = Math.max(...stages.map((s) => s.value), 1)
    return stages.map((stage) => ({
      ...stage,
      percentage: Math.round((stage.value / maxValue) * 100),
      rate:
        aggregateMetrics.totalCandidates > 0
          ? ((stage.value / aggregateMetrics.totalCandidates) * 100).toFixed(1)
          : "0",
    }))
  }, [aggregateMetrics])

  // ── demographics aggregation ────────────────────────────────────────────
  const demographicData = useMemo(() => {
    if (aggregatedDemographics) {
      return {
        cities: aggregatedDemographics.cities || [],
        workModels: aggregatedDemographics.workModels || [],
        genders: aggregatedDemographics.genders || [],
        ageRanges: aggregatedDemographics.ageRanges || [],
        educationLevels: aggregatedDemographics.educationLevels || [],
        experienceYears: aggregatedDemographics.experienceYears || [],
      }
    }

    const cityMap = new Map<string, number>()
    const workModelMap = new Map<string, number>()
    const genderMap = new Map<string, number>()
    const ageRangeMap = new Map<string, number>()
    const educationLevelMap = new Map<string, number>()
    const experienceYearsMap = new Map<string, number>()
    let totalWithDemographics = 0

    jobs.forEach((job) => {
      if (job.candidate_demographics) {
        totalWithDemographics++
        job.candidate_demographics.cities?.forEach((c) =>
          cityMap.set(c.name, (cityMap.get(c.name) || 0) + c.count)
        )
        job.candidate_demographics.workModels?.forEach((w) =>
          workModelMap.set(w.name, (workModelMap.get(w.name) || 0) + w.count)
        )
        job.candidate_demographics.genders?.forEach((g) =>
          genderMap.set(g.name, (genderMap.get(g.name) || 0) + g.count)
        )
        job.candidate_demographics.ageRanges?.forEach((a) =>
          ageRangeMap.set(a.name, (ageRangeMap.get(a.name) || 0) + a.count)
        )
        job.candidate_demographics.educationLevels?.forEach((e) =>
          educationLevelMap.set(e.name, (educationLevelMap.get(e.name) || 0) + e.count)
        )
        job.candidate_demographics.experienceYears?.forEach((e) =>
          experienceYearsMap.set(e.name, (experienceYearsMap.get(e.name) || 0) + e.count)
        )
      }
    })

    if (totalWithDemographics === 0) {
      return { cities: [], workModels: [], genders: [], ageRanges: [], educationLevels: [], experienceYears: [] }
    }

    const toArray = (map: Map<string, number>): DemographicDistribution[] => {
      const total = Array.from(map.values()).reduce((s, c) => s + c, 0)
      return Array.from(map.entries())
        .map(([name, count]) => ({
          name,
          count,
          percentage: total > 0 ? Math.round((count / total) * 100) : 0,
        }))
        .sort((a, b) => b.count - a.count)
    }

    return {
      cities: toArray(cityMap),
      workModels: toArray(workModelMap),
      genders: toArray(genderMap),
      ageRanges: toArray(ageRangeMap),
      educationLevels: toArray(educationLevelMap),
      experienceYears: toArray(experienceYearsMap),
    }
  }, [jobs, aggregatedDemographics])

  // ── salary analysis ─────────────────────────────────────────────────────
  const salaryData = useMemo(() => {
    const avgJobMin = jobs.reduce((sum, j) => sum + (j.salary_min || 5000), 0) / (jobs.length || 1)
    const avgJobMax = jobs.reduce((sum, j) => sum + (j.salary_max || 8000), 0) / (jobs.length || 1)
    const avgCandidateExpectation = ((avgJobMin + avgJobMax) / 2) * 0.95
    return {
      vagaMin: Math.round(avgJobMin),
      vagaMax: Math.round(avgJobMax),
      mediaInscritos: Math.round(avgCandidateExpectation),
      dentroFaixa: Math.round(aggregateMetrics.totalCandidates * 0.68),
      percentualDentro: 68,
    }
  }, [jobs, aggregateMetrics])

  // ── quality metrics ─────────────────────────────────────────────────────
  const qualityMetrics = useMemo(() => {
    const avgPerformance =
      jobs.reduce((sum, j) => sum + (j.performance_score || 0), 0) / (jobs.length || 1)
    return {
      avgScoreTodos: Math.round(avgPerformance * 0.75),
      avgScoreTriados: Math.round(avgPerformance * 0.92),
      avgScoreAprovados: Math.round(avgPerformance),
      taxaTriagem:
        aggregateMetrics.totalCandidates > 0
          ? ((aggregateMetrics.totalScreening / aggregateMetrics.totalCandidates) * 100).toFixed(1)
          : "0",
      taxaAprovacao:
        aggregateMetrics.totalScreening > 0
          ? ((aggregateMetrics.totalApproved / aggregateMetrics.totalScreening) * 100).toFixed(1)
          : "0",
    }
  }, [jobs, aggregateMetrics])

  // ── WSI dimensions ──────────────────────────────────────────────────────
  const wsiMetrics = useMemo(() => {
    const avg =
      jobs.reduce((sum, j) => sum + (j.performance_score || 0), 0) / (jobs.length || 1)
    const dimensions: WSIScore[] = [
      { dimension: "Técnico", score: Math.round(avg * 0.95), label: "Competências técnicas" },
      { dimension: "Comportamental", score: Math.round(avg * 0.88), label: "Comp. Comportamentais e atitudes" },
      { dimension: "Cultural", score: Math.round(avg * 0.92), label: "Fit cultural" },
      { dimension: "Experiência", score: Math.round(avg * 0.85), label: "Anos e relevância" },
      { dimension: "Potencial", score: Math.round(avg * 0.78), label: "Capacidade de crescimento" },
    ]
    const avgWSI = Math.round(
      dimensions.reduce((s, d) => s + d.score, 0) / dimensions.length
    )
    return { dimensions, avgWSI }
  }, [jobs])

  // ── LIA funnel ──────────────────────────────────────────────────────────
  const liaFunnelMetrics = useMemo(() => {
    const hasRealLiaData = jobs.some((j) => j.lia_metrics && j.lia_metrics.pipeline_lia > 0)
    if (hasRealLiaData) {
      return jobs.reduce(
        (acc, job) => {
          const lm = job.lia_metrics
          if (lm) {
            acc.pipeline_lia += lm.pipeline_lia || 0
            acc.triagens_agendadas += lm.triagens_agendadas || 0
            acc.triagens_realizadas += lm.triagens_realizadas || 0
            acc.sem_resposta += lm.sem_resposta || 0
            acc.entrevistas_agendadas += lm.entrevistas_agendadas || 0
          }
          return acc
        },
        {
          pipeline_lia: 0,
          triagens_agendadas: 0,
          triagens_realizadas: 0,
          sem_resposta: 0,
          entrevistas_agendadas: 0,
          isEstimated: false,
        }
      )
    }
    return {
      pipeline_lia: Math.round(aggregateMetrics.totalCandidates * 0.6),
      triagens_agendadas: Math.round(aggregateMetrics.totalScreening * 0.8),
      triagens_realizadas: Math.round(aggregateMetrics.totalScreening * 0.65),
      sem_resposta: Math.round(aggregateMetrics.totalScreening * 0.15),
      entrevistas_agendadas: Math.round(aggregateMetrics.totalApproved * 0.9),
      isEstimated: true,
    }
  }, [jobs, aggregateMetrics])

  // ── conversion rates (calculated or provided) ───────────────────────────
  const calculatedConversionRates = useMemo((): ConversionRate[] => {
    if (conversionRates && conversionRates.length > 0) return conversionRates
    const stages = [
      { from: "Funil IA", to: "Triagens Agendadas", fromValue: liaFunnelMetrics.pipeline_lia, toValue: liaFunnelMetrics.triagens_agendadas },
      { from: "Triagens Agendadas", to: "Triagens Realizadas", fromValue: liaFunnelMetrics.triagens_agendadas, toValue: liaFunnelMetrics.triagens_realizadas },
      { from: "Triagens Realizadas", to: "Entrevistas Agendadas", fromValue: liaFunnelMetrics.triagens_realizadas, toValue: liaFunnelMetrics.entrevistas_agendadas },
      { from: "Inscritos", to: "Aprovados", fromValue: aggregateMetrics.totalCandidates, toValue: aggregateMetrics.totalApproved },
    ]
    return stages.map((s) => {
      const rate = s.fromValue > 0 ? (s.toValue / s.fromValue) * 100 : 0
      const status: ConversionRate["status"] = rate < 20 ? "critical" : rate < 50 ? "warning" : "good"
      return { from: s.from, to: s.to, rate: Math.round(rate * 10) / 10, status }
    })
  }, [conversionRates, liaFunnelMetrics, aggregateMetrics])

  // ── categorized insights ────────────────────────────────────────────────
  const categorizedInsights = useMemo((): InsightCategory[] => {
    if (insights && insights.length > 0) return insights
    const generated: InsightCategory[] = []

    if (parseFloat(qualityMetrics.taxaAprovacao) < 30)
      generated.push({ type: "action", title: "Revisar Critérios de Triagem", description: `Taxa de aprovação de ${qualityMetrics.taxaAprovacao}% está abaixo do esperado.`, badge: "Urgente" })

    if (aggregateMetrics.avgTimePerStage > 5)
      generated.push({ type: "action", title: "Acelerar Processo Seletivo", description: `Tempo médio de ${aggregateMetrics.avgTimePerStage} dias por etapa. Candidatos podem estar desistindo.` })

    const conversionAnalysis = parseFloat(aggregateMetrics.conversionRate)
    if (conversionAnalysis > 0)
      generated.push({ type: "analysis", title: "Performance do Funil", description: `Taxa de conversão de ${conversionAnalysis}% com ${aggregateMetrics.totalApproved} aprovados de ${aggregateMetrics.totalCandidates} candidatos.` })

    if (jobs.length > 1) {
      const avgScore = jobs.reduce((sum, j) => sum + (j.performance_score || 0), 0) / jobs.length
      generated.push({ type: "comparison", title: "Comparativo entre Vagas", description: `Nota média de ${Math.round(avgScore)}% entre as ${jobs.length} vagas selecionadas.` })
    }

    const lowScoreJobs = jobs.filter((j) => (j.performance_score || 0) < 60)
    if (lowScoreJobs.length > 0)
      generated.push({ type: "attention", title: "Vagas com Baixa Performance", description: `${lowScoreJobs.length} vaga(s) com nota abaixo de 60% requerem atenção imediata.`, badge: "Crítico" })

    if (liaFunnelMetrics.sem_resposta > liaFunnelMetrics.triagens_realizadas * 0.3)
      generated.push({ type: "attention", title: "Alto Índice de Não Resposta", description: `${liaFunnelMetrics.sem_resposta} candidatos sem resposta. Considere revisar horários de contato.` })

    if (generated.length === 0)
      generated.push({ type: "analysis", title: "Processo Saudável", description: "Todas as métricas estão dentro dos parâmetros esperados. Continue monitorando." })

    return generated
  }, [insights, qualityMetrics, aggregateMetrics, jobs, liaFunnelMetrics])

  // ── LIA textual analysis ────────────────────────────────────────────────
  const liaTextualAnalysis = useMemo(() => {
    const totalJobs = jobs.length
    const totalCandidates = aggregateMetrics.totalCandidates
    const avgConversion = parseFloat(aggregateMetrics.conversionRate)
    const avgPerformance = jobs.reduce((sum, j) => sum + (j.performance_score || 0), 0) / (jobs.length || 1)
    const topJob = jobs.reduce((top, job) => ((job.candidates_count || 0) > (top?.candidates_count || 0) ? job : top), jobs[0])
    const avgDaysOpen = jobs.reduce((sum, j) => sum + (j.days_open || 0), 0) / (jobs.length || 1)

    const summary = `Analisando ${totalJobs} vaga${totalJobs > 1 ? "s" : ""} com total de ${totalCandidates} candidatos.`
    const performance = avgPerformance >= 80 ? "Performance excelente detectada." : avgPerformance >= 60 ? "Performance dentro da média esperada." : "Performance abaixo do esperado, considere revisar critérios."
    const volumeInsight = topJob && totalJobs > 1 ? `"${topJob.title}" lidera com ${topJob.candidates_count || 0} candidatos.` : ""
    const conversionNote = avgConversion < 10 ? "Taxa de conversão baixa (< 10%) - revisar critérios de triagem." : avgConversion >= 30 ? "Taxa de conversão saudável acima de 30%." : ""

    return { summary, performance, volumeInsight, conversionNote, avgDaysOpen: Math.round(avgDaysOpen) }
  }, [jobs, aggregateMetrics])

  // ── trend chart data ────────────────────────────────────────────────────
  const trendData = useMemo(() => {
    const totalBase = Math.max(aggregateMetrics.totalCandidates, 10)
    const candidatesTrend = [0.25, 0.5, 0.75, 1].map((f) => Math.round(totalBase * f))
    const conversionBase = parseFloat(aggregateMetrics.conversionRate)
    const conversionTrend = [12, conversionBase * 0.7, conversionBase * 0.9, conversionBase].map((v) => Math.round(v))
    return {
      weeks: TREND_WEEKS,
      candidatesTrend,
      conversionTrend,
      maxCandidates: Math.max(...candidatesTrend),
    }
  }, [aggregateMetrics])

  // ── helpers ─────────────────────────────────────────────────────────────
  const getDaysRemaining = useCallback((deadline?: string) => {
    if (!deadline) return null
    const diffTime = new Date(deadline).getTime() - new Date().getTime()
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  }, [])

  const getScoreColor = useCallback((score?: number) => {
    if (!score) return "text-lia-text-tertiary"
    return getJobScoreClass(score)
  }, [])

  const generateAttentionPoints = useCallback(() => {
    const points: string[] = []
    const lowScore = jobs.filter((j) => (j.performance_score || 0) < 70)
    if (lowScore.length) points.push(`${lowScore.length} vaga(s) com nota abaixo de 70%`)
    const urgent = jobs.filter((j) => { const d = getDaysRemaining(j.deadline); return d !== null && d <= 7 })
    if (urgent.length) points.push(`${urgent.length} vaga(s) com prazo em até 7 dias`)
    const lowCand = jobs.filter((j) => (j.candidates_count || 0) < 5)
    if (lowCand.length) points.push(`${lowCand.length} vaga(s) com menos de 5 candidatos`)
    const highRej = jobs.filter((j) => { const t = j.candidates_count || 0; return t > 0 && (j.rejected_count || 0) / t > 0.5 })
    if (highRej.length) points.push(`${highRej.length} vaga(s) com rejeição > 50%`)
    if (parseFloat(qualityMetrics.taxaAprovacao) < 20) points.push("Taxa de conversão de triagem abaixo de 20%")
    if (salaryData.percentualDentro < 50) points.push("Menos de 50% dos candidatos dentro da faixa salarial")
    if (!points.length) points.push("Todas as vagas estão dentro dos parâmetros esperados")
    return points
  }, [jobs, getDaysRemaining, qualityMetrics, salaryData])

  const generateRecommendations = useCallback(() => {
    const recs: string[] = []
    if (parseFloat(aggregateMetrics.conversionRate) < 20) recs.push("Revisar critérios de triagem para aumentar taxa de conversão")
    if (aggregateMetrics.avgTimePerStage > 5) recs.push("Otimizar tempo médio por etapa focando em gargalos")
    const highPrioLow = jobs.filter((j) => j.priority?.toLowerCase() === "alta" && (j.approved_count || 0) < 3)
    if (highPrioLow.length) recs.push("Priorizar sourcing ativo para vagas de alta prioridade")
    if (aggregateMetrics.totalScreening > aggregateMetrics.totalApproved * 3) recs.push("Considerar calibração de perfil com gestores")
    if (salaryData.mediaInscritos > salaryData.vagaMax) recs.push("Revisar faixa salarial - candidatos têm expectativas acima do oferecido")
    if (qualityMetrics.avgScoreTodos < 60) recs.push("Ajustar divulgação para atrair candidatos mais qualificados")
    if (!recs.length) { recs.push("Manter ritmo atual de execução"); recs.push("Acompanhar métricas semanalmente") }
    return recs
  }, [aggregateMetrics, jobs, salaryData, qualityMetrics])

  // ── report handlers ─────────────────────────────────────────────────────
  const handleExportReport = useCallback(() => {
    const printContent = document.getElementById("insights-report-content")
    if (!printContent) return
    const printWindow = window.open("", "_blank")
    if (!printWindow) return
    const reportDate = new Date().toLocaleDateString("pt-BR")
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Relatório de Insights - ${reportDate}</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 40px; color: #1a1a1a; }
          h1 { font-size: 24px; margin-bottom: 8px; }
          h2 { font-size: 18px; color: #374151; margin-top: 24px; }
          .subtitle { color: #6b7280; font-size: 14px; margin-bottom: 24px; }
          .metric-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin: 16px 0; }
          .metric-card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; }
          .metric-label { font-size: 12px; color: #6b7280; }
          .metric-value { font-size: 20px; font-weight: 600; }
          .section { margin: 24px 0; padding: 16px; border: 1px solid #e5e7eb; border-radius: 8px; }
          .job-item { padding: 12px; border-bottom: 1px solid #e5e7eb; }
          .job-item:last-child { border-bottom: none; }
          @media print { body { padding: 20px; } }
        </style>
      </head>
      <body>
        <h1>Relatório de Insights</h1>
        <p class="subtitle">${jobs.length} vaga(s) selecionada(s) • Gerado em ${reportDate}</p>
        <div class="metric-grid">
          <div class="metric-card"><div class="metric-label">Total de Candidatos</div><div class="metric-value">${aggregateMetrics.totalCandidates}</div></div>
          <div class="metric-card"><div class="metric-label">Aprovados</div><div class="metric-value">${aggregateMetrics.totalApproved}</div></div>
          <div class="metric-card"><div class="metric-label">Em Triagem</div><div class="metric-value">${aggregateMetrics.totalScreening}</div></div>
          <div class="metric-card"><div class="metric-label">Taxa de Conversão</div><div class="metric-value">${aggregateMetrics.conversionRate}%</div></div>
        </div>
        <h2>Vagas Analisadas</h2>
        <div class="section">
          ${jobs.map((job) => `<div class="job-item"><strong>${job.code || ""} ${job.title}</strong><div style="font-size:12px;color:#6b7280;">${job.candidates_count || 0} candidatos • ${job.approved_count || 0} aprovados • Nota: ${job.performance_score || "--"}%</div></div>`).join("")}
        </div>
        <p style="font-size:12px;color:#9ca3af;margin-top:32px;">Gerado pelo WeDoTalent</p>
      </body>
      </html>
    `)
    printWindow.document.close()
    printWindow.print()
  }, [jobs, aggregateMetrics])

  const handleSendEmail = useCallback(() => {
    if (!onSendEmail) return
    const reportDate = new Date().toLocaleDateString("pt-BR")
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
    onSendEmail({ jobIds: jobs.map((j) => j.id), reportHtml })
  }, [jobs, aggregateMetrics, onSendEmail])

  return {
    aggregateMetrics,
    funnelData,
    demographicData,
    salaryData,
    qualityMetrics,
    wsiMetrics,
    liaFunnelMetrics,
    calculatedConversionRates,
    categorizedInsights,
    liaTextualAnalysis,
    trendData,
    getDaysRemaining,
    getScoreColor,
    generateAttentionPoints,
    generateRecommendations,
    handleExportReport,
    handleSendEmail,
  }
}
