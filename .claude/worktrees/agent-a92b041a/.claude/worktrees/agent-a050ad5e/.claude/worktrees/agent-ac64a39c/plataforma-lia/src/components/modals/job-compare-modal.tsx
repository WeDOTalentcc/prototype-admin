"use client"

import { useState, useMemo } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Scale,
  Brain,
  Download,
  Share2,
  MapPin,
  Users,
  CheckCircle,
  Clock,
  DollarSign,
  Target,
  Award,
  Gift,
  Briefcase,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Lightbulb,
  BarChart3,
  Filter,
  Zap,
  Search,
  ArrowRightLeft,
  XCircle,
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"

interface JobCompareModalProps {
  isOpen: boolean
  onClose: () => void
  jobs: Array<{
    id: string
    code?: string
    title: string
    department?: string
    location?: string
    work_model?: string
    salary_range?: { min?: number; max?: number }
    status: string
    deadline?: string
    candidates_count?: number
    approved_count?: number
    screening_count?: number
    performance_score?: number
    benefits?: string[]
    technical_requirements?: any[]
    behavioral_competencies?: any[]
  }>
}

type ComparisonDimension =
  | "technical_requirements"
  | "competencies"
  | "benefits"
  | "salary_range"
  | "location"
  | "performance"

const COMPARISON_DIMENSIONS: {
  id: ComparisonDimension
  label: string
  icon: React.ElementType
}[] = [
  { id: "technical_requirements", label: "Técnicos", icon: Target },
  { id: "competencies", label: "Competências", icon: Award },
  { id: "benefits", label: "Benefícios", icon: Gift },
  { id: "salary_range", label: "Salário", icon: DollarSign },
  { id: "location", label: "Local", icon: MapPin },
  { id: "performance", label: "Performance", icon: Brain },
]

interface LiaInsight {
  type: "action_recommended" | "analysis" | "comparative" | "attention"
  title: string
  description: string
}

const INSIGHT_STYLES: Record<LiaInsight["type"], {
  bg: string
  border: string
  iconColor: string
  badgeText: string
  badgeBg: string
  icon: React.ElementType
}> = {
  action_recommended: {
    bg: "bg-amber-50",
    border: "border-amber-200",
    iconColor: "text-amber-600",
    badgeText: "Ação Recomendada",
    badgeBg: "bg-amber-100 text-amber-700",
    icon: Zap,
  },
  analysis: {
    bg: "bg-purple-50",
    border: "border-purple-200",
    iconColor: "text-purple-600",
    badgeText: "Análise",
    badgeBg: "bg-purple-100 text-purple-700",
    icon: Search,
  },
  comparative: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    iconColor: "text-blue-600",
    badgeText: "Comparativo",
    badgeBg: "bg-blue-100 text-blue-700",
    icon: ArrowRightLeft,
  },
  attention: {
    bg: "bg-red-50",
    border: "border-red-200",
    iconColor: "text-red-600",
    badgeText: "Atenção",
    badgeBg: "bg-red-100 text-red-700",
    icon: XCircle,
  },
}

const JOB_COLORS = [
 { bar: "bg-gray-900", text: "text-gray-600 dark:text-gray-400", light: "bg-gray-100 dark:bg-gray-800" },
  { bar: "bg-purple-500", text: "text-purple-600", light: "bg-purple-100" },
  { bar: "bg-emerald-500", text: "text-emerald-600", light: "bg-emerald-100" },
  { bar: "bg-orange-500", text: "text-orange-600", light: "bg-orange-100" },
]

interface LiaAnalysisData {
  summary: string
  keyMetrics: {
    label: string
    value: string
    trend?: "up" | "down" | "neutral"
    highlight?: boolean
  }[]
  insights: LiaInsight[]
  recommendations: string[]
}

