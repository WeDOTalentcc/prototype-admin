"use client"

import React from "react"
import { Brain, Send, Paperclip, Loader2, FileText, Target, Search, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { VoiceChatButton } from "@/components/chat/voice-chat-button"
import { LiaVacancyQueriesGuide } from "@/components/ui/lia-vacancy-queries-guide"
import { cn } from "@/lib/utils"
import { DRAFT_DETECTED_MESSAGE, INITIAL_JOB_CREATION_MESSAGE } from '../config'
import type { Message, WizardDraftData } from '../types'

// ─── WizardGreeting type (mirrors the state in the parent modal) ───────────────
export interface WizardGreeting {
  greeting_message: string
  catalog_status: {
    company_id: string
    maturity_score: number
    maturity_level: 'complete' | 'partial' | 'minimal'
    maturity_factors: string[]
    smart_start_enabled: boolean
    required_fields_for_wizard: string[]
    available_data_summary: string[]
    counts: Record<string, number>
    recommendations: string[]
  }
  prefill_data: Record<string, unknown>
}

// ─── Props ────────────────────────────────────────────────────────────────────
export interface ExpandedChatInputProps {
  // Values
  inputValue: string
  isLoading: boolean
  isTypingEffect: boolean
  hideModeButtons: boolean
  activeInputTab: 'ia-natural' | 'job-description' | 'templates'
  conversationId: string | null
  showMoreIdeas: boolean
  wizardGreeting: WizardGreeting | null

  // Refs
  inputRef: React.RefObject<HTMLInputElement | null>
  fileInputRef: React.RefObject<HTMLInputElement | null>
  extractCriteriaDebounceRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>

  // Functions
  extractCriteriaFromText: (text: string) => void
  checkForExistingDraftSync: () => { hasDraft: boolean; stageName: string | null; draftData: Partial<WizardDraftData> | null }
  checkForExistingDraftFromBackend?: () => Promise<{ hasDraft: boolean; stageName: string | null; draftData: Partial<WizardDraftData> | null }>
  typeText: (text: string, messageId: string) => void

  // Callbacks (on* naming — Bridge React→Vue)
  onInputValueChange: (value: string) => void
  onKeyDown: (e: React.KeyboardEvent) => void
  onSendMessage: (content: string) => void
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
  onVoiceTranscription: (text: string) => void
  onVoiceResponse: (response: { text: string; audio?: string }) => void
  onVoiceError: (error: string) => void
  onSetActiveInputTab: (tab: 'ia-natural' | 'job-description' | 'templates') => void
  onSetMessages: React.Dispatch<React.SetStateAction<Message[]>>
  onSetInputValue: React.Dispatch<React.SetStateAction<string>>
  onSetShowMoreIdeas: (val: boolean) => void
  onSetDisplayedText: (text: string) => void
  onSetInternalJobCreationMode: (val: boolean) => void
  onSetPendingDraftData: (data: Partial<WizardDraftData> | null) => void
  onSetAwaitingDraftChoice: (val: boolean) => void
  onSetDynamicInitialMessage: (msg: string | null) => void
}

// ─── Component ────────────────────────────────────────────────────────────────
export function ExpandedChatInput({
  inputValue,
  isLoading,
  isTypingEffect,
  hideModeButtons,
  activeInputTab,
  conversationId,
  showMoreIdeas,
  wizardGreeting,
  inputRef,
  fileInputRef,
  extractCriteriaDebounceRef,
  extractCriteriaFromText,
  checkForExistingDraftSync,
  checkForExistingDraftFromBackend,
  typeText,
  onInputValueChange,
  onKeyDown,
  onSendMessage,
  onFileSelect,
  onVoiceTranscription,
  onVoiceResponse,
  onVoiceError,
  onSetActiveInputTab,
  onSetMessages,
  onSetInputValue,
  onSetShowMoreIdeas,
  onSetDisplayedText,
  onSetInternalJobCreationMode,
  onSetPendingDraftData,
  onSetAwaitingDraftChoice,
  onSetDynamicInitialMessage,
}: ExpandedChatInputProps) {
  const suggestionTags = [
    { label: "Criar vaga", icon: Plus, action: "criar_vaga" },
    { label: "Sugerir melhorias", icon: Brain, action: "sugerir_melhorias" },
  ]

  return (
    <div className="px-4 py-4 flex-shrink-0 bg-lia-bg-primary mt-auto">
      <div className="flex justify-center">
        <div className="w-full max-w-lg">
          <div className="flex items-center gap-2 px-3 py-2 bg-lia-bg-primary border border-lia-border-subtle rounded-full">
            <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center">
              <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
            </div>
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => {
                onInputValueChange(e.target.value)
                if (extractCriteriaDebounceRef.current) {
                  clearTimeout(extractCriteriaDebounceRef.current)
                }
                extractCriteriaDebounceRef.current = setTimeout(() => {
                  extractCriteriaFromText(e.target.value)
                }, 600)
              }}
              onKeyDown={onKeyDown}
              placeholder="Envie mensagem para a LIA..."
              data-testid="chat-input"
              aria-label="Digite sua mensagem para a LIA"
              aria-describedby="chat-input-hint"
              className="flex-1 py-1 bg-transparent text-base-ui text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none"
              disabled={isLoading || isTypingEffect}
            />
            <span id="chat-input-hint" className="sr-only">Pressione Enter para enviar a mensagem</span>

            <div className="flex items-center gap-1">
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,application/pdf,.doc,.docx"
                  onChange={onFileSelect}
                  className="hidden"
                />
                <button
                  className="p-1.5 text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary transition-colors motion-reduce:transition-none rounded-full"
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  title="Anexar arquivo para análise"
                  aria-label="Anexar arquivo para análise"
                >
                  <Paperclip className="w-4 h-4" aria-hidden="true" />
                </button>
              </>
              <VoiceChatButton
                sessionId={conversationId || undefined}
                onTranscription={(text) => {
                  onVoiceTranscription(text)
                }}
                onResponse={onVoiceResponse}
                onError={(error) => {
                  const errorMsg: Message = {
                    id: `voice-error-${Date.now()}`,
                    role: 'assistant',
                    content: `⚠️ ${error}`,
                    timestamp: new Date()
                  }
                  onSetMessages(prev => [...prev, errorMsg])
                }}
                disabled={isLoading || isTypingEffect}
              />
              <button
                onClick={() => onSendMessage(inputValue)}
                disabled={!inputValue.trim() || isLoading || isTypingEffect}
                aria-label="Enviar mensagem"
                aria-disabled={!inputValue.trim() || isLoading || isTypingEffect}
                className={cn(
 "w-8 h-8 rounded-full flex items-center justify-center transition-[width,height] duration-200 ml-1",
                  inputValue.trim() && !isLoading && !isTypingEffect
                    ? "bg-wedo-cyan text-white hover:opacity-90"
                    : "bg-lia-interactive-active text-lia-text-secondary cursor-not-allowed"
                )}
                type="button"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                ) : (
                  <Send className="w-4 h-4" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>

          {/* Tabs como badges abaixo do input (IA Natural, Job Description, Templates) - Sempre visível */}
          {!hideModeButtons && (
            <div className="flex items-center justify-center gap-1.5 mt-1.5">
              <button
                onClick={() => onSetActiveInputTab('ia-natural')}
                className={cn(
 "px-2.5 py-1 rounded-full text-xs font-medium transition-[width,height]",
                  activeInputTab === 'ia-natural'
                    ? "text-white bg-lia-btn-primary-bg"
                    : "text-lia-text-secondary bg-lia-bg-tertiary hover:bg-lia-interactive-active hover:bg-lia-interactive-hover"
                )}
              >
                <div className="flex items-center gap-1">
                  <Brain className="w-2.5 h-2.5 text-wedo-cyan" />
                  <span>IA Natural</span>
                </div>
              </button>
              <button
                onClick={() => onSetActiveInputTab('job-description')}
                className={cn(
 "px-2.5 py-1 rounded-full text-xs font-medium transition-[width,height]",
                  activeInputTab === 'job-description'
                    ? "text-white bg-lia-btn-primary-bg"
                    : "text-lia-text-secondary bg-lia-bg-tertiary hover:bg-lia-interactive-active hover:bg-lia-interactive-hover"
                )}
              >
                <div className="flex items-center gap-1">
                  <FileText className="w-2.5 h-2.5" />
                  <span>Job Description</span>
                </div>
              </button>
              <button
                onClick={() => onSetActiveInputTab('templates')}
                className={cn(
 "px-2.5 py-1 rounded-full text-xs font-medium transition-[width,height]",
                  activeInputTab === 'templates'
                    ? "text-white bg-lia-btn-primary-bg"
                    : "text-lia-text-secondary bg-lia-bg-tertiary hover:bg-lia-interactive-active hover:bg-lia-interactive-hover"
                )}
              >
                <div className="flex items-center gap-1">
                  <Target className="w-2.5 h-2.5" />
                  <span>Templates</span>
                </div>
              </button>
            </div>
          )}

          {/* Badges de sugestão abaixo das tabs (só quando IA Natural selecionado) */}
          {!hideModeButtons && activeInputTab === 'ia-natural' && (
            <div className="flex flex-wrap items-center justify-center gap-1.5 mt-1.5">
              <span className="text-xs font-medium text-lia-text-tertiary">Sugestões:</span>
              {suggestionTags.map((tag) => {
                const IconComponent = tag.icon
                return (
                  <button
                    key={tag.action}
                    onClick={async () => {
                      if (tag.action === 'criar_vaga') {
                        onSetInternalJobCreationMode(true)

                        // Check for existing draft: prefer backend (cross-session), fallback to local sync
                        let hasDraft = false
                        let stageName: string | null = null
                        let draftData: Partial<WizardDraftData> | null = null

                        if (checkForExistingDraftFromBackend) {
                          try {
                            const backendResult = await checkForExistingDraftFromBackend()
                            hasDraft = backendResult.hasDraft
                            stageName = backendResult.stageName
                            draftData = backendResult.draftData
                          } catch {
                            // fallback to local check on backend failure
                            const syncResult = checkForExistingDraftSync()
                            hasDraft = syncResult.hasDraft
                            stageName = syncResult.stageName
                            draftData = syncResult.draftData
                          }
                        } else {
                          const syncResult = checkForExistingDraftSync()
                          hasDraft = syncResult.hasDraft
                          stageName = syncResult.stageName
                          draftData = syncResult.draftData
                        }

                        if (hasDraft && stageName && draftData) {
                          // Store draft data for restoration BEFORE showing message
                          onSetPendingDraftData(draftData)
                          onSetAwaitingDraftChoice(true)

                          // Show only the draft choice message - let user decide
                          const draftChoiceMsg: Message = {
                            id: 'draft-choice-intro',
                            role: 'assistant',
                            content: DRAFT_DETECTED_MESSAGE(stageName),
                            timestamp: new Date(),
                            isTyping: true
                          }
                          onSetMessages([draftChoiceMsg])
                          onSetDisplayedText("")
                          setTimeout(() => {
                            typeText(DRAFT_DETECTED_MESSAGE(stageName!), 'draft-choice-intro')
                          }, 300)
                        } else {
                          // No draft - show welcome message
                          const dynamicGreeting = wizardGreeting?.greeting_message || INITIAL_JOB_CREATION_MESSAGE
                          onSetDynamicInitialMessage(dynamicGreeting)
                          const jobCreationMsg: Message = {
                            id: 'job-creation-intro',
                            role: 'assistant',
                            content: dynamicGreeting,
                            timestamp: new Date(),
                            isTyping: true
                          }
                          onSetMessages([jobCreationMsg])
                          onSetDisplayedText("")
                          setTimeout(() => {
                            typeText(dynamicGreeting, 'job-creation-intro')
                          }, 300)
                        }
                      } else {
                        onSendMessage(tag.label)
                      }
                    }}
                    disabled={isTypingEffect || isLoading}
                    className={cn(
 "inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-lia-text-secondary bg-lia-bg-tertiary rounded-full transition-[width,height]",
                      isTypingEffect || isLoading
                        ? "opacity-50 cursor-not-allowed"
                        : "hover:bg-lia-interactive-active hover:bg-lia-interactive-hover"
                    )}
                  >
                    <IconComponent className="w-2.5 h-2.5 text-lia-text-secondary" />
                    {tag.label}
                  </button>
                )
              })}
              <LiaVacancyQueriesGuide
                onSelectQuery={(query) => {
                  onSendMessage(query)
                }}
                isOpen={showMoreIdeas}
                onOpenChange={onSetShowMoreIdeas}
              />
            </div>
          )}

          {/* Conteúdo da aba Job Description */}
          {activeInputTab === 'job-description' && (
            <div className="mt-3 p-3 rounded-md border border-lia-border-subtle bg-lia-bg-primary">
              <p className="text-xs text-lia-text-secondary mb-2" aria-live="polite" aria-atomic="true">
                Cole ou anexe uma descrição de vaga e eu vou criar a vaga automaticamente para você, configurando todos os detalhes.
              </p>
              <textarea
                value={inputValue}
                onChange={(e) => onSetInputValue(e.target.value)}
                placeholder="Cole aqui o job description completo (requisitos, responsabilidades, benefícios...)."
                className="w-full px-3 py-2.5 text-xs rounded-md border border-lia-border-subtle focus:border-lia-border-medium focus:outline-none resize-none transition-colors motion-reduce:transition-none bg-lia-bg-secondary text-lia-text-primary min-h-20"
                rows={4}
              />
              <div className="flex items-center justify-between mt-2">
                <div className="flex items-center gap-1">
                  <Paperclip className="w-3 h-3 text-lia-text-secondary" />
                  <span className="text-micro text-lia-text-secondary">PDF, Word, TXT</span>
                </div>
                <Button
                  size="sm"
                  className={cn(
 "h-7 px-3 text-xs font-medium",
                    inputValue.trim() ? "bg-lia-btn-primary-bg text-lia-btn-primary-text" : "bg-lia-bg-tertiary text-lia-text-disabled"
                  )}
                  onClick={() => {
                    if (inputValue.trim()) {
                      onSetInternalJobCreationMode(true)
                      const dynamicGreeting = wizardGreeting?.greeting_message || INITIAL_JOB_CREATION_MESSAGE
                      onSetDynamicInitialMessage(dynamicGreeting)
                      onSendMessage(inputValue)
                      onSetActiveInputTab('ia-natural')
                    }
                  }}
                  disabled={!inputValue.trim()}
                >
                  <Brain className="w-3 h-3 mr-1 text-wedo-cyan" />
                  Criar Vaga a Partir do JD
                </Button>
              </div>
            </div>
          )}

          {/* Conteúdo da aba Templates */}
          {activeInputTab === 'templates' && (
            <div className="mt-3 p-3 rounded-md border border-lia-border-subtle bg-lia-bg-primary space-y-3">
              {/* Seção 1: Criar a partir de Template */}
              <div>
                <h4 className="text-xs font-medium mb-1 text-lia-text-primary">
                  Criar Vaga a Partir de Template
                </h4>
                <p className="text-micro text-lia-text-tertiary mb-2" aria-live="polite" aria-atomic="true">
                  Selecione um modelo pronto e eu inicio a criação da vaga para você
                </p>
                <div className="grid grid-cols-2 gap-1.5">
                  {[
                    { icon: '🚀', title: 'Backend Sênior Node.js', tags: ['Backend', 'Node.js'] },
                    { icon: '📊', title: 'Product Manager', tags: ['Product', 'Agile'] },
                    { icon: '🎨', title: 'UX/UI Designer', tags: ['Design', 'Figma'] },
                    { icon: '☁️', title: 'DevOps Engineer', tags: ['Cloud', 'CI/CD'] },
                  ].map((template) => (
                    <div
                      key={template.title}
                      className="cursor-pointer transition-colors motion-reduce:transition-none rounded-md p-2 hover:border border-lia-border-subtle bg-lia-bg-primary hover:border-lia-btn-primary-bg"
                      onClick={() => {
                        onSetInternalJobCreationMode(true)
                        const dynamicGreeting = wizardGreeting?.greeting_message || INITIAL_JOB_CREATION_MESSAGE
                        onSetDynamicInitialMessage(dynamicGreeting)
                        const templateMsg = `Criar vaga ${template.title}`
                        onSendMessage(templateMsg)
                        onSetActiveInputTab('ia-natural')
                      }}
                    >
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm">{template.icon}</span>
                        <div className="flex-1 min-w-0">
                          <h5 className="text-xs font-medium truncate text-lia-text-primary">
                            {template.title}
                          </h5>
                          <div className="flex gap-1 mt-0.5">
                            {template.tags.map(tag => (
                              <span key={tag} className="text-micro px-1 py-0.5 rounded-full bg-lia-bg-tertiary text-lia-text-tertiary">{tag}</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Seção 2: Criar a partir de Vaga Existente */}
              <div className="pt-2 border-t border-lia-border-subtle">
                <h4 className="text-xs font-medium mb-1 text-lia-text-primary">
                  Criar a Partir de Vaga Existente
                </h4>
                <p className="text-micro text-lia-text-tertiary mb-2" aria-live="polite" aria-atomic="true">
                  Copie uma vaga já criada e faça ajustes
                </p>
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-lia-text-secondary" />
                  <input
                    type="text"
                    placeholder="Buscar vaga por título ou ID..."
                    className="w-full pl-8 pr-3 py-2 text-xs rounded-md border border-lia-border-subtle focus:border-lia-border-medium focus:outline-none transition-colors motion-reduce:transition-none bg-lia-bg-secondary text-lia-text-primary"
                  />
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
