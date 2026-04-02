"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { LIAIcon } from "@/components/ui/lia-icon"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { ProactiveInsightCard, type SearchAnalytics } from "@/components/proactive-insight-card"
import { CalibrationCard, type CalibrationCandidate } from "@/components/calibration-card"
import { ThinkingDots } from "@/components/ui/thinking-dots"
import {
  Brain, X, Globe, TrendingUp, Bookmark, Search, Home
} from "lucide-react"

interface ApiExperience {
  company_info?: { name?: string; location?: string; is_startup?: boolean }
  company_roles?: { title?: string; start_date?: string; end_date?: string; description?: string }[]
  company?: string
  title?: string
  start_date?: string
  end_date?: string
  duration?: string
  location?: string
  description?: string
}

interface ApiEducation {
  school?: string
  degree?: string
  field_of_study?: string
  start_date?: string
  end_date?: string
}

interface ApiCandidate {
  id?: string
  name?: string
  email?: string
  phone?: string
  headline?: string
  current_title?: string
  current_company?: string
  location?: string
  linkedin_url?: string
  avatar_url?: string
  picture_url?: string
  skills?: string[]
  seniority_level?: string
  years_experience?: number
  total_experience_years?: number
  match_score?: number
  source?: string
  has_email?: boolean
  has_phone?: boolean
  is_opentowork?: boolean
  is_decision_maker?: boolean
  is_top_universities?: boolean
  is_startup?: boolean
  company_info?: { is_startup?: boolean }
  expertise?: string
  outreach_message?: string
  experiences?: ApiExperience[]
  education?: ApiEducation[]
}

// Re-export for use in parent
export type { ApiCandidate, ApiExperience, ApiEducation }

type ChatMessage = {
  id: string
  type: 'user' | 'lia' | 'proactive_insight' | 'calibration'
  content: string
  timestamp: Date
  searchResults?: {
    localCount: number
    globalCount: number
    query: string
  }
  analytics?: SearchAnalytics
  candidates?: CalibrationCandidate[]
  metadata?: {
    action_executed?: boolean
    action_result?: Record<string, unknown>
    action_type?: string
    needs_confirmation?: boolean
    needs_params?: boolean
    pending_action_id?: string
    conversation_id?: string
  }
}

interface LIASearchSidebarChatProps {
  chatScrollRef: React.RefObject<HTMLDivElement>
  searchResults: {
    query: string
    isLoading: boolean
    localCount: number
    globalCount: number
    showGlobalResults: boolean
    globalDismissed: boolean
    local: unknown[]
    global: unknown[]
  }
  setSearchResults: React.Dispatch<React.SetStateAction<LIASearchSidebarChatProps['searchResults']>>
  currentSearchSource: string
  chatMessages: ChatMessage[]
  setShowSaveAsArchetypeModal: (v: boolean) => void
  setShowGlobalExpansionConfirm: (v: boolean) => void
  onQuickAction: (actionId: string, actionType: string) => void
  onCalibrationLike: (candidateId: string) => void
  onCalibrationDislike: (candidateId: string, reason?: string) => void
}

