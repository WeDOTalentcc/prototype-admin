"use client"

import React from"react"
import { Chip } from "@/components/ui/chip"
import { LIAIcon } from"@/components/ui/lia-icon"

// --- Workflow context types (E.6) ---

export type WorkflowContext =
  | 'vacancy_published'
  | 'candidate_approved'
  | 'wizard_active'
  | 'idle'

interface ContextSuggestionItem {
  icon: string
  label: string
  prompt: string
}

const CONTEXT_SUGGESTIONS: Record<WorkflowContext, ContextSuggestionItem[]> = {
  vacancy_published: [
    { icon: '🎯', label: 'Calibrar busca', prompt: 'Quero calibrar a busca de candidatos' },
    { icon: '🔍', label: 'Iniciar triagem', prompt: 'Vamos iniciar a triagem dos candidatos' },
    { icon: '👥', label: 'Escolher entrevistadores', prompt: 'Quero definir os entrevistadores' },
    { icon: '🔗', label: 'Compartilhar vaga', prompt: 'Como compartilho o link da vaga?' },
  ],
  candidate_approved: [
    { icon: '📅', label: 'Agendar entrevista', prompt: 'Agendar entrevista para esse candidato' },
    { icon: '📋', label: 'Gerar plano', prompt: 'Gerar plano de entrevista' },
  ],
  wizard_active: [
    { icon: '⚡', label: 'Preencher rápido', prompt: 'Preencher os campos restantes automaticamente' },
    { icon: '👁️', label: 'Ver progresso', prompt: 'Mostrar o progresso da vaga' },
  ],
  idle: [],
}

// --- Existing types ---

interface SavedTemplate {
  id: string
  name: string
  usageCount?: number
  [key: string]: unknown
}

interface CandidateContext {
  name?: string
  liaAnalysis?: { score?: number }
  score?: number
  [key: string]: unknown
}

interface SuggestionItem {
  id: string
  icon: string
  label: string
  description: string
  action: string
  category?: string
  isTemplate?: boolean
  template?: SavedTemplate
}

interface PromptSuggestionsPanelProps {
  selectedCandidates: CandidateContext[]
  candidateContext: CandidateContext | null
  savedTemplates: SavedTemplate[]
  suggestions: SuggestionItem[]
  isProcessing: boolean
  commandHistory: string[]
  showHistory: boolean
  setShowHistory: (val: boolean) => void
  onSuggestionClick: (suggestion: SuggestionItem) => void
  onHistoryCommand: (command: string) => void
  /** E.6: optional context that overrides default suggestions with contextual chips */
  workflowContext?: WorkflowContext
  /** E.6: callback when a contextual chip is clicked (sends the prompt) */
  onContextPromptClick?: (prompt: string) => void
}

