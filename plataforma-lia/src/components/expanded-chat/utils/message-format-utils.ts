/**
 * message-format-utils — utilitários puros de formatação de mensagens.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.3 — 2026-03-27).
 * Portabilidade Vue: funções puras, sem dependências React.
 */

import { type CompensationAnalysisResult } from '@/components/job-creation/compensation-analysis-panel'

export function formatTimestamp(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'agora'
  if (diffMins < 60) return `${diffMins} min atrás`
  if (diffHours < 24) return `${diffHours}h atrás`
  if (diffDays === 1) return 'ontem'
  if (diffDays < 7) return `${diffDays} dias atrás`
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}

export function formatSalaryAnalysisText(analysis: CompensationAnalysisResult | null): string {
  if (!analysis) return ''

  const formatCurrency = (value: number): string =>
    new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)

  const statusLabels: Record<string, { emoji: string; label: string; description: string }> = {
    competitive: { emoji: '✅', label: 'Competitivo', description: 'A remuneração proposta está alinhada com as práticas do mercado' },
    below_market: { emoji: '⚠️', label: 'Abaixo do Mercado', description: 'A faixa proposta pode dificultar a atração de talentos qualificados' },
    above_market: { emoji: '📈', label: 'Acima do Mercado', description: 'Excelente! A remuneração é mais atrativa que a média' },
  }

  const status = statusLabels[analysis.overallStatus] || statusLabels.competitive

  const proposedMin = formatCurrency(analysis.salary.proposed.min)
  const proposedMax = formatCurrency(analysis.salary.proposed.max)
  const marketMin = formatCurrency(analysis.salary.market.min)
  const marketMax = formatCurrency(analysis.salary.market.max)

  const proposedRange = `${proposedMin} - ${proposedMax}`
  const marketRange = `${marketMin} - ${marketMax}`
  const percentilStr = `Percentil ${analysis.salary.percentileVsMarket}`

  let text = `Com base nas informações que você forneceu sobre a vaga, realizei uma análise de mercado sobre a remuneração proposta. Aqui está minha avaliação:

**${status.emoji} Análise de Remuneração: ${status.label}**

${status.description}.

**COMPARATIVO SALARIAL**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Proposto:  ${proposedRange}
📈 Mercado:   ${marketRange}
🎯 Posição:   ${percentilStr}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Análise:**
${analysis.executiveSummary}`

  if (analysis.salary.suggestion) {
    const sugMin = formatCurrency(analysis.salary.suggestion.min)
    const sugMax = formatCurrency(analysis.salary.suggestion.max)
    text += `

**💡 Sugestão:**
Para melhorar a competitividade da vaga, considere ajustar a faixa para **${sugMin} - ${sugMax}**.`
  }

  text += `

**Próximos passos:**
• "confirmar" - manter os valores atuais
• "aceitar sugestão" - aplicar os valores recomendados
• "ajustar para R$ X a R$ Y" - definir novos valores manualmente`

  return text
}
