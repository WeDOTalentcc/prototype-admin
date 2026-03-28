"use client"

import React, { useCallback } from "react"
import { type ParecerLIAData } from "@/components/chat/parecer-lia-card"
import { liaApi, type JobVacancyCreateRequest } from "@/services/lia-api"
import {
  type TechnicalSkill,
  type BehavioralCompetency,
  type SalaryInfo,
  type DetectedCriteria,
  type BasicInfoFields,
} from "../ExpandedChatContext"
import { type WizardStage } from "../config/wizard-config"
import { type Message } from "../types"
import { type PublishingPlatform, type JobConfig } from "./usePublishingState"
import { type RecruitmentStage } from "@/components/settings/recruitment-journey.types"
import { useLearning } from "./useLearning"

export interface WizardPublishHandlersContext {
  // Detected criteria and basic info
  detectedCriteria: DetectedCriteria
  setDetectedCriteria: React.Dispatch<React.SetStateAction<DetectedCriteria>>
  basicInfoFields: BasicInfoFields
  setBasicInfoFields: React.Dispatch<React.SetStateAction<BasicInfoFields>>

  // Skills and competencies
  technicalSkills: TechnicalSkill[]
  setTechnicalSkills: React.Dispatch<React.SetStateAction<TechnicalSkill[]>>
  behavioralCompetencies: BehavioralCompetency[]
  setBehavioralCompetencies: React.Dispatch<React.SetStateAction<BehavioralCompetency[]>>

  // Salary and benefits
  salaryInfo: SalaryInfo
  setSalaryInfo: React.Dispatch<React.SetStateAction<SalaryInfo>>

  // Messages
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>

  // Stage management
  currentStage: WizardStage
  setCurrentStage: React.Dispatch<React.SetStateAction<WizardStage>>

  // Publishing state
  publishingPlatforms: PublishingPlatform[]
  jobConfig: JobConfig
  setJobDescription: (desc: string) => void
  setIsGeneratingDescription: (val: boolean) => void

  // Calibration and search
  setPublishedJobId: (id: string | null) => void
  setAwaitingCalibrationChoice: (val: boolean) => void
  setSearchPhase: React.Dispatch<React.SetStateAction<'local-searching' | 'local-complete' | 'global-searching' | 'global-complete' | 'idle'>>
  setLocalCandidateCount: (count: number) => void
  setGlobalCandidateCount: (count: number) => void
  preferredCandidateCount: number

  // Competency suggestions
  selectedSuggestedTechnical: Set<string>
  selectedSuggestedBehavioral: Set<string>
  setShowCompetenciesSuggestionsModal: (val: boolean) => void

  // Draft management
  clearWizardDraft: () => void
  setHasAppliedRestoredDraft: (val: boolean) => void
  setShowClearDraftConfirm: (val: boolean) => void
  setWsiCandidates: React.Dispatch<React.SetStateAction<any[]>>
  setGeneratedJobDescription: React.Dispatch<React.SetStateAction<string>>

  // Company config
  companyConfig: { values?: string[]; [key: string]: unknown } | null
  interviewStages: RecruitmentStage[]
  companyMembersMap: Map<string, string>
  companyDefaultQuestions: Array<{ enabled: boolean; question: string; type: string }>
  wsiCandidates: Array<{ selected: boolean; question: string; category?: string; expectedAnswer?: unknown; type?: string }>

  // User
  user: { name?: string; email?: string; company?: string; id?: string } | null

  // Fast track
  wizardFastTrackSourceJobId: string | null
  setWizardFastTrackSourceJobId: (id: string | null) => void

  // Conversation
  conversationId: string | null

  // Learning suggestions
  learning: ReturnType<typeof useLearning>

  // Loading state
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>

  // Proceed to next stage callback (defined in component — calls setCurrentStage etc.)
  proceedToNextStage: () => void
}

