"use client"

import type {
  TechnicalSkill,
  BehavioralCompetency,
} from "../ExpandedChatContext"
import type { WizardPublishHandlersContext } from "./wizardPublishHandlers.types"
import { generateCriteriaResponse, generateCompetencyAnalysisMessage, generateWSIExplanationMessage } from "./useWizardMessageGenerators"
import { useWizardParecerData } from "./useWizardParecerData"
import { useWizardJobPublisher } from "./useWizardJobPublisher"

export type { WizardPublishHandlersContext } from "./wizardPublishHandlers.types"

export function useWizardPublishHandlers(ctx: WizardPublishHandlersContext) {
  const { generateParecerData } = useWizardParecerData(ctx)
  const {
    handlePublishJob,
    buildCandidateSearchQuery,
    generateJobDescription,
    startLocalSearch,
    startGlobalSearch,
  } = useWizardJobPublisher(ctx)

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
