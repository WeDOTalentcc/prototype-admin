import type { JobCompareItem, LiaAnalysisData } from "./useJobCompare"

export async function generateComparePDFBlob(
  jobs: JobCompareItem[],
  liaAnalysis: LiaAnalysisData | null
): Promise<Blob> {
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