export function useWizardPublishHandlers(ctx: WizardPublishHandlersContext) {
  const generateCriteriaResponse = (criteria: DetectedCriteria): string => {
    const detected: string[] = []
    const missing: string[] = []

    if (criteria.cargo) detected.push(`**Cargo**: ${criteria.cargo}`)
    else missing.push('cargo')

    if (criteria.gestorArea) detected.push(`**Gestor**: ${criteria.gestorArea}`)

    if (criteria.responsabilidades.length > 0) {
      detected.push(`**Responsabilidades**: ${criteria.responsabilidades.slice(0, 4).join(', ')}${criteria.responsabilidades.length > 4 ? ` (+${criteria.responsabilidades.length - 4})` : ''}`)
    }

    if (criteria.competenciasTecnicas.length > 0) {
      detected.push(`**Skills técnicos**: ${criteria.competenciasTecnicas.slice(0, 5).join(', ')}${criteria.competenciasTecnicas.length > 5 ? ` (+${criteria.competenciasTecnicas.length - 5})` : ''}`)
    } else {
      missing.push('competências técnicas')
    }

    if (criteria.competenciasComportamentais.length > 0) {
      detected.push(`**Competências comportamentais**: ${criteria.competenciasComportamentais.slice(0, 3).join(', ')}`)
    }

    if (criteria.idiomas && criteria.idiomas.length > 0) {
      detected.push(`**Idiomas**: ${criteria.idiomas.join(', ')}`)
    }

    if (criteria.senioridadeIdiomas) detected.push(`**Senioridade**: ${criteria.senioridadeIdiomas}`)
    else missing.push('senioridade')

    if (criteria.modeloTrabalho) {
      let modeloText = `**Modelo**: ${criteria.modeloTrabalho}`
      if (criteria.diasPresenciais) {
        modeloText += ` (${criteria.diasPresenciais}x por semana no escritório)`
      }
      detected.push(modeloText)
    }
    if (criteria.localizacao) detected.push(`**Local**: ${criteria.localizacao}`)
    if (criteria.tipoContrato) detected.push(`**Contrato**: ${criteria.tipoContrato}`)
    if (criteria.salario) detected.push(`**Salário**: ${criteria.salario}`)
    if (criteria.bonus) detected.push(`**Bônus**: ${criteria.bonus}`)
    if (criteria.isAffirmative !== null) {
      let affirmText = `**Vaga Afirmativa**: ${criteria.isAffirmative ? 'Sim' : 'Não'}`
      if (criteria.affirmativeCriteriaPrimary) {
        affirmText += ` (${criteria.affirmativeCriteriaPrimary}${criteria.affirmativeCriteriaSecondary ? `, ${criteria.affirmativeCriteriaSecondary}` : ''})`
      }
      detected.push(affirmText)
    }

    // Novos campos detectáveis
    if (criteria.experienciaMinima) detected.push(`**Experiência**: ${criteria.experienciaMinima}`)
    if (criteria.formacao && criteria.formacao.length > 0) {
      detected.push(`**Formação**: ${criteria.formacao.join(', ')}`)
    }
    if (criteria.certificacoes && criteria.certificacoes.length > 0) {
      detected.push(`**Certificações**: ${criteria.certificacoes.join(', ')}`)
    }
    if (criteria.ferramentas && criteria.ferramentas.length > 0) {
      detected.push(`**Ferramentas**: ${criteria.ferramentas.slice(0, 5).join(', ')}${criteria.ferramentas.length > 5 ? ` (+${criteria.ferramentas.length - 5})` : ''}`)
    }
    if (criteria.beneficiosMencionados && criteria.beneficiosMencionados.length > 0) {
      detected.push(`**Benefícios**: ${criteria.beneficiosMencionados.slice(0, 4).join(', ')}${criteria.beneficiosMencionados.length > 4 ? ` (+${criteria.beneficiosMencionados.length - 4})` : ''}`)
    }
    if (criteria.viagensFrequentes) detected.push(`**Viagens**: Sim`)
    if (criteria.disponibilidade) detected.push(`**Início**: ${criteria.disponibilidade}`)
    if (criteria.cnh) detected.push(`**CNH**: ${criteria.cnh}`)
    if (criteria.horario) detected.push(`**Horário**: ${criteria.horario}`)

    let response = ''

    if (detected.length > 0) {
      response = `Detectei os seguintes critérios:\n\n${detected.map(d => `- ${d}`).join('\n')}`

      if (missing.length > 0 && missing.length <= 2) {
        response += `\n\nPara completar, informe: **${missing.join('** e **')}**.`
      } else if (detected.length >= 3) {
        response += `\n\nÓtimo progresso! Você pode adicionar mais detalhes para enriquecer a vaga.`
      }
    } else {
      response = 'Não consegui detectar critérios específicos. Tente descrever o cargo, senioridade, skills técnicos e modelo de trabalho.'
    }

    return response
  }

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
      salaryItems.push(`Faixa: R$ ${salaryInfo.minSalary} - R$ ${salaryInfo.maxSalary}`)
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
          yourValue: `R$ ${salaryInfo.minSalary} - ${salaryInfo.maxSalary}`,
          marketValue: `R$ ${marketMin.toLocaleString('pt-BR')} - ${marketMax.toLocaleString('pt-BR')}`,
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

  // Generate competency analysis message from LIA
  const generateCompetencyAnalysisMessage = (
    cargo: string | null,
    area: string | null,
    criteria: DetectedCriteria,
    deduplicatedSkills?: string[]
  ): string => {
    const role = cargo || 'profissional'

    let message = `**Análise de Competências para ${role}**\n\n`
    message += `Com base nas informações da vaga e dados de mercado, preparei sugestões de competências:\n\n`

    if (criteria.competenciasTecnicas.length > 0) {
      message += `**Competências Técnicas Identificadas:**\n`
      criteria.competenciasTecnicas.slice(0, 5).forEach(skill => {
        message += `• ${skill}\n`
      })
      message += `\n`
    }

    if (criteria.competenciasComportamentais.length > 0) {
      message += `**Competências Comportamentais Sugeridas:**\n`
      criteria.competenciasComportamentais.slice(0, 4).forEach(comp => {
        message += `• ${comp}\n`
      })
      message += `\n`
    }

    message += `📊 *Fontes: histórico de vagas similares + dados de mercado*\n\n`
    message += `Me informe aqui no chat se deseja adicionar, remover ou alterar os pesos das competências.`

    return message
  }

  // Generate WSI explanation message from LIA
  const generateWSIExplanationMessage = (
    technicalSkillsList: string[],
    behavioralCompetenciesList: string[],
    cargo: string | null
  ): string => {
    const role = cargo || 'a vaga'
    const totalCompetencies = technicalSkillsList.length + behavioralCompetenciesList.length

    let message = `**Gerando Perguntas de Triagem WSI**\n\n`
    message += `Vou criar perguntas baseadas na metodologia WSI (Work Sample Interview), que combina:\n\n`
    message += `• **Taxonomia de Bloom** - níveis cognitivos\n`
    message += `• **Modelo Dreyfus** - proficiência técnica\n`
    message += `• **Big Five** - traços comportamentais\n\n`

    message += `Considerando as ${totalCompetencies} competências definidas para ${role}, `
    message += `as perguntas avaliarão tanto habilidades técnicas quanto comportamentais.\n\n`

    message += `⏳ *Aguarde enquanto gero as perguntas personalizadas...*`

    return message
  }

  // Handle accepting selected suggestions from the modal
  const handleAcceptSuggestions = () => {
    const { selectedSuggestedTechnical, selectedSuggestedBehavioral, setTechnicalSkills, setBehavioralCompetencies, setMessages, setShowCompetenciesSuggestionsModal, proceedToNextStage } = ctx

    const skillCategories: Record<string, 'language' | 'framework' | 'database' | 'tool'> = {
      'Python': 'language', 'Java': 'language', 'Node.js': 'framework', 'React': 'framework',
      'TypeScript': 'language', 'SQL': 'database', 'Docker': 'tool', 'AWS': 'tool',
      'Git': 'tool', 'Linux': 'tool', 'MongoDB': 'database', 'PostgreSQL': 'database',
      'Kubernetes': 'tool', 'CI/CD': 'tool', 'REST API': 'tool',
      'Excel Avançado': 'tool', 'Power BI': 'tool', 'SAP': 'tool', 'ERP': 'tool'
    }

    const newTechnicalSkills: TechnicalSkill[] = Array.from(selectedSuggestedTechnical).map((skill, idx) => ({
      id: `suggested-tech-${Date.now()}-${idx}`,
      name: skill,
      level: 'Intermediário' as const,
      required: idx < 3,
      category: skillCategories[skill] || 'tool',
      weight: idx < 3 ? 3 : 2
    }))

    setTechnicalSkills(prev => {
      const existingNames = prev.map(s => s.name.toLowerCase())
      const filteredNew = newTechnicalSkills.filter(s => !existingNames.includes(s.name.toLowerCase()))
      return [...prev, ...filteredNew]
    })

    const newBehavioralCompetencies: BehavioralCompetency[] = Array.from(selectedSuggestedBehavioral).map((comp, idx) => ({
      id: `suggested-behav-${Date.now()}-${idx}`,
      name: comp,
      weight: 4,
      justification: 'Sugerido pela LIA com base no cargo/área',
      enabled: true
    }))

    setBehavioralCompetencies(prev => {
      const existingNames = prev.map(c => c.name.toLowerCase())
      const filteredNew = newBehavioralCompetencies.filter(c => !existingNames.includes(c.name.toLowerCase()))
      return [...prev, ...filteredNew]
    })

    const acceptedCount = selectedSuggestedTechnical.size + selectedSuggestedBehavioral.size
    if (acceptedCount > 0) {
      const feedbackMessage = {
        id: `suggestions-accepted-${Date.now()}`,
        role: 'assistant' as const,
        content: `Ótimo! Adicionei **${selectedSuggestedTechnical.size} competências técnicas** e **${selectedSuggestedBehavioral.size} comportamentais** baseadas no perfil da vaga. Me informe aqui no chat se precisar ajustar os pesos e níveis.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, feedbackMessage])
    }

    setShowCompetenciesSuggestionsModal(false)
    proceedToNextStage()
  }

  // Handle skipping suggestions
  const handleSkipSuggestions = () => {
    ctx.setShowCompetenciesSuggestionsModal(false)
    ctx.proceedToNextStage()
  }

  const handleClearDraftAndReset = () => {
    const {
      clearWizardDraft, setMessages, setBasicInfoFields, setTechnicalSkills,
      setBehavioralCompetencies, setSalaryInfo, setWsiCandidates, setDetectedCriteria,
      setCurrentStage, setGeneratedJobDescription, setHasAppliedRestoredDraft, setShowClearDraftConfirm
    } = ctx

    clearWizardDraft()
    setMessages([])
    setBasicInfoFields({
      cargo: '',
      area: '',
      gestor: '',
      localidade: '',
      modeloTrabalho: '',
      tipoContrato: ''
    })
    setTechnicalSkills([])
    setBehavioralCompetencies([
      { id: '1', name: 'Comunicação Eficaz', weight: 4, justification: '', enabled: false },
      { id: '2', name: 'Resolução de Problemas', weight: 5, justification: '', enabled: false },
      { id: '3', name: 'Adaptabilidade', weight: 4, justification: '', enabled: false },
      { id: '4', name: 'Trabalho em Equipe', weight: 4, justification: '', enabled: false },
      { id: '5', name: 'Proatividade', weight: 3, justification: '', enabled: false },
    ])
    setSalaryInfo({
      minSalary: '',
      maxSalary: '',
      minBonus: '',
      maxBonus: '',
      bonusCriteria: '',
      benefits: []
    })
    setWsiCandidates([])
    setDetectedCriteria({
      cargo: null,
      gestorArea: null,
      responsabilidades: [],
      competenciasTecnicas: [],
      competenciasComportamentais: [],
      idiomas: [],
      senioridadeIdiomas: null,
      modeloTrabalho: null,
      localizacao: null,
      tipoContrato: null,
      salario: null,
      departamento: null,
      isAffirmative: null,
      affirmativeCriteriaPrimary: null,
      affirmativeCriteriaSecondary: null,
      affirmativeDescription: null,
      experienciaMinima: null,
      formacao: [],
      certificacoes: [],
      ferramentas: [],
      diasPresenciais: null,
      beneficiosMencionados: [],
      bonus: null,
      viagensFrequentes: null,
      disponibilidade: null,
      cnh: null,
      horario: null
    })
    setCurrentStage('input-evaluation')
    setGeneratedJobDescription('')
    setHasAppliedRestoredDraft(false)
    setShowClearDraftConfirm(false)
  }

  const buildCandidateSearchQuery = (): string => {
    const { basicInfoFields, detectedCriteria, technicalSkills } = ctx
    const parts: string[] = []
    if (basicInfoFields.cargo) parts.push(basicInfoFields.cargo)
    if (detectedCriteria.senioridadeIdiomas) parts.push(detectedCriteria.senioridadeIdiomas)
    if (basicInfoFields.area) parts.push(basicInfoFields.area)
    const topSkills = technicalSkills.slice(0, 5).map(s => s.name)
    if (topSkills.length > 0) parts.push(topSkills.join(', '))
    if (basicInfoFields.localidade) parts.push(basicInfoFields.localidade)
    return parts.join(' ') || 'profissional'
  }

  const startLocalSearch = async () => {
    const { setSearchPhase, setLocalCandidateCount, preferredCandidateCount } = ctx
    setSearchPhase('local-searching')
    try {
      const searchQuery = buildCandidateSearchQuery()
      const response = await liaApi.searchCandidatesLocal({
        query: searchQuery,
        limit: Math.max(20, preferredCandidateCount * 5)
      })
      setLocalCandidateCount(response.total_results || response.candidates?.length || 0)
      setSearchPhase('local-complete')
    } catch (error) {
      console.error('Local search error:', error)
      setLocalCandidateCount(0)
      setSearchPhase('local-complete')
    }
  }

  const startGlobalSearch = async () => {
    const { setSearchPhase, setGlobalCandidateCount, preferredCandidateCount } = ctx
    setSearchPhase('global-searching')
    try {
      const searchQuery = buildCandidateSearchQuery()
      const response = await liaApi.searchCandidates({
        query: searchQuery,
        search_type: 'fast',
        limit: Math.max(100, preferredCandidateCount * 20)
      })
      setGlobalCandidateCount(response.total_results || response.candidates?.length || 0)
      setSearchPhase('global-complete')
    } catch (error) {
      console.error('Global search error:', error)
      setGlobalCandidateCount(0)
      setSearchPhase('global-complete')
    }
  }

  const handlePublishJob = async () => {
    const {
      basicInfoFields, detectedCriteria, technicalSkills, behavioralCompetencies,
      salaryInfo, publishingPlatforms, jobConfig, interviewStages, wsiCandidates,
      companyDefaultQuestions, companyMembersMap, conversationId, user,
      wizardFastTrackSourceJobId, setWizardFastTrackSourceJobId,
      setPublishedJobId, setAwaitingCalibrationChoice, setCurrentStage,
      clearWizardDraft, setMessages, setIsLoading
    } = ctx

    setIsLoading(true)
    try {
      const linkedinPlatform = publishingPlatforms.find(p => p.id === 'linkedin')
      const indeedPlatform = publishingPlatforms.find(p => p.id === 'indeed')
      const websitePlatform = publishingPlatforms.find(p => p.id === 'website')

      const jobData = {
        title: basicInfoFields.cargo || 'Nova Vaga',
        department: basicInfoFields.area || undefined,
        location: basicInfoFields.localidade || undefined,
        work_model: basicInfoFields.modeloTrabalho || undefined,
        hybrid_days_onsite: basicInfoFields.modeloTrabalho === 'Híbrido'
          ? (jobConfig.hybridDaysOnsite || 3)
          : undefined,
        employment_type: basicInfoFields.tipoContrato || 'CLT',
        seniority_level: detectedCriteria.senioridadeIdiomas || 'Pleno',
        description: ctx.messages.find(m => m.role === 'user')?.content || `Vaga de ${basicInfoFields.cargo}`,
        requirements: technicalSkills.filter(s => s.required).map(s => s.name),
        technical_requirements: technicalSkills.map(s => ({
          name: s.name,
          level: s.level,
          required: s.required,
          weight: s.weight
        })),
        behavioral_competencies: behavioralCompetencies.filter(c => c.enabled).map(c => ({
          name: c.name,
          weight: c.weight,
          justification: c.justification
        })),
        salary: salaryInfo.minSalary && salaryInfo.maxSalary
          ? `R$ ${parseInt(salaryInfo.minSalary).toLocaleString('pt-BR')} - R$ ${parseInt(salaryInfo.maxSalary).toLocaleString('pt-BR')}`
          : undefined,
        salary_range: (salaryInfo.minSalary || salaryInfo.maxSalary || salaryInfo.minBonus || salaryInfo.maxBonus) ? {
          min: salaryInfo.minSalary ? parseInt(salaryInfo.minSalary) : undefined,
          max: salaryInfo.maxSalary ? parseInt(salaryInfo.maxSalary) : undefined,
          currency: 'BRL',
          bonus_min: salaryInfo.minBonus ? parseInt(salaryInfo.minBonus) : undefined,
          bonus_max: salaryInfo.maxBonus ? parseInt(salaryInfo.maxBonus) : undefined
        } : undefined,
        benefits: salaryInfo.benefits.filter(b => b.enabled).map(b => b.name),
        manager: basicInfoFields.gestor || undefined,
        status: 'active' as const,
        recruiter: user?.name || user?.email?.split('@')[0] || 'Recrutador',
        recruiter_email: user?.email || '',
        open_date: new Date().toISOString(),
        urgency_level: jobConfig.urgencyLevel,
        visibility: jobConfig.visibility,
        is_confidential: jobConfig.isConfidential,
        is_affirmative: jobConfig.isAffirmative,
        affirmative_criteria_primary: detectedCriteria.affirmativeCriteriaPrimary,
        affirmative_criteria_secondary: detectedCriteria.affirmativeCriteriaSecondary,
        affirmative_description: detectedCriteria.affirmativeDescription,
        deadline: jobConfig.deadline,
        deadline_screening: jobConfig.deadlineScreening,
        deadline_shortlist: jobConfig.deadlineShortlist,
        languages: jobConfig.languages.map(l => ({ name: l.name, level: l.level })),
        stage: 'screening',
        target_audience: jobConfig.visibility === 'internal' || jobConfig.visibility === 'confidential' ? 'internal' : 'external',
        masked_company_name: jobConfig.isConfidential ? 'Empresa Confidencial' : undefined,
        interview_stages: interviewStages.length > 0
          ? interviewStages.map((stage, index) => ({
              stageName: stage.name,
              order: index + 1,
              type: stage.name.toLowerCase().includes('triagem') ? 'screening' :
                    stage.name.toLowerCase().includes('técnic') ? 'technical' :
                    stage.name.toLowerCase().includes('rh') ? 'interview' :
                    stage.name.toLowerCase().includes('final') || stage.name.toLowerCase().includes('gestor') ? 'final' :
                    'interview',
              sla: stage.sla
            }))
          : [
              { stageName: 'Triagem', order: 1, type: 'screening' },
              { stageName: 'Entrevista RH', order: 2, type: 'interview' },
              { stageName: 'Entrevista Técnica', order: 3, type: 'technical' },
              { stageName: 'Entrevista Final', order: 4, type: 'final' },
            ],
        hiring_process: interviewStages.length > 0
          ? interviewStages.map(stage => stage.name)
          : ['Triagem', 'Entrevista RH', 'Entrevista Técnica', 'Entrevista Final'],
        published_linkedin: linkedinPlatform?.enabled || false,
        published_indeed: indeedPlatform?.enabled || false,
        published_website: websitePlatform?.enabled || false,
        eligibility_questions: companyDefaultQuestions.filter(q => q.enabled).map(q => ({
          question: q.question,
          category: 'eligibility',
          type: q.type,
          weight: 3,
          is_eliminatory: true
        })),
        screening_questions: wsiCandidates.filter(q => q.selected).map(q => ({
          question: q.question,
          category: q.category,
          expected_answer: q.expectedAnswer,
          weight: 5,
          type: q.type
        })),
        conversation_id: conversationId || undefined
      }

      const createdJob = await liaApi.createJobVacancy(jobData as JobVacancyCreateRequest)

      const jobId = (createdJob as any).job_id || createdJob.id
      setPublishedJobId(jobId)

      if (wizardFastTrackSourceJobId && jobId && jobId !== wizardFastTrackSourceJobId) {
        const tenantId = user?.company || 'default'
        liaApi.recordFastTrackUsage({
          company_id: tenantId,
          source_job_id: wizardFastTrackSourceJobId,
          new_job_id: jobId,
          modified_fields: [],
          was_published: true
        }).catch(err => console.error('Non-blocking: Fast Track usage recording failed:', err))
        setWizardFastTrackSourceJobId(null)
      }

      try {
        await liaApi.sendJobCreatedNotification({
          job_id: jobId,
          job_title: basicInfoFields.cargo || 'Nova Vaga',
          department: basicInfoFields.area || undefined,
          location: basicInfoFields.localidade || undefined,
          work_model: basicInfoFields.modeloTrabalho || undefined,
          seniority_level: detectedCriteria.senioridadeIdiomas || undefined,
          job_description: ctx.messages.find(m => m.role === 'user')?.content || `Vaga de ${basicInfoFields.cargo}`,
          technical_requirements: technicalSkills.map(s => ({
            name: s.name,
            level: s.level,
            required: s.required,
            weight: s.weight
          })),
          behavioral_competencies: behavioralCompetencies.filter(c => c.enabled).map(c => ({
            name: c.name,
            weight: String(c.weight)
          })),
          languages: jobConfig.languages.map(l => ({ name: l.name, level: l.level })),
          salary_range: (salaryInfo.minSalary || salaryInfo.maxSalary) ? {
            min: salaryInfo.minSalary ? parseInt(salaryInfo.minSalary) : undefined,
            max: salaryInfo.maxSalary ? parseInt(salaryInfo.maxSalary) : undefined,
            currency: 'BRL'
          } : undefined,
          benefits: salaryInfo.benefits.filter(b => b.enabled).map(b => b.name),
          deadline_screening: jobConfig.deadlineScreening,
          deadline_shortlist: jobConfig.deadlineShortlist,
          deadline_closing: jobConfig.deadline,
          interview_stages: interviewStages.map((stage, index) => ({
            stageName: stage.name,
            order: index + 1,
            sla: stage.sla
          })),
          publishing_platforms: {
            linkedin: linkedinPlatform?.enabled || false,
            indeed: indeedPlatform?.enabled || false,
            website: websitePlatform?.enabled || false
          },
          urgency_level: jobConfig.urgencyLevel,
          is_confidential: jobConfig.isConfidential,
          is_affirmative: jobConfig.isAffirmative,
          recruiter_email: user?.email || '',
          recruiter_name: user?.name || user?.email?.split('@')[0] || 'Recrutador',
          manager_email: basicInfoFields.gestor
            ? (companyMembersMap.get(basicInfoFields.gestor.trim()) ||
               companyMembersMap.get(basicInfoFields.gestor.trim().toLowerCase()))
            : undefined,
          manager_name: basicInfoFields.gestor || undefined,
          channels: ['email', 'teams']
        })
      } catch (notifError) {
        console.error('Failed to send job created notification (non-blocking):', notifError)
      }

      const publishMessage = {
        id: `publish-${Date.now()}`,
        role: 'assistant' as const,
        content: `A vaga **${basicInfoFields.cargo || 'Nova Vaga'}** foi criada e publicada com sucesso! 🎉

📋 **ID da Vaga:** ${jobId}
🏢 **Área:** ${basicInfoFields.area || 'A definir'}
📍 **Local:** ${basicInfoFields.localidade || 'A definir'}

---

**Próximo passo: Calibração de Busca**

Posso apresentar alguns candidatos para você avaliar agora. Isso me ajuda a entender melhor o perfil ideal e melhora a precisão das próximas sugestões em até 60%.

**OU** você pode ir direto para o Kanban e eu aprendo naturalmente conforme você move candidatos pelo funil (aprovar → entrevista, reprovar → descartado).

*O que prefere?*
• "Calibrar agora" - mostro 5 perfis rápidos para você avaliar
• "Ir para o kanban" - já adiciono os candidatos e você avalia lá`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, publishMessage])

      setAwaitingCalibrationChoice(true)
      setCurrentStage('search-calibration')
      clearWizardDraft()
      startLocalSearch()
    } catch (error) {
      console.error('Error creating job vacancy:', error)

      const errorMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant' as const,
        content: `Desculpe, ocorreu um erro ao criar a vaga. Por favor, tente novamente.\n\nErro: ${error instanceof Error ? error.message : 'Erro desconhecido'}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const generateJobDescription = () => {
    const { basicInfoFields, technicalSkills, behavioralCompetencies, salaryInfo, companyConfig, setJobDescription, setIsGeneratingDescription } = ctx

    setIsGeneratingDescription(true)

    const skills = technicalSkills.slice(0, 5).map(s => s.name).join(', ')
    const competencies = behavioralCompetencies.filter(c => c.enabled).slice(0, 3).map(c => c.name).join(', ')
    const benefits = salaryInfo.benefits.filter(b => b.enabled).slice(0, 4).map(b => b.name).join(', ')

    const description = `Estamos em busca de um(a) ${basicInfoFields.cargo || 'profissional'} para integrar nossa equipe de ${basicInfoFields.area || 'alto desempenho'}.

📍 **Local:** ${basicInfoFields.localidade || 'A definir'} | ${basicInfoFields.modeloTrabalho || 'Flexível'}
📝 **Contrato:** ${basicInfoFields.tipoContrato || 'CLT'}

**O que você vai encontrar:**
• Oportunidade de crescimento em ambiente ${companyConfig?.values?.includes('inovação') ? 'inovador' : 'dinâmico'}
• Projetos desafiadores na área de ${basicInfoFields.area || 'tecnologia'}
${benefits ? `• Benefícios: ${benefits}` : '• Pacote de benefícios competitivo'}

**O que buscamos:**
${skills ? `• Experiência com: ${skills}` : '• Conhecimentos técnicos na área'}
${competencies ? `• Perfil: ${competencies}` : '• Profissional colaborativo e proativo'}
• Experiência compatível com a posição

${salaryInfo.minSalary && salaryInfo.maxSalary ? `💰 **Faixa salarial:** R$ ${salaryInfo.minSalary} - R$ ${salaryInfo.maxSalary}` : ''}

Venha fazer parte do nosso time! 🚀`

    setTimeout(() => {
      setJobDescription(description)
      setIsGeneratingDescription(false)
    }, 1200)
  }

  return {
    generateCriteriaResponse,
    generateParecerData,
    generateCompetencyAnalysisMessage,
    generateWSIExplanationMessage,
    handleAcceptSuggestions,
    handleSkipSuggestions,
    handleClearDraftAndReset,
    handlePublishJob,
    buildCandidateSearchQuery,
    generateJobDescription,
    startLocalSearch,
    startGlobalSearch,
  }
}
