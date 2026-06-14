"use client"

import { formatBRL, CURRENCY_SYMBOL } from"@/lib/pricing"

import React, { useState, useRef, useEffect, useCallback } from"react"
import { useJobReport } from"@/hooks/jobs/use-job-report"
import { useMLPredictions } from"@/hooks/ai/use-ml-predictions"
import { useAuthStore } from"@/stores/auth-store"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Progress } from"@/components/ui/progress"
import {
  X, Download, Share2, Printer, Mail, FileText, Users,
  TrendingUp, Clock, Calendar, DollarSign, Target, CheckCircle,
  Brain, Briefcase, MapPin, BarChart3, PieChart, Activity,
  AlertCircle, Award, Star, MessageSquare, Eye, ChevronRight,
  ArrowUp, ArrowDown, Building, User, Phone, Shield, Globe,
  Zap, Filter, Hash, Layers3, Settings, Copy, Maximize2,
  Trophy, Lightbulb
} from"lucide-react"

interface JobReportJob {
  jobId?: string
  title?: string
  department?: string
  location?: string
  seniority?: string
  workModel?: string
  openDate?: string
  stage?: string
  [key: string]: unknown
}

interface JobReportModalProps {
  job: JobReportJob
  isOpen: boolean
  onClose: () => void
}

