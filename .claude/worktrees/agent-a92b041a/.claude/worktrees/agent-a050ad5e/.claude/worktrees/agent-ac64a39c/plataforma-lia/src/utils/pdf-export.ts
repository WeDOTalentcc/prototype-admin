export interface PDFExportOptions {
  title: string
  jobId: string
  orientation: 'portrait' | 'landscape'
  includeCharts: boolean
  includeLogos: boolean
  watermark?: string
  branding?: {
    companyName: string
    logo?: string
    colors: {
      primary: string
      secondary: string
    }
  }
}

export class PDFExporter {
  private options: PDFExportOptions

  constructor(options: PDFExportOptions) {
    this.options = options
  }

  async exportReportToPDF(elementId: string, customOptions?: Partial<PDFExportOptions>): Promise<Blob> {
    const finalOptions = { ...this.options, ...customOptions }

    // Mock implementation - em produção usaria jsPDF ou Puppeteer
    const mockPDFContent = this.generateMockPDF(finalOptions)

    // Simular tempo de geração
    await new Promise(resolve => setTimeout(resolve, 2000))

    return new Blob([JSON.stringify(mockPDFContent, null, 2)], {
      type: 'application/pdf'
    })
  }

  private generateMockPDF(options: PDFExportOptions) {
    return {
      title: options.title,
      jobId: options.jobId,
      orientation: options.orientation,
      includeCharts: options.includeCharts,
      includeLogos: options.includeLogos,
      watermark: options.watermark,
      branding: options.branding,
      generatedAt: new Date().toISOString(),
      pages: [
        {
          type: 'cover',
          content: {
            title: options.title,
            subtitle: `Relatório de Vaga ${options.jobId}`,
            generatedDate: new Date().toLocaleDateString('pt-BR'),
            company: options.branding?.companyName || 'Sodexo Enterprise'
          }
        },
        {
          type: 'summary',
          content: {
            kpis: [
              { label: 'Total de Candidatos', value: '234', trend: 'up' },
              { label: 'Taxa de Conversão', value: '12%', trend: 'stable' },
              { label: 'Time to Fill', value: '28 dias', trend: 'down' },
              { label: 'NPS Score', value: '85%', trend: 'up' }
            ]
          }
        },
        {
          type: 'charts',
          content: options.includeCharts ? [
            { type: 'funnel', title: 'Funil de Recrutamento' },
            { type: 'timeline', title: 'Evolução no Tempo' },
            { type: 'sources', title: 'Fontes de Candidatos' }
          ] : []
        },
        {
          type: 'insights',
          content: {
            highlights: [
              'Alta taxa de conversão na triagem inicial (51%)',
              'NPS dos candidatos acima da média do mercado',
              'Tempo de resposta rápido nas etapas iniciais'
            ],
            challenges: [
              'Taxa de conversão baixa entre entrevista e fase final',
              'Concorrência alta no mercado para este perfil',
              'Processo longo pode estar desmotivando candidatos'
            ],
            recommendations: [
              'Revisar processo de entrevistas para otimização',
              'Implementar automação na triagem inicial',
              'Considerar ajuste salarial para aumentar competitividade'
            ]
          }
        }
      ]
    }
  }

  static generateFileName(jobId: string, type: string = 'relatorio'): string {
    const date = new Date().toISOString().split('T')[0]
    return `${type}-${jobId}-${date}.pdf`
  }
}

export function downloadPDF(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function sharePDF(blob: Blob, filename: string): void {
  if (navigator.share && navigator.canShare?.({ files: [new File([blob], filename, { type: 'application/pdf' })] })) {
    const file = new File([blob], filename, { type: 'application/pdf' })
    navigator.share({
      title: 'Relatório de Vaga',
      text: 'Confira o relatório detalhado desta vaga',
      files: [file]
    })
  } else {
    // Fallback para browsers que não suportam Web Share API
    downloadPDF(blob, filename)
  }
}
