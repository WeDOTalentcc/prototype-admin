"use client"

import React, { useCallback } from "react"
import type { FileAnalysisResult } from "@/components/ui/file-upload-button"
import { toast } from "sonner"
import { useChatStateStore } from "@/stores/chat-state-store"
import type {
  ArchetypeData,
  UseEAPCallbacksParams,
} from './useEAPCallbacksTypes'

export function useEAPCommandCallbacks(params: UseEAPCallbacksParams) {
  const {
    parseEntitiesFromQuery,
    candidateContext,
    selectedCandidates,
    savedTemplates,
    filteredCount,
    totalCount,
    inputValue,
    isProcessing,
    onCommand,
    templateSuggestions,
    suggestionQueue,
    setNaturalSearchValue,
    setShowPremiumAutocomplete,
    setIsProcessing,
    setLastCommand,
    setCommandHistory,
    setInputValue,
    setIsExpanded,
    setShowHistory,
    setArchetypes,
  } = params

  const handleFileAnalyzed = useCallback((file: File, analysis: FileAnalysisResult) => {
    if (analysis.success) {
      const keywords: string[] = []
      if (analysis.keywords && analysis.keywords.length > 0) {
        keywords.push(...analysis.keywords.slice(0, 5))
      }
      if (analysis.entities) {
        if (analysis.entities.skills) keywords.push(...analysis.entities.skills.slice(0, 3))
        if (analysis.entities.job_titles) keywords.push(...analysis.entities.job_titles.slice(0, 2))
        if (analysis.entities.locations) keywords.push(...analysis.entities.locations.slice(0, 2))
      }
      const uniqueKeywords = [...new Set(keywords)]
      if (uniqueKeywords.length > 0) {
        const searchText = uniqueKeywords.join(', ')
        setNaturalSearchValue(prev => prev ? `${prev}, ${searchText}` : searchText)
        parseEntitiesFromQuery(searchText)
        toast.info("Arquivo analisado", { description: `Extraídos ${uniqueKeywords.length} critérios de ${file.name}` })
      } else {
        toast.info("Arquivo processado", { description: `${file.name} foi analisado mas não foram encontrados critérios de busca` })
      }
    } else {
      toast.error("Erro na análise", { description: analysis.error || "Não foi possível analisar o arquivo" })
    }
  }, [parseEntitiesFromQuery, setNaturalSearchValue])

  const handleAudioTranscription = useCallback((text: string) => {
    if (text && text.trim()) {
      setNaturalSearchValue(prev => {
        const newValue = prev ? `${prev} ${text.trim()}` : text.trim()
        parseEntitiesFromQuery(newValue)
        return newValue
      })
      setShowPremiumAutocomplete(true)
      toast.info("Transcrição concluída", { description: "Texto adicionado à busca" })
    }
  }, [parseEntitiesFromQuery, setNaturalSearchValue, setShowPremiumAutocomplete])

  const handlePremiumAutocompleteSelect = useCallback((suggestion: string) => {
    setNaturalSearchValue(suggestion)
    setShowPremiumAutocomplete(false)
    parseEntitiesFromQuery(suggestion)
  }, [parseEntitiesFromQuery, setNaturalSearchValue, setShowPremiumAutocomplete])

  const getAdvancedFilters = () => {
    return {
      selectedCandidates: selectedCandidates.length,
      contextType: 'candidates',
      filteredCount,
      totalCount
    }
  }

  const checkForTemplateSuggestions = () => {
    const pendingSuggestions = (templateSuggestions as Record<string, (...args: unknown[]) => unknown>).getPendingSuggestions() as Array<Record<string, unknown>>
    pendingSuggestions.forEach(suggestion => {
      if ((templateSuggestions as Record<string, (...args: unknown[]) => boolean>).shouldShowSuggestion(suggestion)) {
        (suggestionQueue as Record<string, (...args: unknown[]) => void>).addSuggestion(suggestion)
        ;(templateSuggestions as Record<string, (...args: unknown[]) => void>).markSuggestionAsShown(suggestion.id)
      }
    })
  }

  const { liaTemplates, setLiaTemplates } = useChatStateStore()

  const executeTemplate = (template: Record<string, unknown>) => {
    const updatedTemplates = liaTemplates.map((t: Record<string, unknown>) =>
      t.id === template.id
        ? { ...t, usageCount: (t.usageCount as number) + 1, updatedAt: new Date() }
        : t
    )
    setLiaTemplates(updatedTemplates)

    setTimeout(() => {
      onCommand(template.command as string, (template.actions as string[])[0] || 'execute_template')
      setIsExpanded(false)
      setIsProcessing(false)
    }, 1000)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputValue.trim() && !isProcessing) {
      setIsProcessing(true)
      setLastCommand(inputValue)

      ;(templateSuggestions as Record<string, (...args: unknown[]) => void>).addCommand(inputValue, getAdvancedFilters(), ['text_command'])

      setCommandHistory(prev => [inputValue, ...prev.slice(0, 4)])

      setTimeout(() => {
        onCommand(inputValue, 'text_command')
        setInputValue("")
        setIsExpanded(false)
        setIsProcessing(false)
        checkForTemplateSuggestions()
      }, 1500)
    }
  }

  const handleSuggestionClick = (suggestion: Record<string, unknown>) => {
    if (!isProcessing) {
      setIsProcessing(true)
      setLastCommand(suggestion.label as string)

      if (suggestion.isTemplate) {
        executeTemplate(suggestion.template as Record<string, unknown>)
        return
      }

      ;(templateSuggestions as Record<string, (...args: unknown[]) => void>).addCommand(suggestion.label as string, getAdvancedFilters(), [suggestion.action])

      setCommandHistory(prev => [suggestion.label as string, ...prev.slice(0, 4)])

      setTimeout(() => {
        onCommand(suggestion.label as string, suggestion.action as string)
        setIsExpanded(false)
        setIsProcessing(false)
        checkForTemplateSuggestions()
      }, 1200)
    }
  }

  const handleArchetypeSaved = (newArchetype: ArchetypeData) => {
    setArchetypes(prev => [...prev, newArchetype])
    toast.success("Arquétipo salvo", { description: `"${newArchetype.name}" foi adicionado aos seus arquétipos.` })
  }

  const handleHistoryCommand = (command: string) => {
    setInputValue(command)
    setShowHistory(false)
  }

  const getSmartSuggestions = () => {
    if (candidateContext) {
      return [
        { id: 'analyze_profile', icon: '🔍', label: `Analisar perfil completo de ${(candidateContext as Record<string, unknown>).name}`, description: 'Análise detalhada de competências, aderência cultural e potencial', action: 'analyze_individual_profile' },
        { id: 'generate_interview_questions', icon: '❓', label: 'Gerar roteiro de entrevista personalizado', description: 'Perguntas técnicas e comportamentais baseadas no perfil', action: 'generate_interview_questions' },
        { id: 'draft_email', icon: '📧', label: 'Rascunhar convite personalizado', description: 'Email de convite customizado para o candidato', action: 'draft_personalized_email' },
        { id: 'compare_with_role', icon: '⚖️', label: 'Comparar com requisitos da vaga', description: 'Match detalhado com job description', action: 'compare_with_job_requirements' },
        { id: 'predict_success', icon: '🎯', label: 'Predizer sucesso na posição', description: 'Análise preditiva baseada em dados históricos', action: 'predict_candidate_success' },
        { id: 'salary_benchmark', icon: '💰', label: 'Benchmark salarial personalizado', description: 'Comparação com mercado baseada no perfil específico', action: 'salary_benchmark' }
      ]
    }

    const selectedCount = selectedCandidates.length
    const allSuggestions: Array<Record<string, unknown>> = []

    if (selectedCount === 0 && savedTemplates.length > 0) {
      allSuggestions.push(...savedTemplates.map(template => ({
        id: `template-${template.id}`,
        icon: '🔖',
        label: template.name,
        description: `Template salvo • ${template.usageCount} usos`,
        action: 'execute_template',
        template: template,
        isTemplate: true
      })))
    }

    if (selectedCount === 0) {
      const advancedSuggestions = [
        { id: 'smart_search_ai', icon: '🧠', label: 'Busca inteligente com IA', description: 'Descreva o perfil ideal e a IA encontra candidatos similares', action: 'ai_smart_search', category: 'search' },
        { id: 'boolean_search_expert', icon: '🔧', label: 'Busca booleana avançada', description: 'Construtor visual de queries complexas para LinkedIn/Github', action: 'boolean_search_builder', category: 'search' },
        { id: 'passive_candidates', icon: '🕵️', label: 'Identificar candidatos passivos', description: 'Encontrar talentos que não estão procurando ativamente', action: 'find_passive_candidates', category: 'search' },
        { id: 'competitor_analysis', icon: '🏢', label: 'Mapear concorrentes e talentos', description: 'Análise de empresas similares e seus melhores profissionais', action: 'competitor_talent_mapping', category: 'search' },
        { id: 'pipeline_automation', icon: '⚙️', label: 'Automatizar pipeline de talentos', description: 'Configurar fluxos automáticos para diferentes perfis', action: 'setup_pipeline_automation', category: 'automation' },
        { id: 'email_sequences', icon: '📬', label: 'Sequências de email inteligentes', description: 'Campanhas de nurturing personalizadas por segmento', action: 'create_email_sequences', category: 'automation' },
        { id: 'calendar_optimization', icon: '📅', label: 'Otimizar agenda de entrevistas', description: 'Sugerir melhor organização e horários mais eficientes', action: 'optimize_interview_calendar', category: 'automation' },
        { id: 'market_trends', icon: '📈', label: 'Análise de tendências do mercado', description: 'Insights sobre salários, demanda e escassez de talentos', action: 'analyze_market_trends', category: 'analytics' },
        { id: 'diversity_analysis', icon: '🌈', label: 'Análise de diversidade e inclusão', description: 'Métricas D&I e sugestões para melhorar representatividade', action: 'diversity_inclusion_analysis', category: 'analytics' },
        { id: 'conversion_funnels', icon: '🎯', label: 'Análise de funis de conversão', description: 'Identificar gargalos e oportunidades de melhoria', action: 'analyze_conversion_funnels', category: 'analytics' },
        { id: 'predictive_hiring', icon: '🔮', label: 'Previsões de contratação', description: 'Predizer necessidades futuras baseado em crescimento', action: 'predictive_hiring_analysis', category: 'analytics' },
        { id: 'interview_scorecards', icon: '📋', label: 'Criar scorecards de entrevista', description: 'Formulários estruturados para avaliação consistente', action: 'create_interview_scorecards', category: 'tools' },
        { id: 'reference_automation', icon: '📞', label: 'Automatizar checagem de referências', description: 'Templates e fluxos para verificação de background', action: 'automate_reference_checks', category: 'tools' },
        { id: 'onboarding_preparation', icon: '🎯', label: 'Preparar onboarding personalizado', description: 'Planos customizados baseados no perfil do novo hire', action: 'prepare_custom_onboarding', category: 'tools' },
        { id: 'salary_intelligence', icon: '💎', label: 'Inteligência salarial avançada', description: 'Benchmarks detalhados por região, experiência e skills', action: 'advanced_salary_intelligence', category: 'intelligence' },
        { id: 'skill_gap_analysis', icon: '🔍', label: 'Análise de lacunas de habilidades', description: 'Identificar skills em falta no time e no mercado', action: 'skill_gap_analysis', category: 'intelligence' },
        { id: 'employer_branding', icon: '✨', label: 'Otimizar employer branding', description: 'Sugestões para melhorar atratividade da empresa', action: 'optimize_employer_branding', category: 'intelligence' }
      ]

      const shuffled = advancedSuggestions.sort(() => 0.5 - Math.random())
      allSuggestions.push(...shuffled.slice(0, 10))
      return allSuggestions
    }

    if (selectedCount === 1) {
      const candidate = selectedCandidates[0]
      const candidateName = (candidate.name as string) || 'Candidato'
      const candidateScore = ((candidate.liaAnalysis as Record<string, unknown>)?.score as number) || (candidate.score as number) || 0

      const individualSuggestions = [
        { id: 'send_personalized_email', icon: '📧', label: `Enviar convite personalizado para ${candidateName}`, description: 'Email customizado baseado no perfil e interesses', action: 'send_personalized_email' },
        { id: 'schedule_interview', icon: '📅', label: 'Agendar entrevista estratégica', description: 'Escolher melhor horário e formato baseado no perfil', action: 'schedule_strategic_interview' },
        { id: 'deep_profile_analysis', icon: '🔬', label: 'Análise profunda do perfil', description: 'Investigação completa de competências e aderência cultural', action: 'deep_profile_analysis' },
        { id: 'salary_negotiation_prep', icon: '💰', label: 'Preparar negociação salarial', description: 'Estratégia e faixas baseadas no perfil específico', action: 'prepare_salary_negotiation' },
        { id: 'reference_check_strategy', icon: '📋', label: 'Estratégia de referências', description: 'Plano para checagem de background e referências', action: 'plan_reference_checks' },
        { id: 'competitor_intel', icon: '🕵️', label: 'Intel sobre empresa atual', description: 'Pesquisa sobre empresa e possíveis motivadores', action: 'research_current_company' }
      ]

      if (candidateScore >= 85) {
        individualSuggestions.push({ id: 'fast_track_vip', icon: '⚡', label: 'Fast-track VIP', description: 'Processo acelerado para candidato excepcional', action: 'vip_fast_track' })
      }

      if (candidateScore < 70) {
        individualSuggestions.push({ id: 'improvement_coaching', icon: '📚', label: 'Coaching para candidato', description: 'Sugestões de desenvolvimento para melhorar fit', action: 'candidate_coaching_suggestions' })
      }

      return individualSuggestions
    }

    const batchSuggestions = [
      { id: 'bulk_email_campaign', icon: '📧', label: `Campanha de email para ${selectedCount} candidatos`, description: 'Emails personalizados em massa com A/B testing', action: 'bulk_email_campaign' },
      { id: 'comparative_analysis', icon: '📊', label: `Análise comparativa detalhada`, description: 'Relatório completo comparando perfis selecionados', action: 'detailed_comparative_analysis' },
      { id: 'interview_coordination', icon: '🗓️', label: 'Coordenar entrevistas em lote', description: 'Otimizar agenda para múltiplas entrevistas', action: 'coordinate_batch_interviews' },
      { id: 'shortlist_creation', icon: '⭐', label: 'Criar shortlist inteligente', description: 'Ranking automático baseado em critérios específicos', action: 'create_intelligent_shortlist' },
      { id: 'diversity_check', icon: '🌈', label: 'Verificar diversidade do grupo', description: 'Análise D&I do conjunto de candidatos selecionados', action: 'check_group_diversity' },
      { id: 'salary_range_analysis', icon: '💰', label: 'Análise de faixas salariais', description: 'Comparar expectativas e definir estratégia de ofertas', action: 'analyze_salary_ranges' },
      { id: 'rejection_management', icon: '💔', label: 'Gestão inteligente de rejeições', description: 'Feedback personalizado e manutenção de relacionamento', action: 'manage_intelligent_rejections' }
    ]

    return batchSuggestions
  }

  const getPlaceholder = () => {
    if (candidateContext) {
      return `O que gostaria de fazer com ${(candidateContext as Record<string, unknown>).name}? Ex: analisar perfil, enviar email, agendar entrevista, comparar com outros...`
    }

    const selectedCount = selectedCandidates.length

    if (selectedCount === 0) {
      return "Peça à LIA para filtrar candidatos, fazer buscas específicas, analisar perfis, enviar emails, agendar entrevistas, comparar candidatos..."
    }

    if (selectedCount === 1) {
      return `O que fazer com ${(selectedCandidates[0] as Record<string, unknown>).name}?`
    }

    return `${selectedCount} candidatos selecionados. Como proceder?`
  }

  return {
    handleFileAnalyzed,
    handleAudioTranscription,
    handlePremiumAutocompleteSelect,
    handleSubmit,
    handleSuggestionClick,
    handleArchetypeSaved,
    handleHistoryCommand,
    getSmartSuggestions,
    getPlaceholder,
  }
}
