"use client"

import React, { useState, useMemo } from 'react'
import { ChevronDown, ChevronUp, Building2, Plus, X } from 'lucide-react'
import { textStyles } from '@/lib/design-tokens'
import {
  useEligibilityTemplates,
  flattenTemplates,
  QUESTION_CATEGORIES,
  type FlatEligibilityQuestion,
  type QuestionCategory,
} from '@/hooks/screening/use-eligibility-templates'

interface CompanyBankQuestionsProps {
  isEditing: boolean
  selectedQuestions: string[]
  questionOverrides?: Record<string, { character?: 'eliminatoria' | 'classificatoria', expectedAnswer?: string, contextHint?: string }>
  onToggleQuestion: (questionId: string, selected: boolean) => void
  onUpdateSelectedQuestion?: (questionId: string, updates: { character?: 'eliminatoria' | 'classificatoria', expectedAnswer?: string }) => void
  /** IDs to exclude from the bank picker (e.g. questions already in company defaults) */
  excludeIds?: string[]
}

interface BankQuestion {
  id: string
  question: string
  character: 'eliminatoria' | 'classificatoria'
  expectedAnswer?: string
  contextHint?: string
}

// Audit 2026-05-20 F4: catalogo migrado para useEligibilityTemplates hook.
// COMPANY_QUESTION_BANK mantido vazio por compatibilidade — callers devem
// usar useEligibilityTemplates() direto.
export const COMPANY_QUESTION_BANK: BankQuestion[] = []
export type { CompanyBankQuestionsProps, BankQuestion }

function CharacterBadge({ character }: { character: 'eliminatoria' | 'classificatoria' }) {
  if (character === 'eliminatoria') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-error/10 text-status-error dark:bg-status-error/30 dark:text-status-error">
        eliminatória
      </span>
    )
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-status-warning/10 text-status-warning dark:bg-status-warning/30">
      classificatória
    </span>
  )
}