export function JobCompareModal({ isOpen, onClose, jobs }: JobCompareModalProps) {
  const { toast } = useToast()
  const [selectedDimensions, setSelectedDimensions] = useState<Set<ComparisonDimension>>(
    new Set(["technical_requirements", "competencies", "salary_range", "location", "performance"])
  )
  const [isExporting, setIsExporting] = useState(false)

  const toggleDimension = (dimension: ComparisonDimension) => {
    const newSet = new Set(selectedDimensions)
    if (newSet.has(dimension)) {
      newSet.delete(dimension)
    } else {
      newSet.add(dimension)
    }
    setSelectedDimensions(newSet)
  }

  const formatCurrency = (value?: number) => {
    if (!value) return "-"
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatSalaryRange = (range?: { min?: number; max?: number }) => {
    if (!range) return "-"
    if (range.min && range.max) {
      return `${formatCurrency(range.min)} - ${formatCurrency(range.max)}`
    }
    if (range.min) return `A partir de ${formatCurrency(range.min)}`
    if (range.max) return `Até ${formatCurrency(range.max)}`
    return "-"
  }

  const getScoreColor = (score?: number) => {
    if (!score) return "text-gray-500"
    if (score >= 80) return "text-gray-600 dark:text-gray-400 font-semibold"
    if (score >= 60) return "text-gray-950"
    return "text-gray-800"
  }

  const liaAnalysis = useMemo<LiaAnalysisData | null>(() => {
    if (jobs.length < 2) return null

    const totalCandidates = jobs.reduce((sum, j) => sum + (j.candidates_count || 0), 0)
    const totalApproved = jobs.reduce((sum, j) => sum + (j.approved_count || 0), 0)
    const totalScreening = jobs.reduce((sum, j) => sum + (j.screening_count || 0), 0)
    const avgPerformance = jobs.reduce((sum, j) => sum + (j.performance_score || 0), 0) / jobs.length
    const avgConversionRate = totalCandidates > 0 ? (totalApproved / totalCandidates * 100) : 0

    const bestPerformance = jobs.reduce((best, job) =>
      (job.performance_score || 0) > (best.performance_score || 0) ? job : best
    )
    const worstPerformance = jobs.reduce((worst, job) =>
      (job.performance_score || 0) < (worst.performance_score || 0) ? job : worst
    )
    const mostCandidates = jobs.reduce((best, job) =>
      (job.candidates_count || 0) > (best.candidates_count || 0) ? job : best
    )
    const bestConversion = jobs.reduce((best, job) => {
      const bestRate = (best.approved_count || 0) / Math.max(best.candidates_count || 1, 1)
      const jobRate = (job.approved_count || 0) / Math.max(job.candidates_count || 1, 1)
      return jobRate > bestRate ? job : best
    })

    const insights: LiaInsight[] = []

    if (bestPerformance.performance_score && bestPerformance.performance_score >= 70) {
      insights.push({
        type: "analysis",
        title: "Alta Performance Identificada",
        description: `"${bestPerformance.title}" destaca-se com ${bestPerformance.performance_score}% de performance, ${((bestPerformance.performance_score || 0) - avgPerformance).toFixed(0)}% acima da média.`
      })
    }

    if (worstPerformance.performance_score && worstPerformance.performance_score < 50 && jobs.length > 1) {
      insights.push({
        type: "analysis",
        title: "Taxa de Conversão Baixa",
        description: `"${worstPerformance.title}" apresenta performance de ${worstPerformance.performance_score}%. Considere revisar requisitos ou estratégia de sourcing.`
      })
    }

    const conversionBestRate = (bestConversion.approved_count || 0) / Math.max(bestConversion.candidates_count || 1, 1) * 100
    if (conversionBestRate > avgConversionRate * 1.2 && jobs.length > 1) {
      insights.push({
        type: "comparative",
        title: "Diferença de Volume",
        description: `"${bestConversion.title}" converte ${conversionBestRate.toFixed(1)}% dos candidatos, indicando boa qualificação do pipeline comparado às demais vagas.`
      })
    }

    if (totalScreening > totalCandidates * 0.4) {
      insights.push({
        type: "action_recommended",
        title: "Alto Volume em Triagem",
        description: `${totalScreening} candidatos aguardam triagem (${((totalScreening/totalCandidates)*100).toFixed(0)}% do total). Priorize avaliações.`
      })
    }

    const jobsWithNoApprovals = jobs.filter(j => (j.approved_count || 0) === 0 && (j.candidates_count || 0) > 0)
    if (jobsWithNoApprovals.length > 0) {
      insights.push({
        type: "attention",
        title: "Vagas Sem Aprovações",
        description: `${jobsWithNoApprovals.length} vaga(s) sem candidatos aprovados: ${jobsWithNoApprovals.map(j => `"${j.title}"`).join(", ")}. Revise critérios de triagem.`
      })
    }

    const recommendations: string[] = []
    
    if (bestPerformance.id !== mostCandidates.id) {
      recommendations.push(`Considere replicar estratégias de sourcing de "${mostCandidates.title}" para "${bestPerformance.title}" para aumentar volume qualificado.`)
    }
    
    if (avgConversionRate < 10) {
      recommendations.push("Taxa de conversão média abaixo de 10%. Revise critérios de triagem ou qualidade das fontes de candidatos.")
    }

    if (totalScreening > 30) {
      recommendations.push(`Priorize triagem das ${totalScreening} candidaturas pendentes para manter pipeline saudável.`)
    }

    const jobsWithLowBenefits = jobs.filter(j => !j.benefits || j.benefits.length < 3)
    if (jobsWithLowBenefits.length > 0) {
      recommendations.push(`Complete informações de benefícios em ${jobsWithLowBenefits.length} vaga(s) para melhorar atratividade.`)
    }

    return {
      summary: `Comparando ${jobs.length} vagas com total de ${totalCandidates} candidatos. "${bestPerformance.title}" lidera em performance (${bestPerformance.performance_score || 0}%), enquanto "${mostCandidates.title}" possui maior volume (${mostCandidates.candidates_count || 0} candidatos).`,
      keyMetrics: [
        {
          label: "Total Candidatos",
          value: totalCandidates.toString(),
          trend: "neutral"
        },
        {
          label: "Performance Média",
          value: `${avgPerformance.toFixed(0)}%`,
          trend: avgPerformance >= 60 ? "up" : avgPerformance >= 40 ? "neutral" : "down",
          highlight: avgPerformance >= 70
        },
        {
          label: "Taxa Conversão",
          value: `${avgConversionRate.toFixed(1)}%`,
          trend: avgConversionRate >= 15 ? "up" : avgConversionRate >= 5 ? "neutral" : "down"
        },
        {
          label: "Em Triagem",
          value: totalScreening.toString(),
          trend: totalScreening > totalCandidates * 0.3 ? "down" : "neutral"
        }
      ],
      insights,
      recommendations
    }
  }, [jobs])

  const handleExportPDF = async () => {
    setIsExporting(true)
    try {
      const pdfBlob = await generatePDFBlob()
      const fileName = `comparativo-vagas-${new Date().toISOString().split("T")[0]}.pdf`
      
      const url = URL.createObjectURL(pdfBlob)
      const a = document.createElement("a")
      a.href = url
      a.download = fileName
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      toast({
        title: "PDF exportado",
        description: "Arquivo salvo com sucesso.",
      })
    } catch (error) {
      console.error("Erro ao exportar PDF:", error)
      toast({
        title: "Erro ao exportar",
        description: "Não foi possível gerar o PDF.",
        variant: "destructive",
      })
    } finally {
      setIsExporting(false)
    }
  }

  const generatePDFBlob = async (): Promise<Blob> => {
    const { jsPDF } = await import("jspdf")
    const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: "a4" })
    
    doc.setFont("helvetica", "bold")
    doc.setFontSize(18)
    doc.setTextColor(17, 24, 39)
    doc.text("Comparativo de Vagas - WedoTalent", 14, 20)
    
    doc.setFont("helvetica", "normal")
    doc.setFontSize(10)
    doc.setTextColor(107, 114, 128)
    doc.text(`Gerado em: ${new Date().toLocaleDateString("pt-BR")} às ${new Date().toLocaleTimeString("pt-BR")}`, 14, 28)
    doc.text(`${jobs.length} vagas comparadas`, 14, 34)
    
    let yPos = 45
    
    doc.setFont("helvetica", "bold")
    doc.setFontSize(12)
    doc.setTextColor(17, 24, 39)
    doc.text("Vagas Comparadas", 14, yPos)
    yPos += 8
    
    jobs.forEach((job, idx) => {
      doc.setFont("helvetica", "normal")
      doc.setFontSize(10)
      doc.setTextColor(55, 65, 81)
      const jobInfo = `${idx + 1}. ${job.code ? `[${job.code}] ` : ""}${job.title}`
      doc.text(jobInfo, 14, yPos)
      yPos += 6
    })
    
    yPos += 5
    
    if (liaAnalysis) {
      doc.setFont("helvetica", "bold")
      doc.setFontSize(12)
      doc.setTextColor(17, 24, 39)
      doc.text("Análise LIA", 14, yPos)
      yPos += 8
      
      doc.setFont("helvetica", "normal")
      doc.setFontSize(9)
      doc.setTextColor(55, 65, 81)
      const summaryLines = doc.splitTextToSize(liaAnalysis.summary, 260)
      doc.text(summaryLines, 14, yPos)
      yPos += summaryLines.length * 5 + 5
      
      doc.setFont("helvetica", "bold")
      doc.setFontSize(10)
      doc.text("Indicadores-Chave:", 14, yPos)
      yPos += 6
      
      liaAnalysis.keyMetrics.forEach(metric => {
        doc.setFont("helvetica", "normal")
        doc.setFontSize(9)
        doc.text(`• ${metric.label}: ${metric.value}`, 18, yPos)
        yPos += 5
      })
      
      yPos += 3
      
      if (liaAnalysis.insights.length > 0) {
        doc.setFont("helvetica", "bold")
        doc.setFontSize(10)
        doc.text("Insights:", 14, yPos)
        yPos += 6
        
        liaAnalysis.insights.forEach(insight => {
          doc.setFont("helvetica", "normal")
          doc.setFontSize(9)
          const insightText = `• ${insight.title}: ${insight.description}`
          const insightLines = doc.splitTextToSize(insightText, 255)
          doc.text(insightLines, 18, yPos)
          yPos += insightLines.length * 5 + 2
        })
      }
      
      yPos += 3
      
      if (liaAnalysis.recommendations.length > 0) {
        doc.setFont("helvetica", "bold")
        doc.setFontSize(10)
        doc.text("Recomendações:", 14, yPos)
        yPos += 6
        
        liaAnalysis.recommendations.forEach(rec => {
          doc.setFont("helvetica", "normal")
          doc.setFontSize(9)
          const recLines = doc.splitTextToSize(`• ${rec}`, 255)
          doc.text(recLines, 18, yPos)
          yPos += recLines.length * 5 + 2
        })
      }
    }
    
    yPos += 10
    
    if (yPos > 150) {
      doc.addPage()
      yPos = 20
    }
    
    doc.setFont("helvetica", "bold")
    doc.setFontSize(12)
    doc.setTextColor(17, 24, 39)
    doc.text("Tabela Comparativa", 14, yPos)
    yPos += 8
    
    const tableHeaders = ["Métrica", ...jobs.map(j => j.title.substring(0, 25))]
    const tableData = [
      ["Candidatos", ...jobs.map(j => (j.candidates_count ?? "-").toString())],
      ["Aprovados", ...jobs.map(j => (j.approved_count ?? "-").toString())],
      ["Em Triagem", ...jobs.map(j => (j.screening_count ?? "-").toString())],
      ["Performance", ...jobs.map(j => j.performance_score ? `${j.performance_score}%` : "-")],
      ["Local", ...jobs.map(j => j.location || "-")],
      ["Modelo", ...jobs.map(j => j.work_model || "-")],
    ]
    
    const colWidth = Math.min(70, 260 / (jobs.length + 1))
    
    doc.setFont("helvetica", "bold")
    doc.setFontSize(8)
    doc.setFillColor(249, 250, 251)
    doc.rect(14, yPos - 3, colWidth * tableHeaders.length, 8, "F")
    
    tableHeaders.forEach((header, idx) => {
      doc.text(header.substring(0, 15), 14 + idx * colWidth + 2, yPos + 2)
    })
    yPos += 10
    
    doc.setFont("helvetica", "normal")
    tableData.forEach(row => {
      row.forEach((cell, idx) => {
        doc.text(cell.substring(0, 20), 14 + idx * colWidth + 2, yPos)
      })
      yPos += 6
    })
    
    doc.setFontSize(8)
    doc.setTextColor(156, 163, 175)
    doc.text("WedoTalent - Plataforma LIA | Relatório gerado automaticamente", 14, 200)
    
    return doc.output("blob")
  }

  const handleShare = async () => {
    setIsExporting(true)
    try {
      const pdfBlob = await generatePDFBlob()
      const fileName = `comparativo-vagas-${new Date().toISOString().split("T")[0]}.pdf`
      const file = new File([pdfBlob], fileName, { type: "application/pdf" })
      
      const shareData = {
        title: "Comparativo de Vagas - WedoTalent",
        text: `Comparativo de ${jobs.length} vagas`,
        files: [file],
      }

      if (navigator.share && navigator.canShare(shareData)) {
        await navigator.share(shareData)
        toast({
          title: "PDF compartilhado",
          description: "Relatório enviado com sucesso.",
        })
      } else {
        const url = URL.createObjectURL(pdfBlob)
        const a = document.createElement("a")
        a.href = url
        a.download = fileName
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
        toast({
          title: "PDF baixado",
          description: "Compartilhamento não suportado. Arquivo baixado.",
        })
      }
    } catch (error) {
      if ((error as Error).name !== "AbortError") {
        console.error("Erro ao compartilhar:", error)
        toast({
          title: "Erro",
          description: "Não foi possível compartilhar o PDF.",
          variant: "destructive",
        })
      }
    } finally {
      setIsExporting(false)
    }
  }

  if (!isOpen) return null

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className="max-w-4xl max-h-[90vh] overflow-y-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md"
        style={{ fontFamily: "'Open Sans', sans-serif" }}
      >
        <DialogHeader className="border-b border-gray-200 dark:border-gray-700 pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gray-100 dark:bg-gray-700 rounded-md flex items-center justify-center">
                <Scale className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              </div>
              <div>
                <DialogTitle className="text-[14px] font-semibold text-gray-950 dark:text-gray-50">
                  Comparar Vagas
                </DialogTitle>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                  {jobs.length} vaga{jobs.length > 1 ? "s" : ""} selecionada{jobs.length > 1 ? "s" : ""}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleShare}
                className="h-7 px-2.5 text-[11px] gap-1.5 border-gray-200 text-gray-700 hover:bg-gray-50"
              >
                <Share2 className="w-3 h-3" />
                Compartilhar
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportPDF}
                disabled={isExporting}
                className="h-7 px-2.5 text-[11px] gap-1.5 border-gray-200 text-gray-700 hover:bg-gray-50"
              >
                <Download className="w-3 h-3" />
                {isExporting ? "Gerando..." : "Exportar PDF"}
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="py-4 space-y-4">
          <div className="grid grid-cols-[240px_1fr] gap-4">
            <div className="space-y-3">
              <div>
                <h4 className="text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-2">
                  Vagas Selecionadas
                </h4>
                <div className="space-y-1.5 max-h-[120px] overflow-y-auto">
                  {jobs.map((job) => (
                    <div
                      key={job.id}
                      className="p-2 rounded-md bg-gray-50 border border-gray-200"
                    >
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-md bg-white border border-gray-200 flex items-center justify-center flex-shrink-0">
                          <Briefcase className="w-3 h-3 text-gray-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1">
                            {job.code && (
                              <span className="text-[10px] font-medium text-gray-600 bg-gray-100 px-1 py-0.5 rounded-full">
                                {job.code}
                              </span>
                            )}
                          </div>
                          <span className="text-xs font-medium text-gray-950 truncate block">
                            {job.title}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-2">
                  Dimensões
                </h4>
                <div className="space-y-1.5 p-2.5 rounded-md bg-gray-50 border border-gray-200">
                  {COMPARISON_DIMENSIONS.map((dim) => (
                    <label
                      key={dim.id}
                      className="flex items-center gap-2 cursor-pointer group"
                    >
                      <Checkbox
                        checked={selectedDimensions.has(dim.id)}
                        onCheckedChange={() => toggleDimension(dim.id)}
                        className="w-3.5 h-3.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                      />
                      <dim.icon className="w-3 h-3 text-gray-500 group-hover:text-gray-900" />
                      <span className="text-[11px] text-gray-800 group-hover:text-gray-950">
                        {dim.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-[11px]">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="text-left font-semibold text-gray-600 uppercase tracking-wide p-2.5 border border-gray-200 w-[100px]">
                      Métrica
                    </th>
                    {jobs.map((job) => (
                      <th
                        key={job.id}
                        className="text-left font-semibold text-gray-950 p-2.5 border border-gray-200 min-w-[180px]"
                      >
                        <div className="flex flex-col gap-0.5">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {job.code && (
                              <span className="text-[10px] text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded-full font-medium">
                                {job.code}
                              </span>
                            )}
                            <span className="text-gray-950 text-xs font-semibold">
                              {job.title}
                            </span>
                          </div>
                          {job.department && (
                            <span className="text-[10px] font-normal text-gray-500">{job.department}</span>
                          )}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr className="hover:bg-gray-50">
                    <td className="text-gray-800 p-2.5 border border-gray-200">
                      <div className="flex items-center gap-1.5">
                        <Users className="w-3.5 h-3.5 text-gray-500" />
                        Candidatos
                      </div>
                    </td>
                    {jobs.map((job) => (
                      <td key={job.id} className="text-gray-950 p-2.5 border border-gray-200 font-medium text-[13px]">
                        {job.candidates_count ?? "-"}
                      </td>
                    ))}
                  </tr>

                  <tr className="hover:bg-gray-50">
                    <td className="text-gray-800 p-2.5 border border-gray-200">
                      <div className="flex items-center gap-1.5">
                        <CheckCircle className="w-3.5 h-3.5 text-green-600" />
                        Aprovados
                      </div>
                    </td>
                    {jobs.map((job) => (
                      <td key={job.id} className="text-gray-700 p-2.5 border border-gray-200 font-semibold text-[13px]">
                        {job.approved_count ?? "-"}
                      </td>
                    ))}
                  </tr>

                  <tr className="hover:bg-gray-50">
                    <td className="text-gray-800 p-2.5 border border-gray-200">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-gray-600" />
                        Triagem
                      </div>
                    </td>
                    {jobs.map((job) => (
                      <td key={job.id} className="text-gray-800 p-2.5 border border-gray-200 font-medium text-[13px]">
                        {job.screening_count ?? "-"}
                      </td>
                    ))}
                  </tr>

                  {selectedDimensions.has("salary_range") && (
                    <tr className="hover:bg-gray-50">
                      <td className="text-gray-800 p-2.5 border border-gray-200">
                        <div className="flex items-center gap-1.5">
                          <DollarSign className="w-3.5 h-3.5 text-gray-500" />
                          Salário
                        </div>
                      </td>
                      {jobs.map((job) => (
                        <td key={job.id} className="text-gray-950 p-2.5 border border-gray-200 text-[11px]">
                          {formatSalaryRange(job.salary_range)}
                        </td>
                      ))}
                    </tr>
                  )}

                  {selectedDimensions.has("location") && (
                    <tr className="hover:bg-gray-50">
                      <td className="text-gray-800 p-2.5 border border-gray-200">
                        <div className="flex items-center gap-1.5">
                          <MapPin className="w-3.5 h-3.5 text-gray-500" />
                          Local
                        </div>
                      </td>
                      {jobs.map((job) => (
                        <td key={job.id} className="text-gray-950 p-2.5 border border-gray-200 text-[11px]">
                          {job.location || "-"} {job.work_model && `(${job.work_model})`}
                        </td>
                      ))}
                    </tr>
                  )}

                  {selectedDimensions.has("performance") && (
                    <tr className="hover:bg-gray-50 bg-gray-50">
                      <td className="text-gray-800 p-2.5 border border-gray-200">
                        <div className="flex items-center gap-1.5">
                          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                          Performance
                        </div>
                      </td>
                      {jobs.map((job) => (
                        <td key={job.id} className="p-2.5 border border-gray-200">
                          <span className={`text-[13px] font-semibold ${getScoreColor(job.performance_score)}`}>
                            {job.performance_score ? `${job.performance_score}%` : "-"}
                          </span>
                        </td>
                      ))}
                    </tr>
                  )}

                  {selectedDimensions.has("technical_requirements") && (
                    <tr className="hover:bg-gray-50">
                      <td className="text-gray-800 p-2.5 border border-gray-200 align-top">
                        <div className="flex items-center gap-1.5">
                          <Target className="w-3.5 h-3.5 text-gray-500" />
                          Requisitos
                        </div>
                      </td>
                      {jobs.map((job) => (
                        <td key={job.id} className="text-gray-950 p-2.5 border border-gray-200 align-top">
                          {job.technical_requirements && job.technical_requirements.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {job.technical_requirements.slice(0, 4).map((req, idx) => (
                                <span key={idx} className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 text-gray-700">
                                  {typeof req === "string" ? req : req.name || req.skill || "-"}
                                </span>
                              ))}
                              {job.technical_requirements.length > 4 && (
                                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 text-gray-500">
                                  +{job.technical_requirements.length - 4}
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  )}

                  {selectedDimensions.has("competencies") && (
                    <tr className="hover:bg-gray-50">
                      <td className="text-gray-800 p-2.5 border border-gray-200 align-top">
                        <div className="flex items-center gap-1.5">
                          <Award className="w-3.5 h-3.5 text-gray-500" />
                          Competências
                        </div>
                      </td>
                      {jobs.map((job) => (
                        <td key={job.id} className="text-gray-950 p-2.5 border border-gray-200 align-top">
                          {job.behavioral_competencies && job.behavioral_competencies.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {job.behavioral_competencies.slice(0, 4).map((comp, idx) => (
                                <span key={idx} className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 text-gray-700">
                                  {typeof comp === "string" ? comp : comp.name || comp.competency || "-"}
                                </span>
                              ))}
                              {job.behavioral_competencies.length > 4 && (
                                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 text-gray-500">
                                  +{job.behavioral_competencies.length - 4}
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  )}

                  {selectedDimensions.has("benefits") && (
                    <tr className="hover:bg-gray-50">
                      <td className="text-gray-800 p-2.5 border border-gray-200 align-top">
                        <div className="flex items-center gap-1.5">
                          <Gift className="w-3.5 h-3.5 text-gray-500" />
                          Benefícios
                        </div>
                      </td>
                      {jobs.map((job) => (
                        <td key={job.id} className="text-gray-950 p-2.5 border border-gray-200 align-top">
                          {job.benefits && job.benefits.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {job.benefits.slice(0, 4).map((benefit, idx) => (
                                <span key={idx} className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 text-gray-700">
                                  {benefit}
                                </span>
                              ))}
                              {job.benefits.length > 4 && (
                                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 text-gray-500">
                                  +{job.benefits.length - 4}
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {jobs.length >= 2 && (
            <div className="border border-gray-200 rounded-md overflow-hidden">
              <div className="bg-gray-50 border-b border-gray-200 px-4 py-2.5">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 bg-gray-100 rounded-md flex items-center justify-center">
                    <Filter className="w-3.5 h-3.5 text-gray-600" />
                  </div>
                  <h3 className="text-[13px] font-semibold text-gray-950">Funil de Candidatos</h3>
                </div>
              </div>
              
              <div className="p-4 space-y-4">
                {jobs.map((job, jobIndex) => {
                  const jobColor = JOB_COLORS[jobIndex % JOB_COLORS.length]
                  const total = job.candidates_count || 0
                  const screening = job.screening_count || 0
                  const approved = job.approved_count || 0
                  const screeningPct = total > 0 ? (screening / total * 100) : 0
                  const approvedPct = total > 0 ? (approved / total * 100) : 0

                  return (
                    <div key={job.id} className="space-y-2">
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-2.5 h-2.5 rounded-full ${jobColor.bar}`} />
                        <span className="text-xs font-semibold text-gray-950">
                          {job.code && <span className={`${jobColor.text} mr-1.5`}>[{job.code}]</span>}
                          {job.title}
                        </span>
                      </div>
                      
                      <div className="space-y-1.5 pl-4">
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] text-gray-600 w-[70px]">Candidatos</span>
                          <div className="flex-1 h-4 bg-gray-100 rounded overflow-hidden">
                            <div
                              className={`h-full ${jobColor.bar} transition-all duration-300`}
                              style={{ width: "100%" }}
                            />
                          </div>
                          <span className={`text-[11px] font-semibold w-[80px] text-right ${jobColor.text}`}>
                            {total} (100%)
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] text-gray-600 w-[70px]">Em Triagem</span>
                          <div className="flex-1 h-4 bg-gray-100 rounded overflow-hidden">
                            <div
                              className={`h-full ${jobColor.bar} opacity-70 transition-all duration-300`}
                              style={{ width: `${Math.max(screeningPct, 0)}%` }}
                            />
                          </div>
                          <span className={`text-[11px] font-medium w-[80px] text-right text-gray-700`}>
                            {screening} ({screeningPct.toFixed(0)}%)
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] text-gray-600 w-[70px]">Aprovados</span>
                          <div className="flex-1 h-4 bg-gray-100 rounded overflow-hidden">
                            <div
                              className={`h-full ${jobColor.bar} opacity-50 transition-all duration-300`}
                              style={{ width: `${Math.max(approvedPct, 0)}%` }}
                            />
                          </div>
                          <span className={`text-[11px] font-medium w-[80px] text-right text-gray-700`}>
                            {approved} ({approvedPct.toFixed(0)}%)
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {liaAnalysis && jobs.length >= 2 && (
            <div className="border border-gray-200 rounded-md overflow-hidden">
              <div className="bg-gray-50 border-b border-gray-200 px-4 py-2.5">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 bg-gray-100 dark:bg-gray-800 rounded-md flex items-center justify-center">
                    <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                  </div>
                  <h3 className="text-[13px] font-semibold text-gray-950">Análise LIA</h3>
                </div>
              </div>
              
              <div className="p-4 space-y-4">
                <p className="text-xs text-gray-700 leading-relaxed">
                  {liaAnalysis.summary}
                </p>

                <div>
                  <h4 className="text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                    <BarChart3 className="w-3 h-3" />
                    Indicadores-Chave
                  </h4>
                  <div className="grid grid-cols-4 gap-3">
                    {liaAnalysis.keyMetrics.map((metric, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-md border ${
                          metric.highlight
                            ? "bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                            : "bg-gray-50 border-gray-200"
                        }`}
                      >
                        <p className="text-[10px] text-gray-500 uppercase tracking-wide mb-1">
                          {metric.label}
                        </p>
                        <div className="flex items-center gap-1.5">
                          <span className={`text-[18px] font-semibold ${
                            metric.highlight ? "text-gray-600 dark:text-gray-400" : "text-gray-950"
                          }`}>
                            {metric.value}
                          </span>
                          {metric.trend === "up" && (
                            <TrendingUp className="w-3.5 h-3.5 text-green-500" />
                          )}
                          {metric.trend === "down" && (
                            <TrendingDown className="w-3.5 h-3.5 text-amber-500" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {liaAnalysis.insights.length > 0 && (
                  <div>
                    <h4 className="text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                      <Lightbulb className="w-3 h-3" />
                      Insights
                    </h4>
                    <div className="space-y-2">
                      {liaAnalysis.insights.map((insight, idx) => {
                        const style = INSIGHT_STYLES[insight.type]
                        const IconComponent = style.icon
                        return (
                          <div
                            key={idx}
                            className={`p-3 rounded-md border flex items-start gap-2.5 ${style.bg} ${style.border}`}
                          >
                            <IconComponent className={`w-4 h-4 ${style.iconColor} flex-shrink-0 mt-0.5`} />
                            <div className="flex-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <p className="text-[11px] font-semibold text-gray-950">{insight.title}</p>
                                <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full ${style.badgeBg}`}>
                                  {style.badgeText}
                                </span>
                              </div>
                              <p className="text-[11px] text-gray-700 mt-0.5 leading-relaxed">
                                {insight.description}
                              </p>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {liaAnalysis.recommendations.length > 0 && (
                  <div>
                    <h4 className="text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                      <Target className="w-3 h-3" />
                      Recomendações
                    </h4>
                    <ul className="space-y-1.5">
                      {liaAnalysis.recommendations.map((rec, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-[11px] text-gray-700">
                          <span className="text-gray-400 mt-0.5">•</span>
                          <span className="leading-relaxed">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="pt-3 border-t border-gray-200 dark:border-gray-700">
          <Button
            onClick={onClose}
            className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
          >
            Fechar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
