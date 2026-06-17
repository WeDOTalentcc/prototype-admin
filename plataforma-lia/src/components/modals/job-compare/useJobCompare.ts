"use client"

import { useState, useMemo } from "react"
import { getJobScoreClass } from "@/lib/score-utils"
import { toast } from "sonner"
import { generateComparePDFBlob } from "./generateComparePDF"

export type ComparisonDimension =
  | "technical_requirements"
  | "competencies"
  | "benefits"
  | "salary_range"
  | "location"
  | "performance"

export interface JobCompareItem {
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
  technical_requirements?: Record<string, unknown>[]
  behavioral_competencies?: Record<string, unknown>[]
}

export interface LiaInsight {
  type: "action_recommended" | "analysis" | "comparative" | "attention"
  title: string
  description: string
}

export interface LiaAnalysisData {
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

export function useJobCompare(jobs: JobCompareItem[]) {
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
    if (!score) return "text-lia-text-tertiary"
    return getJobScoreClass(score)
  }

  const liaAnalysis = useMemo<LiaAnalysisData | null>(() => {
    if (jobs.length < 2) return null

    const totalCandidates = jobs.reduce((sum, j) => sum + (j.candidates_count || 0), 0)
    const totalApproved = jobs.reduce((sum, j) => sum + (j.approved_count || 0), 0)
    const totalScreening = jobs.reduce((sum, j) => sum + (j.screening_count || 0), 0)
    const avgPerformance = jobs.reduce((sum, j) => sum + (j.performance_score || 0), 0) / jobs.length
    const avgConversionRate = totalCandidates > 0 ? (totalApproved / totalCandidates) * 100 : 0

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
        description: `"${bestPerformance.title}" destaca-se com ${bestPerformance.performance_score}% de performance, ${((bestPerformance.performance_score || 0) - avgPerformance).toFixed(0)}% acima da média.`,
      })
    }

    if (worstPerformance.performance_score && worstPerformance.performance_score < 50 && jobs.length > 1) {
      insights.push({
        type: "analysis",
        title: "Taxa de Conversão Baixa",
        description: `"${worstPerformance.title}" apresenta performance de ${worstPerformance.performance_score}%. Considere revisar requisitos ou estratégia de sourcing.`,
      })
    }

    const conversionBestRate =
      ((bestConversion.approved_count || 0) / Math.max(bestConversion.candidates_count || 1, 1)) * 100
    if (conversionBestRate > avgConversionRate * 1.2 && jobs.length > 1) {
      insights.push({
        type: "comparative",
        title: "Diferença de Volume",
        description: `"${bestConversion.title}" converte ${conversionBestRate.toFixed(1)}% dos candidatos, indicando boa qualificação do funil comparado às demais vagas.`,
      })
    }

    if (totalScreening > totalCandidates * 0.4) {
      insights.push({
        type: "action_recommended",
        title: "Alto Volume em Triagem",
        description: `${totalScreening} candidatos aguardam triagem (${((totalScreening / totalCandidates) * 100).toFixed(0)}% do total). Priorize avaliações.`,
      })
    }

    const jobsWithNoApprovals = jobs.filter((j) => (j.approved_count || 0) === 0 && (j.candidates_count || 0) > 0)
    if (jobsWithNoApprovals.length > 0) {
      insights.push({
        type: "attention",
        title: "Vagas Sem Aprovações",
        description: `${jobsWithNoApprovals.length} vaga(s) sem candidatos aprovados: ${jobsWithNoApprovals.map((j) => `"${j.title}"`).join(", ")}. Revise critérios de triagem.`,
      })
    }

    const recommendations: string[] = []

    if (bestPerformance.id !== mostCandidates.id) {
      recommendations.push(
        `Considere replicar estratégias de sourcing de "${mostCandidates.title}" para "${bestPerformance.title}" para aumentar volume qualificado.`
      )
    }

    if (avgConversionRate < 10) {
      recommendations.push(
        "Taxa de conversão média abaixo de 10%. Revise critérios de triagem ou qualidade das fontes de candidatos."
      )
    }

    if (totalScreening > 30) {
      recommendations.push(
        `Priorize triagem das ${totalScreening} candidaturas pendentes para manter pipeline saudável.`
      )
    }

    const jobsWithLowBenefits = jobs.filter((j) => !j.benefits || j.benefits.length < 3)
    if (jobsWithLowBenefits.length > 0) {
      recommendations.push(
        `Complete informações de benefícios em ${jobsWithLowBenefits.length} vaga(s) para melhorar atratividade.`
      )
    }

    return {
      summary: `Comparando ${jobs.length} vagas com total de ${totalCandidates} candidatos. "${bestPerformance.title}" lidera em performance (${bestPerformance.performance_score || 0}%), enquanto "${mostCandidates.title}" possui maior volume (${mostCandidates.candidates_count || 0} candidatos).`,
      keyMetrics: [
        {
          label: "Total Candidatos",
          value: totalCandidates.toString(),
          trend: "neutral" as const,
        },
        {
          label: "Performance Média",
          value: `${avgPerformance.toFixed(0)}%`,
          trend: (avgPerformance >= 60 ? "up" : avgPerformance >= 40 ? "neutral" : "down") as "up" | "down" | "neutral",
          highlight: avgPerformance >= 70,
        },
        {
          label: "Taxa Conversão",
          value: `${avgConversionRate.toFixed(1)}%`,
          trend: (avgConversionRate >= 15 ? "up" : avgConversionRate >= 5 ? "neutral" : "down") as "up" | "down" | "neutral",
        },
        {
          label: "Em Triagem",
          value: totalScreening.toString(),
          trend: (totalScreening > totalCandidates * 0.3 ? "down" : "neutral") as "up" | "down" | "neutral",
        },
      ],
      insights,
      recommendations,
    }
  }, [jobs])

  const generatePDFBlob = async (): Promise<Blob> => {
    const { jsPDF } = await import("jspdf")
    const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: "a4" })

    doc.setFont("helvetica", "bold")
    doc.setFontSize(18)
    doc.setTextColor(17, 24, 39)
    doc.text("Comparativo de Vagas - WeDOTalent", 14, 20)

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
      doc.text("Análise de Compatibilidade", 14, yPos)
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

      liaAnalysis.keyMetrics.forEach((metric) => {
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

        liaAnalysis.insights.forEach((insight) => {
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

        liaAnalysis.recommendations.forEach((rec) => {
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

    const tableHeaders = ["Métrica", ...jobs.map((j) => j.title.substring(0, 25))]
    const tableData = [
      ["Candidatos", ...jobs.map((j) => (j.candidates_count ?? "-").toString())],
      ["Aprovados", ...jobs.map((j) => (j.approved_count ?? "-").toString())],
      ["Em Triagem", ...jobs.map((j) => (j.screening_count ?? "-").toString())],
      ["Performance", ...jobs.map((j) => (j.performance_score ? `${j.performance_score}%` : "-"))],
      ["Local", ...jobs.map((j) => j.location || "-")],
      ["Modelo", ...jobs.map((j) => j.work_model || "-")],
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
    tableData.forEach((row) => {
      row.forEach((cell, idx) => {
        doc.text(cell.substring(0, 20), 14 + idx * colWidth + 2, yPos)
      })
      yPos += 6
    })

    doc.setFontSize(8)
    doc.setTextColor(156, 163, 175)
    doc.text("WeDOTalent | Relatório gerado automaticamente", 14, 200)

    return doc.output("blob")
  }

  const handleExportPDF = async () => {
    setIsExporting(true)
    try {
      let pdfBlob: Blob
      try {
        pdfBlob = await generateComparePDFBlob(jobs, liaAnalysis)
      } catch (err) {
        console.error("Error using generateComparePDFBlob, falling back to local generator", err)
        pdfBlob = await generatePDFBlob()
      }
      const fileName = `comparativo-vagas-${new Date().toISOString().split("T")[0]}.pdf`

      const url = URL.createObjectURL(pdfBlob)
      const a = document.createElement("a")
      a.href = url
      a.download = fileName
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast.success("PDF exportado", { description: "Arquivo salvo com sucesso." })
    } catch {
      toast.error("Erro ao exportar", { description: "Não foi possível gerar o PDF." })
    } finally {
      setIsExporting(false)
    }
  }

  const handleShare = async () => {
    setIsExporting(true)
    try {
      let pdfBlob: Blob
      try {
        pdfBlob = await generateComparePDFBlob(jobs, liaAnalysis)
      } catch (err) {
        console.error("Error using generateComparePDFBlob, falling back to local generator", err)
        pdfBlob = await generatePDFBlob()
      }
      const fileName = `comparativo-vagas-${new Date().toISOString().split("T")[0]}.pdf`
      const file = new File([pdfBlob], fileName, { type: "application/pdf" })

      const shareData = {
        title: "Comparativo de Vagas - WeDOTalent",
        text: `Comparativo de ${jobs.length} vagas`,
        files: [file],
      }

      if (navigator.share && navigator.canShare(shareData)) {
        await navigator.share(shareData)
        toast.success("PDF compartilhado", { description: "Relatório enviado com sucesso." })
      } else {
        const url = URL.createObjectURL(pdfBlob)
        const a = document.createElement("a")
        a.href = url
        a.download = fileName
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
        toast.success("PDF baixado", { description: "Compartilhamento não suportado. Arquivo baixado." })
      }
    } catch (error) {
      if ((error as Error).name !== "AbortError") {
        toast.error("Erro", { description: "Não foi possível compartilhar o PDF." })
      }
    } finally {
      setIsExporting(false)
    }
  }

  return {
    selectedDimensions,
    toggleDimension,
    isExporting,
    formatSalaryRange,
    getScoreColor,
    liaAnalysis,
    handleExportPDF,
    handleShare,
  }
}