export function CompanyBankQuestions({ isEditing, selectedQuestions, questionOverrides, onToggleQuestion, onUpdateSelectedQuestion, excludeIds = [] }: CompanyBankQuestionsProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  // Audit 2026-05-20 F4: catalogo dinamico via useEligibilityTemplates (substitui ELIGIBILITY_QUESTIONS_BANK_DYNAMIC hardcoded)
  const { templates, isLoading: _templatesLoading } = useEligibilityTemplates({ includeMaster: true })
  const ELIGIBILITY_QUESTIONS_BANK_DYNAMIC = useMemo<FlatEligibilityQuestion[]>(
    () => flattenTemplates(templates),
    [templates],
  )
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({})

  const nonSystemTemplates = useMemo(() =>
    ELIGIBILITY_QUESTIONS_BANK_DYNAMIC.filter(q => !q.isSystemDefault && !excludeIds.includes(q.id)),
    [excludeIds]
  )

  const selectedCount = selectedQuestions.length

  // F4 audit 2026-05-20: deriva do catalogo dinamico (hook) — substitui STATIC_COMPANY_BANK
  const COMPANY_BANK_DYNAMIC = useMemo<BankQuestion[]>(
    () => ELIGIBILITY_QUESTIONS_BANK_DYNAMIC
      .filter(q => !q.isSystemDefault)
      .map(q => ({
        id: q.id,
        question: q.question,
        character: q.eliminatory ? 'eliminatoria' as const : 'classificatoria' as const,
        expectedAnswer: q.eliminatoryAnswer != null ? String(q.eliminatoryAnswer) : undefined,
        contextHint: q.contextHint,
      })),
    [ELIGIBILITY_QUESTIONS_BANK_DYNAMIC],
  )

  const selectedBankQuestions = useMemo(() =>
    COMPANY_BANK_DYNAMIC
      .filter(q => selectedQuestions.includes(q.id))
      .map(q => {
        const overrides = questionOverrides?.[q.id]
        if (!overrides) return q
        return { ...q, ...overrides }
      }),
    [COMPANY_BANK_DYNAMIC, selectedQuestions, questionOverrides]
  )

  const categorizedQuestions = useMemo(() => {
    const groups: Record<string, FlatEligibilityQuestion[]> = {}
    for (const q of nonSystemTemplates) {
      if (selectedQuestions.includes(q.id)) continue
      if (!groups[q.category]) groups[q.category] = []
      groups[q.category].push(q)
    }
    return groups
  }, [nonSystemTemplates, selectedQuestions])

  const getTemplateById = (id: string) => ELIGIBILITY_QUESTIONS_BANK_DYNAMIC.find(q => q.id === id)

  const toggleCategory = (cat: string) => {
    setExpandedCategories(prev => ({ ...prev, [cat]: !prev[cat] }))
  }

  return (
    <div className="border border-lia-border-subtle rounded-xl bg-lia-bg-primary overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
      >
        <div className="flex items-center gap-2">
          <Building2 className="w-4 h-4 text-lia-text-tertiary" />
          <span className="text-xs uppercase tracking-wider font-semibold text-lia-text-tertiary">
            Banco da Empresa
          </span>
          {selectedCount > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-micro font-medium bg-lia-bg-tertiary text-lia-text-secondary">
              {selectedCount} selecionadas
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-lia-text-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-lia-text-muted" />
        )}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4">
          {isEditing ? (
            <>
              <div className="space-y-1 mb-4">
                {Object.entries(categorizedQuestions).map(([category, questions]) => {
                  const catInfo = QUESTION_CATEGORIES[category as QuestionCategory]
                  if (!catInfo || questions.length === 0) return null
                  const isCatExpanded = expandedCategories[category] ?? false

                  return (
                    <div key={category}>
                      <button
                        onClick={() => toggleCategory(category)}
                        className="w-full flex items-center gap-2 px-2 py-1.5 hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-hover rounded-lg transition-colors motion-reduce:transition-none"
                      >
                        <span className="text-xs">{catInfo.icon}</span>
                        <span className="text-micro uppercase tracking-wider font-semibold text-lia-text-tertiary flex-1 text-left">
                          {catInfo.label}
                        </span>
                        <span className="text-micro text-lia-text-muted">
                          {questions.length}
                        </span>
                        {isCatExpanded ? (
                          <ChevronUp className="w-3 h-3 text-lia-text-muted" />
                        ) : (
                          <ChevronDown className="w-3 h-3 text-lia-text-muted" />
                        )}
                      </button>

                      {isCatExpanded && (
                        <div className="space-y-1 ml-2 mt-1">
                          {questions.map((q) => (
                            <div
                              key={q.id}
                              className="flex items-start gap-2 px-3 py-2 rounded-lg hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none group"
                            >
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className={`${textStyles.bodySmall} flex-1`}>
                                    {q.question}
                                  </span>
                                  <CharacterBadge character={q.eliminatory ? 'eliminatoria' : 'classificatoria'} />
                                </div>
                                <p className="text-micro text-lia-text-muted italic mt-0.5">
                                  {q.contextHint}
                                </p>
                              </div>
                              <button
                                onClick={() => onToggleQuestion(q.id, true)}
                                className="rounded-lg bg-lia-bg-tertiary hover:bg-lia-interactive-active dark:hover:bg-lia-btn-primary-bg p-1 transition-colors motion-reduce:transition-none opacity-60 group-hover:opacity-100 mt-0.5 shrink-0"
                                title="Adicionar pergunta"
                              >
                                <Plus className="w-3.5 h-3.5 text-lia-text-secondary" />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}

                {Object.keys(categorizedQuestions).length === 0 && (
                  <p className="text-xs text-lia-text-muted text-center py-3">
                    Todas as perguntas já foram selecionadas.
                  </p>
                )}
              </div>

              <div className="border-t border-lia-border-subtle pt-3">
                <span className="text-xs uppercase tracking-wider font-semibold text-lia-text-tertiary">
                  Perguntas Selecionadas ({selectedCount})
                </span>

                {selectedCount === 0 ? (
                  <p className="text-xs text-lia-text-muted text-center py-4">
                    Nenhuma pergunta selecionada.
                  </p>
                ) : (
                  <div className="space-y-2 mt-2">
                    {selectedBankQuestions.map((question) => {
                      const template = getTemplateById(question.id)
                      const contextHint = question.contextHint || template?.contextHint

                      return (
                        <div
                          key={question.id}
                          className="px-3 py-2.5 rounded-lg bg-lia-bg-secondary/50 group"
                        >
                          <div className="flex items-start gap-2">
                            <span className={`${textStyles.bodySmall} flex-1 pt-0.5`}>
                              {question.question}
                            </span>
                            <button
                              onClick={() => onToggleQuestion(question.id, false)}
                              className="rounded-lg p-1 hover:bg-status-error/10 dark:hover:bg-status-error/20 text-lia-text-disabled hover:text-status-error dark:hover:text-status-error transition-colors motion-reduce:transition-none shrink-0"
                              title="Remover pergunta"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </div>

                          <div className="ml-0 mt-1.5 space-y-2 pb-1">
                            <div className="flex items-center gap-2">
                              <label className="text-micro font-medium text-lia-text-tertiary whitespace-nowrap">
                                Caráter:
                              </label>
                              <select
                                value={question.character}
                                onChange={(e) => onUpdateSelectedQuestion?.(question.id, { character: e.target.value as 'eliminatoria' | 'classificatoria' })}
                                className="text-xs rounded-xl border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary px-2 py-1 focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/10 cursor-pointer"
                              >
                                <option value="classificatoria">Classificatória</option>
                                <option value="eliminatoria">Eliminatória</option>
                              </select>
                            </div>

                            {question.character === 'eliminatoria' && (
                              <div className="flex items-center gap-2">
                                <label className="text-micro font-medium text-lia-text-tertiary whitespace-nowrap">
                                  Resposta esperada:
                                </label>
                                <input
                                  type="text"
                                  placeholder="Resposta esperada"
                                  value={question.expectedAnswer || ''}
                                  onChange={(e) => onUpdateSelectedQuestion?.(question.id, { expectedAnswer: e.target.value })}
                                  className="text-xs rounded-md border border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary px-2 py-1 flex-1 max-w-[220px] placeholder-lia-text-tertiary focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/10"
                                />
                              </div>
                            )}

                            {contextHint && (
                              <p className="text-micro text-lia-text-muted italic">
                                {contextHint}
                              </p>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="space-y-2">
              {selectedCount === 0 ? (
                <p className="text-xs text-lia-text-muted text-center py-3">
                  Nenhuma pergunta selecionada.
                </p>
              ) : (
                selectedBankQuestions.map((question) => {
                  const template = getTemplateById(question.id)
                  const contextHint = question.contextHint || template?.contextHint

                  return (
                    <div
                      key={question.id}
                      className="px-3 py-2.5 rounded-lg bg-lia-bg-secondary/50"
                    >
                      <div className="flex items-center gap-2">
                        <span className={`${textStyles.bodySmall} flex-1`}>
                          {question.question}
                        </span>
                        <CharacterBadge character={question.character} />
                      </div>

                      {(question.expectedAnswer || contextHint) && (
                        <div className="ml-8 mt-1 space-y-0.5">
                          {question.expectedAnswer && (
                            <p className="text-micro text-lia-text-tertiary">
                              <span className="font-semibold">Resposta esperada:</span> {question.expectedAnswer}
                            </p>
                          )}
                          {contextHint && (
                            <p className="text-micro text-lia-text-muted italic">
                              {contextHint}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