export function getSmartSuggestions(
  candidateContext: CandidateContext | null,
  selectedCandidates: CandidateContext[],
  savedTemplates: SavedTemplate[]
): SuggestionItem[] {
  if (candidateContext) {
    return [
      {
        id: 'analyze_profile',
        icon: '🔍',
        label: `Analisar perfil completo de ${candidateContext.name}`,
        description: 'Análise detalhada de competências, aderência cultural e potencial',
        action: 'analyze_individual_profile'
      },
      {
        id: 'generate_interview_questions',
        icon: '❓',
        label: 'Gerar roteiro de entrevista personalizado',
        description: 'Perguntas técnicas e comportamentais baseadas no perfil',
        action: 'generate_interview_questions'
      },
      {
        id: 'draft_email',
        icon: '📧',
        label: 'Rascunhar convite personalizado',
        description: 'Email de convite customizado para o candidato',
        action: 'draft_personalized_email'
      },
      {
        id: 'compare_with_role',
        icon: '⚖️',
        label: 'Comparar com requisitos da vaga',
        description: 'Match detalhado com job description',
        action: 'compare_with_job_requirements'
      },
      {
        id: 'predict_success',
        icon: '🎯',
        label: 'Predizer sucesso na posição',
        description: 'Análise preditiva baseada em dados históricos',
        action: 'predict_candidate_success'
      },
      {
        id: 'salary_benchmark',
        icon: '💰',
        label: 'Benchmark salarial personalizado',
        description: 'Comparação com mercado baseada no perfil específico',
        action: 'salary_benchmark'
      }
    ]
  }

  const selectedCount = selectedCandidates.length
  const allSuggestions: SuggestionItem[] = []

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
    const advancedSuggestions: SuggestionItem[] = [
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
    const candidateName = candidate.name || 'Candidato'
    const candidateScore = candidate.liaAnalysis?.score || candidate.score || 0
    const individualSuggestions: SuggestionItem[] = [
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

  const batchSuggestions: SuggestionItem[] = [
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

export function PromptSuggestionsPanel({
  suggestions,
  isProcessing,
  commandHistory,
  showHistory,
  setShowHistory,
  onSuggestionClick,
  onHistoryCommand,
  workflowContext,
  onContextPromptClick,
}: PromptSuggestionsPanelProps) {
  // E.6: When workflowContext is provided and non-idle, show contextual chips
  const contextChips =
    workflowContext && workflowContext !== 'idle'
      ? CONTEXT_SUGGESTIONS[workflowContext]
      : []
  const showContextChips = contextChips.length > 0

  if (showContextChips) {
    return (
      <div className="px-4 pb-0">
        <div className="flex items-center gap-2 mb-3">
          <LIAIcon size="sm" />
          <span className="text-sm font-medium text-lia-text-primary">💡 Sugestões</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {contextChips.map((chip) => (
            <button
              key={chip.prompt}
              type="button"
              onClick={() => onContextPromptClick?.(chip.prompt)}
              disabled={isProcessing}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-lia-border-subtle bg-lia-bg-primary text-sm font-medium text-lia-text-primary transition-colors motion-reduce:transition-none ${
                isProcessing
                  ? 'opacity-50 cursor-not-allowed'
                  : 'hover:border-lia-border-medium hover:bg-lia-bg-secondary'
              }`}
            >
              <span aria-hidden="true">{chip.icon}</span>
              {chip.label}
            </button>
          ))}
        </div>
      </div>
    )
  }

  // Default (original) behavior when no workflowContext or idle
  return (
    <div className="px-4 pb-0">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <LIAIcon size="sm" />
          <span className="text-sm font-medium text-lia-text-primary">💡 Sugestões Inteligentes</span>
          <Chip density="relaxed" variant="neutral" >
            {suggestions.length} disponíveis
          </Chip>
        </div>

        {commandHistory.length > 0 && (
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="text-xs text-lia-text-secondary hover:text-lia-text-secondary flex items-center gap-1 transition-colors motion-reduce:transition-none"
          >
            📜 Histórico ({commandHistory.length})
          </button>
        )}
      </div>

      {showHistory && commandHistory.length > 0 && (
        <div className="mb-4 p-3 bg-lia-bg-secondary rounded-xl border">
          <h4 className="text-xs font-medium text-lia-text-primary mb-2">Comandos Recentes</h4>
          <div className="space-y-1">
            {commandHistory.map((command, index) => (
              <button
                key={`hist-${index}`}
                onClick={() => onHistoryCommand(command)}
                disabled={isProcessing}
                className={`w-full text-left text-xs p-2 rounded-md hover:bg-lia-bg-primary transition-colors motion-reduce:transition-none ${
 isProcessing ? 'opacity-50' : 'text-lia-text-secondary hover:text-lia-text-primary'
                }`}
              >
                📝 {command}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion.id}
            onClick={() => onSuggestionClick(suggestion)}
            disabled={isProcessing}
            className={`flex items-start gap-3 p-3 text-left rounded-md border border-lia-border-subtle bg-lia-bg-primary transition-colors motion-reduce:transition-none group ${
 isProcessing
                ? 'opacity-50 cursor-not-allowed'
                : 'hover:border-lia-border-medium hover:'
            }`}
          >
            <span className="text-lg flex-shrink-0">{suggestion.icon}</span>
            <div className="flex-1">
              <div className="text-base-ui font-semibold text-lia-text-primary group-hover:text-lia-text-secondary">
                {suggestion.label}
              </div>
              <div className="text-xs text-lia-text-secondary mt-1">
                {suggestion.description}
              </div>
              {suggestion.category && (
                <Chip variant="neutral" muted className="mt-2 text-micro bg-lia-bg-tertiary text-lia-text-primary border-0">
                  {suggestion.category}
                </Chip>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
