"use client"

import { useCallback } from "react"
import { formatBRL } from "@/lib/pricing"
import type { ParecerLIAData } from "@/components/chat/parecer-lia-card"
import type { WizardPublishHandlersContext } from "./wizardPublishHandlers.types"

export function useWizardParecerData(ctx: WizardPublishHandlersContext) {
  const generateParecerData = useCallback((): ParecerLIAData => {
    const { detectedCriteria, technicalSkills, behavioralCompetencies, salaryInfo, learning } = ctx

    const sections: Array<{ title: string; status: "good" | "attention" | "missing"; items: string[]; suggestions?: string[] }> = []

    const descItems: string[] = []
    const descSuggestions: string[] = []
    if (detectedCriteria.cargo) descItems.push(`Cargo: ${detectedCriteria.cargo}`)
    if (detectedCriteria.senioridadeIdiomas) descItems.push(`Senioridade: ${detectedCriteria.senioridadeIdiomas}`)
    if (detectedCriteria.departamento) descItems.push(`Departamento: ${detectedCriteria.departamento}`)
    if (detectedCriteria.modeloTrabalho) descItems.push(`Modelo: ${detectedCriteria.modeloTrabalho}`)
    if (detectedCriteria.localizacao) descItems.push(`Local: ${detectedCriteria.localizacao}`)
    if (!detectedCriteria.senioridadeIdiomas) descSuggestions.push("Adicionar senioridade para melhor calibração de candidatos")
    if (!detectedCriteria.modeloTrabalho) descSuggestions.push("Definir modelo de trabalho (remoto, híbrido, presencial)")
    sections.push({
      title: "Descrição da Vaga",
      status: descItems.length >= 4 ? "good" : descItems.length >= 2 ? "attention" : "missing",
      items: descItems,
      suggestions: descSuggestions.length > 0 ? descSuggestions : undefined
    })

    const respItems = detectedCriteria.responsabilidades || []
    sections.push({
      title: "Responsabilidades",
      status: respItems.length >= 3 ? "good" : respItems.length >= 1 ? "attention" : "missing",
      items: respItems.length > 0 ? respItems.slice(0, 5) : ["Nenhuma responsabilidade identificada"],
      suggestions: respItems.length < 3 ? ["Adicionar pelo menos 3 responsabilidades principais"] : undefined
    })

    const techItems = technicalSkills.map(s => `${s.name} (${s.level})`)
    const techFromCriteria = detectedCriteria.competenciasTecnicas || []
    const techDisplay = techItems.length > 0 ? techItems : techFromCriteria.map(s => s)
    sections.push({
      title: "Competências Técnicas",
      status: techDisplay.length >= 3 ? "good" : techDisplay.length >= 1 ? "attention" : "missing",
      items: techDisplay.length > 0 ? techDisplay.slice(0, 6) : ["Nenhuma competência técnica identificada"],
      suggestions: techDisplay.length < 3 ? ["Incluir pelo menos 3 skills técnicos para melhor triagem WSI"] : undefined
    })

    const behavItems = behavioralCompetencies.filter(c => c.enabled).map(c => c.name)
    const behavFromCriteria = detectedCriteria.competenciasComportamentais || []
    const behavDisplay = behavItems.length > 0 ? behavItems : behavFromCriteria
    sections.push({
      title: "Competências Comportamentais",
      status: behavDisplay.length >= 2 ? "good" : behavDisplay.length >= 1 ? "attention" : "missing",
      items: behavDisplay.length > 0 ? behavDisplay.slice(0, 5) : ["Nenhuma competência comportamental identificada"],
      suggestions: behavDisplay.length < 2 ? ["Definir competências comportamentais para avaliação cultural"] : undefined
    })

    const salaryItems: string[] = []
    const salarySuggestions: string[] = []
    if (salaryInfo.minSalary && salaryInfo.maxSalary) {
      salaryItems.push(`Faixa: ${formatBRL(Number(salaryInfo.minSalary))} - ${formatBRL(Number(salaryInfo.maxSalary))}`)
    }
    if (salaryInfo.minBonus || salaryInfo.maxBonus) {
      salaryItems.push(`Bônus: ${salaryInfo.minBonus || '0'}% - ${salaryInfo.maxBonus || '0'}%`)
    }
    const enabledBenefits = salaryInfo.benefits?.filter(b => b.enabled) || []
    if (enabledBenefits.length > 0) {
      salaryItems.push(`${enabledBenefits.length} benefício(s) definido(s)`)
    }
    if (!salaryInfo.minSalary) salarySuggestions.push("Definir faixa salarial para atrair candidatos adequados")
    sections.push({
      title: "Remuneração",
      status: salaryItems.length >= 2 ? "good" : salaryItems.length >= 1 ? "attention" : "missing",
      items: salaryItems.length > 0 ? salaryItems : ["Remuneração ainda não definida"],
      suggestions: salarySuggestions.length > 0 ? salarySuggestions : undefined
    })

    const marketComparisons: Array<{ field: string; yourValue: string; marketValue: string; status: "above" | "aligned" | "below" }> = []
    if (learning.suggestions?.salary?.has_suggestion && salaryInfo.minSalary) {
      const yourMin = parseFloat(salaryInfo.minSalary.replace(/\./g, '').replace(',', '.')) || 0
      const marketMin = learning.suggestions.salary.min_salary || 0
      const marketMax = learning.suggestions.salary.max_salary || 0
      if (marketMin > 0) {
        marketComparisons.push({
          field: "Faixa Salarial",
          yourValue: `${formatBRL(Number(salaryInfo.minSalary))} - ${formatBRL(Number(salaryInfo.maxSalary))}`,
          marketValue: `${formatBRL(marketMin)} - ${formatBRL(marketMax)}`,
          status: yourMin > marketMax ? "above" : yourMin < marketMin * 0.8 ? "below" : "aligned"
        })
      }
    }

    let timeToFillEstimate: ParecerLIAData['timeToFillEstimate']
    if (learning.suggestions?.time_to_fill?.has_prediction) {
      const ttf = learning.suggestions.time_to_fill
      timeToFillEstimate = {
        days: ttf.estimated_days || ttf.median_days || 30,
        rangeMin: ttf.range_min || 20,
        rangeMax: ttf.range_max || 45,
        confidence: ttf.confidence || 0.5
      }
    }

    const sectionScores: number[] = sections.map(s => s.status === "good" ? 1 : s.status === "attention" ? 0.5 : 0)
    const overallScore = Math.round((sectionScores.reduce((a, b) => a + b, 0) / sectionScores.length) * 100)

    const totalFields = 10
    const filledFields = [
      detectedCriteria.cargo,
      detectedCriteria.senioridadeIdiomas,
      detectedCriteria.departamento,
      detectedCriteria.modeloTrabalho,
      detectedCriteria.localizacao,
      (detectedCriteria.responsabilidades?.length || 0) > 0,
      techDisplay.length > 0,
      behavDisplay.length > 0,
      salaryInfo.minSalary,
      detectedCriteria.gestorArea
    ].filter(Boolean).length
    const completenessScore = Math.round((filledFields / totalFields) * 100)

    const recommendations: string[] = []
    sections.forEach(s => {
      if (s.suggestions) {
        s.suggestions.forEach(sug => recommendations.push(sug))
      }
    })
    if (recommendations.length === 0) {
      recommendations.push("A vaga está bem estruturada! Revise os detalhes e avance para a próxima etapa.")
    }

    const dataSourcesUsed: string[] = ["Critérios informados pelo recrutador"]
    if (learning.suggestions?.has_suggestions) {
      dataSourcesUsed.push(`${learning.suggestions.total_samples || 0} vagas similares`)
      if (learning.suggestions.patterns_found > 0) {
        dataSourcesUsed.push(`${learning.suggestions.patterns_found} padrões identificados`)
      }
    }

    return {
      overallScore,
      completenessScore,
      sections,
      marketComparisons: marketComparisons.length > 0 ? marketComparisons : undefined,
      timeToFillEstimate,
      similarJobsCount: learning.suggestions?.total_samples,
      dataSourcesUsed,
      recommendations
    }
  }, [ctx])

  return { generateParecerData }
}