export function LIASearchSidebarChat({
  chatScrollRef,
  searchResults,
  setSearchResults,
  currentSearchSource,
  chatMessages,
  setShowSaveAsArchetypeModal,
  setShowGlobalExpansionConfirm,
  onQuickAction,
  onCalibrationLike,
  onCalibrationDislike,
}: LIASearchSidebarChatProps) {
  return (
    <div
      ref={chatScrollRef}
      className="flex-1 overflow-y-auto space-y-3 min-h-0"
    >
      {/* Resultado da Busca (como resposta da LIA) - PRIMEIRO cronologicamente */}
      {searchResults.query && (
        <div className="space-y-3">
          {/* Mensagem do usuário */}
          <div className="flex justify-end">
            <div className="max-w-[85%] p-3 rounded-md bg-gray-900 dark:bg-lia-btn-primary-bg text-white">
              <p className="text-xs">{searchResults.query}</p>
            </div>
          </div>

          {/* Resposta da LIA */}
          <div className="flex items-start gap-2">
            <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 bg-wedo-cyan/15">
              <LIAIcon size="xs" />
            </div>
            <div className="flex-1 space-y-3">
              {/* Resumo dos resultados */}
              <div className="p-3 rounded-md bg-white dark:bg-lia-bg-secondary">
                <p className="text-xs font-medium text-lia-text-primary mb-2">
                  Encontrei <span className="text-lia-text-secondary" aria-live="polite" aria-atomic="true">{searchResults.localCount + (searchResults.showGlobalResults ? searchResults.globalCount : 0)} candidato{(searchResults.localCount + (searchResults.showGlobalResults ? searchResults.globalCount : 0)) > 1 ? 's' : ''}</span> para sua busca:
                </p>
                <div className="flex items-center gap-3 text-xs mb-2">
                  {searchResults.localCount > 0 && (
                    <div className="flex items-center gap-1 text-status-success">
                      <Home className="w-3 h-3" />
                      <span className="font-medium">{searchResults.localCount} base local</span>
                    </div>
                  )}
                  {searchResults.showGlobalResults && searchResults.globalCount > 0 && (
                    <div className="flex items-center gap-1 text-lia-text-secondary">
                      <Globe className="w-3 h-3" />
                      <span className="font-medium">{searchResults.globalCount} busca global</span>
                    </div>
                  )}
                </div>
                <div className="flex items-center justify-between mt-2">
                  <p className="text-xs text-lia-text-primary flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    Ordenados por aderência ao perfil
                  </p>
                  <button
                    onClick={() => {
                      setShowSaveAsArchetypeModal(true)
                    }}
                    className="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border border-gray-900 dark:border-lia-border-medium text-lia-text-secondary hover:bg-gray-100 dark:bg-lia-bg-secondary transition-[width,height]"
                  >
                    <Bookmark className="w-3 h-3" />
                    Salvar Arquétipo
                  </button>
                </div>
              </div>

              {/* Candidatos locais na tabela */}
              {searchResults.localCount > 0 && (
                <div className="p-2.5 rounded-md bg-gray-50 dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
                  <div className="flex items-center gap-2">
                    <Home className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <p className="text-xs text-lia-text-primary">
                      <span className="font-semibold" aria-live="polite" aria-atomic="true">{searchResults.localCount} candidatos</span> da base local exibidos na tabela
                    </p>
                  </div>
                </div>
              )}

              {/* Botão para expandir busca para global - OPT-IN: só mostra após busca local */}
              {currentSearchSource === 'local' && !searchResults.showGlobalResults && !searchResults.globalDismissed && searchResults.query && (
                <div className="p-3 rounded-md border border-gray-900 dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-secondary">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-lia-text-secondary" />
                      <div>
                        <p className="text-xs font-medium text-wedo-cyan-dark dark:text-wedo-cyan-dark">
                          Expandir para Busca Global?
                        </p>
                        <p className="text-xs text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                          Acesse +800M de perfis (1 crédito/candidato)
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="!text-xs !px-2.5 !py-1.5 text-lia-text-primary hover:text-lia-text-primary hover:bg-gray-100 dark:hover:bg-gray-800"
                        onClick={() => {
                          setSearchResults(prev => ({ ...prev, globalDismissed: true }))
                        }}
                      >
                        <X className="w-3 h-3 mr-1" />
                        Manter local
                      </Button>
                      <Button
                        size="sm"
                        className="!text-xs !px-3 !py-1.5 bg-gray-900" style={{color: 'var(--gray-50)'}}
                        onClick={() => setShowGlobalExpansionConfirm(true)}
                      >
                        <Globe className="w-3 h-3 mr-1" />
                        Expandir Busca
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Mensagem quando usuário descartou busca global */}
              {currentSearchSource === 'local' && searchResults.globalDismissed && !searchResults.showGlobalResults && searchResults.query && (
                <div className="p-2.5 rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Globe className="w-3.5 h-3.5 text-lia-text-primary" />
                      <p className="text-xs text-lia-text-primary">
                        Busca global disponível
                      </p>
                    </div>
                    <button
                      onClick={() => setSearchResults(prev => ({ ...prev, globalDismissed: false }))}
                      className="text-xs text-lia-text-secondary hover:text-lia-text-primary hover:underline"
                    >
                      Expandir busca
                    </button>
                  </div>
                </div>
              )}

              {/* Confirmação de candidatos globais adicionados */}
              {searchResults.showGlobalResults && searchResults.globalCount > 0 && (
                <div className="p-2.5 rounded-md bg-gray-50 dark:bg-lia-bg-secondary border border-gray-900 dark:border-lia-border-subtle">
                  <div className="flex items-center gap-2">
                    <Globe className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <p className="text-xs text-wedo-cyan-dark">
                      <span className="font-semibold" aria-live="polite" aria-atomic="true">{searchResults.globalCount} candidatos</span> globais adicionados à tabela
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Loading - LIA Buscando */}
      {searchResults.isLoading && (
        <div className="space-y-3">
          {/* Mensagem do usuário (query atual) */}
          {searchResults.query && (
            <div className="flex justify-end">
              <div className="max-w-[85%] p-3 rounded-md bg-gray-900 dark:bg-lia-btn-primary-bg text-white">
                <p className="text-xs">{searchResults.query}</p>
              </div>
            </div>
          )}

          {/* LIA Pensando */}
          <div className="flex items-start gap-2">
            <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 animate-pulse motion-reduce:animate-none bg-wedo-cyan/20">
              <LIAIcon size="xs" />
            </div>
            <div className="flex-1 space-y-2">
              {/* Card de status */}
              <div className="p-4 rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50">
                <div className="flex items-center gap-3 mb-3">
                  <div className="relative">
                    <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center">
                      <Search className="w-4 h-4 text-lia-text-secondary animate-pulse motion-reduce:animate-none" />
                    </div>
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-gray-900 dark:bg-lia-btn-primary-bg rounded-full animate-ping motion-reduce:animate-none" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-lia-text-primary">
                      LIA está buscando...
                    </p>
                    <p className="text-xs text-lia-text-primary">
                      Analisando perfis compatíveis
                    </p>
                  </div>
                </div>

                {/* Progress steps */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs text-lia-text-primary">
                    <div className="w-4 h-4 rounded-full bg-status-success flex items-center justify-center">
                      <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <span>Interpretando critérios</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-lia-text-primary" role="status" aria-live="polite" aria-label="Carregando...">
                    <div className="w-4 h-4 rounded-full bg-gray-900 dark:bg-lia-btn-primary-bg flex items-center justify-center animate-spin motion-reduce:animate-none" role="status" aria-live="polite" aria-label="Carregando...">
                      <div className="w-2 h-2 border border-white border-t-transparent rounded-full" />
                    </div>
                    <span aria-live="polite" aria-atomic="true">Buscando na base de candidatos</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-lia-text-primary">
                    <div className="w-4 h-4 rounded-full bg-gray-200 dark:bg-lia-bg-elevated" />
                    <span>Rankeando por compatibilidade</span>
                  </div>
                </div>
              </div>

              {/* Typing indicator */}
              <div className="flex items-center gap-1.5 px-3 py-2">
                <div className="flex gap-1">
                  <ThinkingDots dotClassName="bg-gray-900 dark:bg-lia-btn-primary-bg" size="lg" />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mensagens do Chat - DEPOIS dos resultados da busca (ordem cronológica) */}
      {chatMessages.map((msg) => (
        <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
          {msg.type === 'user' ? (
            /* User Message - Alinhado à direita, balão cinza claro com avatar */
            <div className="flex items-start gap-2 max-w-[70%]">
              <img
                src="https://randomuser.me/api/portraits/men/32.jpg"
                alt="Você"
                className="w-7 h-7 rounded-full object-cover flex-shrink-0"
              />
              <div
                className="px-2.5 py-2 rounded-md bg-gray-100"
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className="text-micro font-bold text-lia-text-primary">Você</span>
                  <span className="text-micro text-lia-text-tertiary">agora</span>
                </div>
                <p className="text-xs text-lia-text-primary leading-relaxed">{msg.content}</p>
              </div>
            </div>
          ) : msg.type === 'proactive_insight' && msg.analytics ? (
            <div className="w-full">
              <ProactiveInsightCard
                analytics={msg.analytics}
                onAction={onQuickAction}
                isExpanded={false}
              />
            </div>
          ) : msg.type === 'calibration' && msg.candidates ? (
            <div className="w-full space-y-3">
              <div className="flex items-start gap-2">
                <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 bg-wedo-cyan/15">
                  <LIAIcon size="xs" />
                </div>
                <p className="text-xs text-lia-text-primary" aria-live="polite" aria-atomic="true">
                  Vou mostrar alguns candidatos para entender melhor o perfil que você busca:
                </p>
              </div>
              <div className="space-y-2 pl-8">
                {msg.candidates.map(candidate => (
                  <CalibrationCard
                    key={candidate.id}
                    candidate={candidate}
                    onLike={onCalibrationLike}
                    onDislike={onCalibrationDislike}
                  />
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-[90%]">
              <div className="flex items-start gap-2">
                <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0">
                  <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
                </div>
                <div className="flex-1">
                  <span className="text-micro font-bold text-lia-text-primary" >LIA</span>
                  <p className="text-xs text-lia-text-primary leading-relaxed whitespace-pre-wrap mt-0.5">
                    {msg.content.split(/(\*\*[^*]+\*\*)/).map((part, i) =>
                      part.startsWith('**') && part.endsWith('**')
                        ? <strong key={i}>{part.slice(2, -2)}</strong>
                        : part
                    )}
                  </p>
                  {msg.metadata?.action_executed && msg.metadata?.action_result && (
                    <ActionResultCard
                      actionType={msg.metadata.action_type || 'analyze_profile'}
                      result={msg.metadata.action_result}
                    />
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