export function JobReportModal({ job, isOpen, onClose }: JobReportModalProps) {
  const reportRef = useRef<HTMLDivElement>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedSections, setSelectedSections] = useState({
    overview: true,
    funnel: true,
    candidates: true,
    timeline: true,
    costs: true,
    performance: true,
    recommendations: true
  })
  const { data: reportApiData, loading: reportLoading, fetch: fetchReport } = useJobReport()
  const { timeToFill, salary, loading: mlLoading, fetchTimeToFill, fetchSalary } = useMLPredictions()
  const user = useAuthStore((s) => s.user)

  useEffect(() => {
    if (isOpen && job?.jobId) {
      fetchReport(job.jobId ??"")
      const companyId = (user &&"company_id" in user ? user.company_id : undefined) ||"default"
      const jobData = {
        title: job.title,
        department: job.department,
        location: job.location,
        seniority: job.seniority,
        work_model: job.workModel,
      }
      fetchTimeToFill(companyId, jobData)
      fetchSalary(companyId, jobData)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, job?.jobId, fetchReport, fetchTimeToFill, fetchSalary, user])

  if (!isOpen) return null

  // Dados reais do backend mesclados com fallback para campos sem cobertura de DB
  const funnelMetrics = reportApiData
    ? {
        totalCandidates: reportApiData.funnel_metrics.total_candidates,
        screening: reportApiData.funnel_metrics.screening,
        interview: reportApiData.funnel_metrics.interview,
        final: reportApiData.funnel_metrics.final,
        hired: reportApiData.funnel_metrics.hired,
        conversionRate: reportApiData.funnel_metrics.conversion_rate,
        averageTimeToHire: reportApiData.funnel_metrics.avg_time_to_hire,
        costPerHire: reportApiData.funnel_metrics.cost_per_hire,
      }
    : {
        totalCandidates: 0, screening: 0, interview: 0, final: 0,
        hired: 0, conversionRate: 0, averageTimeToHire: 0, costPerHire: 0,
      }

  const channelPerformance = reportApiData?.channel_performance.map(c => ({
    channel: c.channel,
    candidates: c.candidates,
    quality: 0,
    hired: c.hired,
    cost: 0,
  })) ?? []

  const topCandidates = reportApiData?.top_candidates.map(c => ({
    name: c.name,
    score: Math.round(c.score),
    status: c.status,
    fit: Math.round(c.score * 0.95),
  })) ?? []

  const reportData = {
    generatedDate: new Date().toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    }),
    generatedTime: new Date().toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    }),
    funnelMetrics,
    channelPerformance,
    timeline: (() => {
      const openDate = job.openDate ? new Date(job.openDate) : new Date()
      const fmt = (d: Date) => d.toLocaleDateString("pt-BR", { day:"2-digit", month:"2-digit" })
      const addDays = (d: Date, n: number) => new Date(d.getTime() + n * 86400000)
      const now = new Date()
      const daysOpen = Math.floor((now.getTime() - openDate.getTime()) / 86400000)
      const predictedDays = timeToFill?.predicted_days || 30
      const predictedEnd = addDays(openDate, predictedDays)

      const events = [
        { date: fmt(openDate), event:"Vaga publicada", status:"completed" as const },
        { date: fmt(addDays(openDate, Math.min(3, daysOpen))), event:"Primeira triagem LIA", status: daysOpen >= 3 ?"completed" as const :"pending" as const },
        { date: fmt(addDays(openDate, Math.min(7, daysOpen))), event:"Início das entrevistas", status: daysOpen >= 7 ?"completed" as const : daysOpen >= 3 ?"in-progress" as const :"pending" as const },
        { date: fmt(addDays(openDate, Math.round(predictedDays * 0.6))), event:"Testes técnicos", status: daysOpen >= predictedDays * 0.6 ?"completed" as const : daysOpen >= 7 ?"in-progress" as const :"pending" as const },
        { date: fmt(addDays(openDate, Math.round(predictedDays * 0.85))), event:"Decisão final", status: daysOpen >= predictedDays * 0.85 ?"completed" as const :"pending" as const },
        { date: fmt(predictedEnd), event: `Contratação prevista (${predictedDays}d)`, status:"pending" as const },
      ]
      return events
    })(),
    topCandidates,
    budget: {
      total: 50000,
      spent: 18500,
      remaining: 31500,
      breakdown: [
        { category:"Divulgação", amount: 5200 },
        { category:"Plataformas", amount: 3800 },
        { category:"Testes", amount: 2400 },
        { category:"Equipe", amount: 4600 },
        { category:"LIA/Automação", amount: 2500 }
      ]
    },
    predictions: {
      timeToFill: timeToFill ? {
        predictedDays: timeToFill.predicted_days,
        rangeMin: timeToFill.range_min,
        rangeMax: timeToFill.range_max,
        confidence: timeToFill.confidence,
        confidenceLevel: timeToFill.confidence_level,
        comparisonToMarket: timeToFill.comparison_to_market,
        factors: timeToFill.factors,
      } : null,
      salary: salary ? {
        suggestedMin: salary.suggested_min,
        suggestedMax: salary.suggested_max,
        marketPercentile: salary.market_percentile,
        competitiveAnalysis: salary.competitive_analysis,
        confidence: salary.confidence,
        confidenceLevel: salary.confidence_level,
        factors: salary.factors,
      } : null,
    },
    qualityMetrics: {
      nps: 87,
      candidateSatisfaction: 4.6,
      hiringManagerSatisfaction: 4.8,
      timeToFillBenchmark: timeToFill?.comparison_to_market ||"Calculando...",
      marketPercentile: salary ? `P${salary.market_percentile}` :"--",
      qualityOfHireBenchmark: salary?.competitive_analysis ||"Calculando..."
    }
  }

  const generatePDF = async () => {
    if (!reportRef.current) return
    setIsGenerating(true)
    try {
      const [{ default: html2canvas }, { default: jsPDF }] = await Promise.all([
        import('html2canvas'),
        import('jspdf'),
      ])
      const canvas = await html2canvas(reportRef.current, {
        scale: 2,
        logging: false,
        windowWidth: 794,
        windowHeight: reportRef.current.scrollHeight
      })
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
      })
      const imgData = canvas.toDataURL('image/png')
      const imgWidth = 210
      const pageHeight = 297
      const imgHeight = (canvas.height * imgWidth) / canvas.width
      let heightLeft = imgHeight
      let position = 0
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
      while (heightLeft >= 0) {
        position = heightLeft - imgHeight
        pdf.addPage()
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
        heightLeft -= pageHeight
      }
      pdf.save(`Relatorio_Vaga_${job.jobId}_${new Date().getTime()}.pdf`)
    } catch (error) {
    } finally {
      setIsGenerating(false)
    }
  }

  const shareReport = () => {
    if (navigator.share) {
      navigator.share({
        title: `Relatório da Vaga ${job.title}`,
        text: `Relatório completo da vaga ${job.title} - ${job.jobId}`,
        url: window.location.href
      })
    }
  }

  const printReport = () => {
    window.print()
  }

  return (
    <div className="fixed inset-0 z-50 bg-lia-overlay backdrop-blur-sm flex items-start justify-center pt-4 pb-4 overflow-y-auto print:bg-lia-bg-primary print:backdrop-blur-none print:pt-0 print:pb-0">
      <div className="w-full max-w-[830px] bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl overflow-hidden flex flex-col my-auto print:max-w-none print:rounded-none print:shadow-none print:my-0">
        {/* Header - Alinhado com conteúdo A4 */}
        <div className="bg-lia-btn-primary-bg dark:bg-lia-bg-secondary text-white px-4 py-2 print:py-2 print:px-3 dark:border-lia-border-subtle">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 print:w-4 print:h-4" />
              <div>

                <h2 className="text-xs font-semibold print:text-xs">Relatório Executivo da Vaga</h2>
                <p className="text-micro text-white/80">{reportLoading ?"Carregando..." : String(job.title ||"")} • {String(job.jobId ||"")}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 print:hidden">
              <Button

                variant="secondary"
                size="sm"
                onClick={shareReport}
                className="h-7 px-2 text-micro bg-lia-bg-primary/20 hover:bg-lia-bg-primary/30 text-white"
              >
                <Share2 className="w-3 h-3 mr-1" />
                Compartilhar
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={printReport}
                className="h-7 px-2 text-micro bg-lia-bg-primary/20 hover:bg-lia-bg-primary/30 text-white"
              >
                <Printer className="w-3 h-3 mr-1" />
                Imprimir
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={generatePDF}
                disabled={isGenerating}
                className="h-7 px-2 text-micro bg-lia-bg-primary hover:bg-lia-bg-tertiary text-lia-text-primary"
              >
                {isGenerating ? (
                  <>Gerando...</>
                ) : (
                  <>
                    <Download className="w-3 h-3 mr-1" />
                    Exportar PDF
                  </>
                )}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-7 w-7 p-0 text-white hover:bg-lia-bg-primary/20"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Conteúdo - Otimizado para A4 (794px = 210mm) */}
        <div className="flex-1 overflow-y-auto bg-lia-bg-primary max-h-[calc(100vh-120px)] print:bg-lia-bg-primary print:max-h-none print:overflow-visible">
          <div 
            ref={reportRef} 
            className="w-full bg-lia-bg-primary p-4 print:p-3 space-y-3 print:space-y-2"
           
          >
            {/* Cabeçalho do Relatório */}
            <div className="flex items-center justify-between pb-2">
              <div>
                <h1 className="text-base font-semibold text-lia-text-primary">
                  {(job.title as React.ReactNode)}
                </h1>
                <div className="flex items-center gap-3 mt-0.5 text-micro text-lia-text-secondary">
                  <span className="flex items-center gap-0.5">
                    <Building className="w-3 h-3" />
                    {(job.department as React.ReactNode)}
                  </span>
                  <span className="flex items-center gap-0.5">
                    <MapPin className="w-3 h-3" />
                    {(job.location as React.ReactNode)}
                  </span>
                  <span className="flex items-center gap-0.5">

                    <Calendar className="w-3 h-3" />
                    Aberta há {Math.floor((new Date().getTime() - new Date(job.openDate ?? Date.now()).getTime()) / (1000 * 60 * 60 * 24))} dias
                  </span>
                </div>
              </div>
              <div className="text-right text-micro text-lia-text-secondary">
                <p>Gerado: {reportData.generatedDate}</p>
                <p>às {reportData.generatedTime}</p>
              </div>
            </div>

            {/* Resumo Executivo - Grid 4 colunas compacto */}
            {selectedSections.overview && (
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1">
                  <Briefcase className="w-3 h-3 text-lia-text-secondary" />
                  Resumo Executivo
                </h3>
                <div className="grid grid-cols-4 gap-2">
                  <div className="text-center p-2 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-default dark:border-lia-border-default">
                    <Users className="w-4 h-4 text-lia-text-secondary mx-auto mb-0.5" />
                    <p className="text-lg font-semibold text-lia-text-primary">{reportData.funnelMetrics.totalCandidates}</p>
                    <p className="text-micro text-lia-text-secondary">Total Candidatos</p>
                  </div>
                  <div className="text-center p-2 bg-status-success/10 rounded-xl border border-status-success/30">
                    <Target className="w-4 h-4 text-status-success mx-auto mb-0.5" />
                    <p className="text-lg font-semibold text-status-success">{reportData.funnelMetrics.hired}</p>
                    <p className="text-micro text-lia-text-secondary">Contratados</p>
                  </div>
                  <div className="text-center p-2 bg-wedo-purple/10 rounded-xl border border-wedo-purple/30">
                    <Clock className="w-4 h-4 text-wedo-purple mx-auto mb-0.5" />
                    <p className="text-lg font-semibold text-lia-text-secondary">{reportData.funnelMetrics.averageTimeToHire}</p>
                    <p className="text-micro text-lia-text-secondary">Dias p/ Contratar</p>
                  </div>
                  <div className="text-center p-2 bg-wedo-orange/10 rounded-xl border border-wedo-orange/30">
                    <DollarSign className="w-4 h-4 text-wedo-orange mx-auto mb-0.5" />
                    <p className="text-lg font-semibold text-wedo-orange-text">{formatBRL(reportData.funnelMetrics.costPerHire)}</p>
                    <p className="text-micro text-lia-text-secondary">Custo/Contratação</p>
                  </div>
                </div>
                <div className="p-2 bg-status-warning/10 rounded-xl border border-status-warning/30 flex items-start gap-2">
                  <AlertCircle className="w-3 h-3 text-status-warning mt-0.5 flex-shrink-0" />

                  <p className="text-micro text-lia-text-primary">
                    <span className="font-medium">Status:</span> Processo em fase de {job.stage?.toLowerCase() || 'entrevista'} com {reportData.funnelMetrics.interview} candidatos
                    em entrevista e {reportData.funnelMetrics.final} finalistas. Taxa de conversão: {reportData.funnelMetrics.conversionRate}% (mercado: 2.3%).
                  </p>
                </div>
              </div>
            )}

            {/* Grid 2 colunas: Funil + Performance */}
            <div className="grid grid-cols-2 gap-3">
              {/* Análise do Funil */}
              {selectedSections.funnel && (
                <div className="space-y-2">
                  <h3 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1">
                    <Filter className="w-3 h-3 text-lia-text-secondary" />
                    Análise do Funil
                  </h3>
                  <div className="space-y-1.5 p-2 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
                    {[
                      { stage:"Candidatos", value: reportData.funnelMetrics.totalCandidates, percentage: 100, color:"bg-lia-bg-inverse" },
                      { stage:"Triagem", value: reportData.funnelMetrics.screening, percentage: 57, color:"bg-status-warning" },
                      { stage:"Entrevista", value: reportData.funnelMetrics.interview, percentage: 22, color:"bg-wedo-orange" },
                      { stage:"Final", value: reportData.funnelMetrics.final, percentage: 8, color:"bg-wedo-purple" },
                      { stage:"Contratados", value: reportData.funnelMetrics.hired, percentage: 2, color:"bg-status-success" }
                    ].map((item, index) => (
                      <div key={item.stage} className="flex items-center gap-2">
                        <span className="w-16 text-micro text-lia-text-primary">{item.stage}</span>
                        <div className="flex-1 h-3 bg-lia-interactive-active rounded-full overflow-hidden">
                          <div className={`h-full ${item.color}`} style={{width: `${item.percentage}%`}}></div>
                        </div>
                        <span className="w-8 text-micro font-medium text-right">{item.value}</span>
                        <span className="w-8 text-micro text-lia-text-secondary text-right">{item.percentage}%</span>
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1 p-1.5 bg-status-success/10 rounded-xl border border-status-success/30 text-center">
                      <p className="text-micro text-lia-text-secondary">Conversão</p>
                      <p className="text-sm font-bold text-status-success">{reportData.funnelMetrics.conversionRate}%</p>
                    </div>
                    <div className="flex-1 p-1.5 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-default dark:border-lia-border-default text-center">
                      <p className="text-micro text-lia-text-secondary">Qualidade</p>
                      <div className="flex items-center justify-center gap-0.5 mt-0.5">
                        {[1,2,3,4].map((star) => (
                          <Star key={star} className="w-2.5 h-2.5 fill-yellow-400 text-status-warning" />
                        ))}
                        <Star className="w-2.5 h-2.5 text-lia-text-tertiary" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Performance por Canal */}
              {selectedSections.performance && (
                <div className="space-y-2">
                  <h3 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1">
                    <Globe className="w-3 h-3 text-lia-text-secondary" />
                    Performance por Canal
                  </h3>
                  <div className="overflow-hidden rounded-xl border border-lia-border-subtle">
                    <table className="w-full text-micro">
                      <thead className="bg-lia-bg-secondary">
                        <tr>
                          <th className="text-left py-1 px-1.5 font-medium text-lia-text-primary">Canal</th>
                          <th className="text-center py-1 px-1 font-medium text-lia-text-primary">Cand.</th>
                          <th className="text-center py-1 px-1 font-medium text-lia-text-primary">Qual.</th>
                          <th className="text-center py-1 px-1 font-medium text-lia-text-primary">Cont.</th>
                          <th className="text-right py-1 px-1.5 font-medium text-lia-text-primary">Custo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reportData.channelPerformance.map((channel) => (
                          <tr key={channel.channel} className="border-t border-lia-border-subtle">
                            <td className="py-1 px-1.5">
                              <div className="flex items-center gap-1">
                                {channel.channel ==="LinkedIn" && <Briefcase className="w-2.5 h-2.5 text-lia-text-secondary" />}
                                {channel.channel ==="Website" && <Globe className="w-2.5 h-2.5 text-status-success" />}
                                {channel.channel ==="LIA Database" && <Brain className="w-2.5 h-2.5 text-wedo-cyan-text" />}
                                {channel.channel ==="Referral" && <Users className="w-2.5 h-2.5 text-wedo-orange-text" />}
                                <span>{channel.channel}</span>
                              </div>
                            </td>
                            <td className="text-center py-1 px-1 font-medium">{channel.candidates}</td>
                            <td className="text-center py-1 px-1">
                              <span className={`${channel.quality >= 90 ? 'text-status-success' : channel.quality >= 80 ? 'text-lia-text-secondary' : 'text-lia-text-secondary'}`}>
                                {channel.quality}%
                              </span>
                            </td>
                            <td className="text-center py-1 px-1">
                              <span className={`inline-flex items-center justify-center w-4 h-4 rounded-full text-micro font-medium ${channel.hired > 0 ? '' : 'bg-lia-bg-tertiary text-lia-text-secondary'}`}>
                                {channel.hired}
                              </span>
                            </td>
                            <td className="text-right py-1 px-1.5 text-lia-text-secondary">
                              {channel.cost > 0 ? `${formatBRL(channel.cost)}` : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Grid 2 colunas: Top Candidatos + Timeline */}
            <div className="grid grid-cols-2 gap-3">
              {/* Top Candidatos */}
              {selectedSections.candidates && (
                <div className="space-y-2">
                  <h3 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1">
                    <Trophy className="w-3 h-3 text-wedo-orange" />
                    Top 5 Candidatos
                  </h3>
                  <div className="space-y-1">
                    {reportData.topCandidates.map((candidate, index) => (
                      <div key={candidate.name} className="flex items-center justify-between p-1.5 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
                        <div className="flex items-center gap-1.5">
                          <div className={`w-5 h-5 rounded-full flex items-center justify-center text-micro font-bold text-white
 ${index === 0 ? 'bg-status-warning' : index === 1 ? 'bg-lia-border-medium' : index === 2 ? 'bg-wedo-orange/10' : 'bg-lia-bg-secondary'}`}>
                            {index + 1}
                          </div>
                          <div>
                            <p className="text-micro font-medium text-lia-text-primary">{candidate.name}</p>
                            <p className="text-micro text-lia-text-secondary">Score: {candidate.score}% • Fit: {candidate.fit}%</p>
                          </div>
                        </div>
                        <span className={`text-micro px-1.5 py-0.5 rounded-full font-medium
 ${candidate.status ==="Final" ?"" :
                          candidate.status ==="Entrevista" ?"bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-wedo-cyan-text" :""}`}>
                          {candidate.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Linha do Tempo */}
              {selectedSections.timeline && (
                <div className="space-y-2">
                  <h3 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-lia-text-secondary" />
                    Linha do Tempo
                  </h3>
                  <div className="relative pl-3">
                    <div className="absolute left-[5px] top-1 bottom-1 w-px bg-lia-border-default"></div>
                    <div className="space-y-1">
                      {reportData.timeline.map((event, index) => (
                        <div key={`event-${index}`} className="relative flex items-center gap-2">
                          <div className={`w-2.5 h-2.5 rounded-full z-10 flex-shrink-0 ${
 event.status === 'completed' ? 'bg-status-success' :
                            event.status === 'in-progress' ? 'bg-status-warning' :
                            'bg-lia-border-default'
                          }`}></div>
                          <div className="flex-1 flex items-center justify-between text-micro">
 <span className={event.status === 'completed' ? 'text-lia-text-primary' : event.status === 'in-progress' ? 'font-medium' : 'text-lia-text-tertiary'}>
                              {event.event}
                            </span>
                            <span className="text-micro text-lia-text-secondary">{event.date}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Predições ML */}
            {(reportData.predictions.timeToFill || reportData.predictions.salary) && (
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1">
                  <Brain className="w-3 h-3 text-wedo-purple" />
                  Análise Preditiva (ML)
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {reportData.predictions.timeToFill && (
                    <div className="p-2 bg-wedo-purple/10 rounded-xl border border-wedo-purple/30">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-micro font-medium text-lia-text-secondary">Previsão Time-to-Fill</span>
                        <Chip variant="neutral" muted className="bg-wedo-purple/20 text-wedo-purple-text text-micro px-1 py-0">
                          {Math.round(reportData.predictions.timeToFill.confidence * 100)}% confiança
                        </Chip>
                      </div>
                      <p className="text-sm font-bold text-lia-text-secondary">
                        {reportData.predictions.timeToFill.predictedDays} dias
                        <span className="text-micro font-normal ml-1">
                          ({reportData.predictions.timeToFill.rangeMin}-{reportData.predictions.timeToFill.rangeMax})
                        </span>
                      </p>
                      <p className="text-micro text-lia-text-secondary mt-0.5">{reportData.predictions.timeToFill.comparisonToMarket}</p>
                      {reportData.predictions.timeToFill.factors.length > 0 && (
                        <div className="mt-1.5 space-y-0.5">
                          <p className="text-micro font-medium text-lia-text-primary">Fatores de risco:</p>
                          {reportData.predictions.timeToFill.factors.slice(0, 3).map((f, i) => (
                            <div key={i} className="flex items-center gap-1 text-micro">
                              <span className={f.impact ==="high" ?"text-status-error" : f.impact ==="medium" ?"text-status-warning" :"text-status-success"}>
                                {f.impact ==="high" ?"▲" : f.impact ==="medium" ?"●" :"▼"}
                              </span>
                              <span className="text-lia-text-secondary">{f.name}: {f.value}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  {reportData.predictions.salary && (
                    <div className="p-2 bg-status-success/10 rounded-xl border border-status-success/30">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-micro font-medium text-status-success">Faixa Salarial Ótima</span>
                        <Chip variant="neutral" muted className="bg-status-success/20 text-status-success text-micro px-1 py-0">
                          P{reportData.predictions.salary.marketPercentile}
                        </Chip>
                      </div>
                      <p className="text-sm font-bold text-status-success">
                        {formatBRL(reportData.predictions.salary.suggestedMin)} — {formatBRL(reportData.predictions.salary.suggestedMax)}
                      </p>
                      <p className="text-micro text-lia-text-secondary mt-0.5">{reportData.predictions.salary.competitiveAnalysis}</p>
                      {reportData.predictions.salary.factors.length > 0 && (
                        <div className="mt-1.5 space-y-0.5">
                          <p className="text-micro font-medium text-lia-text-primary">Fatores de impacto:</p>
                          {reportData.predictions.salary.factors.slice(0, 3).map((f, i) => (
                            <div key={i} className="flex items-center gap-1 text-micro">
                              <span className={f.impact ==="high" ?"text-status-error" : f.impact ==="medium" ?"text-status-warning" :"text-status-success"}>●</span>
                              <span className="text-lia-text-secondary">{f.name}: {f.value}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Métricas de Qualidade (ML) */}
            {(reportData.predictions.timeToFill || reportData.predictions.salary) && (
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1">
                  <Target className="w-3 h-3 text-status-success" />
                  Métricas de Qualidade
                </h3>
                <div className="grid grid-cols-5 gap-2">
                  <div className="p-2 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle text-center">
                    <p className="text-micro text-lia-text-secondary">NPS</p>
                    <p className="text-sm font-bold text-lia-text-primary">{reportData.qualityMetrics.nps}</p>
                  </div>
                  <div className="p-2 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle text-center">
                    <p className="text-micro text-lia-text-secondary">Satisfação Cand.</p>
                    <p className="text-sm font-bold text-lia-text-primary">{reportData.qualityMetrics.candidateSatisfaction}/5</p>
                  </div>
                  <div className="p-2 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle text-center">
                    <p className="text-micro text-lia-text-secondary">Satisfação Gestor</p>
                    <p className="text-sm font-bold text-lia-text-primary">{reportData.qualityMetrics.hiringManagerSatisfaction}/5</p>
                  </div>
                  <div className="p-2 bg-wedo-purple/10 rounded-xl border border-wedo-purple/30 text-center">
                    <p className="text-micro text-lia-text-secondary">Benchmark TTF</p>
                    <p className="text-micro font-medium text-lia-text-secondary">{reportData.qualityMetrics.timeToFillBenchmark}</p>
                  </div>
                  <div className="p-2 bg-status-success/10 rounded-xl border border-status-success/30 text-center">
                    <p className="text-micro text-lia-text-secondary">Salário vs Mercado</p>
                    <p className="text-sm font-bold text-status-success">{reportData.qualityMetrics.marketPercentile}</p>
                    <p className="text-micro font-medium text-status-success">{reportData.qualityMetrics.qualityOfHireBenchmark}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Análise de Custos */}
            {selectedSections.costs && (
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1">
                  <DollarSign className="w-3 h-3 text-wedo-green" />
                  Análise de Custos
                </h3>
                <div className="grid grid-cols-6 gap-2">
                  <div className="col-span-2 p-2 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-default dark:border-lia-border-default">
                    <p className="text-micro text-lia-text-secondary">Orçamento Total</p>
                    <p className="text-sm font-bold text-lia-text-primary">{formatBRL(reportData.budget.total)}</p>
                  </div>
                  <div className="col-span-2 p-2 bg-wedo-orange/10 rounded-xl border border-wedo-orange/30">
                    <p className="text-micro text-lia-text-secondary">Gasto ({Math.round((reportData.budget.spent / reportData.budget.total) * 100)}%)</p>
                    <p className="text-sm font-bold text-wedo-orange-text">{formatBRL(reportData.budget.spent)}</p>
                  </div>
                  <div className="col-span-2 p-2 bg-status-success/10 rounded-xl border border-status-success/30">
                    <p className="text-micro text-lia-text-secondary">Disponível ({Math.round((reportData.budget.remaining / reportData.budget.total) * 100)}%)</p>
                    <p className="text-sm font-bold text-status-success">{formatBRL(reportData.budget.remaining)}</p>
                  </div>
                </div>
                <div className="grid grid-cols-5 gap-1.5">
                  {reportData.budget.breakdown.map((item) => (
                    <div key={item.category} className="p-1.5 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle text-center">
                      <p className="text-micro text-lia-text-secondary truncate">{item.category}</p>
                      <p className="text-micro font-semibold text-lia-text-primary">{formatBRL(item.amount)}</p>
                      <p className="text-micro text-lia-text-secondary">{Math.round((item.amount / reportData.budget.spent) * 100)}%</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recomendações */}
            {selectedSections.recommendations && (
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-lia-text-primary flex items-center gap-1 bg-status-warning/10 py-1.5 px-2 rounded-t border border-status-warning/30 border-b-0">
                  <Lightbulb className="w-3 h-3 text-wedo-orange" />
                  Recomendações e Próximos Passos
                </h3>
                <div className="space-y-1.5 p-2 bg-lia-bg-primary rounded-b border border-lia-border-subtle border-t-0">
                  {[
                    { icon: CheckCircle, color:"text-status-success", bgColor:"bg-status-success/10", title:"Acelerar Processo de Entrevista", desc:"Com 34 candidatos em fase de entrevista, recomenda-se agendar entrevistas em bloco para reduzir o tempo de processo em 30%." },
                    { icon: Brain, color:"text-lia-text-secondary", bgColor:"bg-lia-bg-tertiary dark:bg-lia-bg-secondary", title:"Otimizar Triagem com LIA", desc: `Aumentar o uso da LIA para triagem inicial pode reduzir custos em ${CURRENCY_SYMBOL} 3.000 e melhorar a qualidade dos candidatos em 15%.` },
                    { icon: Target, color:"text-wedo-purple-text", bgColor:"bg-wedo-purple/10", title:"Focar em Canais de Alta Performance", desc:"LinkedIn e LIA Database apresentam melhor qualidade de candidatos. Considere realocar 40% do orçamento para estes canais." },
                    { icon: Clock, color:"text-wedo-orange-text", bgColor:"bg-wedo-orange/10", title:"Definir Prazo para Decisão Final", desc:"Estabelecer deadline de 10 dias para decisões finais pode evitar perda de candidatos qualificados para concorrentes." }
                  ].map((rec, idx) => (
                    <div key={idx} className="flex items-start gap-2">
                      <div className={`w-5 h-5 rounded-full ${rec.bgColor} flex items-center justify-center flex-shrink-0`}>
                        <rec.icon className={`w-3 h-3 ${rec.color}`} />
                      </div>
                      <div className="flex-1">
                        <h4 className="text-micro font-semibold text-lia-text-primary">{rec.title}</h4>
                        <p className="text-micro text-lia-text-secondary leading-tight">{rec.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="p-2 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-default dark:border-lia-border-default flex items-start gap-2">
                  <Zap className="w-4 h-4 text-lia-text-secondary flex-shrink-0" />
                  <div>
                    <h4 className="text-micro font-semibold text-lia-text-primary">Ação Prioritária</h4>
                    <p className="text-micro text-lia-text-primary">
                      Agendar entrevistas com os 12 finalistas nos próximos 3 dias para manter o momentum do processo e garantir as contratações dentro do prazo.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Footer */}
            <div className="pt-3 mt-3 border-t border-lia-border-subtle flex items-center justify-between text-micro text-lia-text-secondary">
              <div>
                <p>Relatório gerado automaticamente pela plataforma WeDoTalent</p>
                <p>© 2025 Sodexo - Todos os direitos reservados</p>
              </div>
              <div className="text-right">

                <p>Versão do relatório: 2.0</p>
                <p>ID do documento: RPT-{String(job.jobId ||"")}-{new Date().getTime()}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
