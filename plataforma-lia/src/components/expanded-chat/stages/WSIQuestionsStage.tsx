'use client'

import React from 'react'
import { Phone, Code, Brain, Check, Trash2, Plus, X, Loader2, Settings, AlertTriangle, CheckCircle2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { textStyles } from '@/lib/design-tokens'

export interface WSIQuestionCandidate {
  id: string
  question: string
  type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  required: boolean
  selected: boolean
  batch: number
  isWSI?: boolean
  competency?: string
  framework?: string
  category?: 'technical' | 'behavioral' | 'autodeclaracao_contexto' | 'micro_case' | 'situacional' | 'fit' | 'autodeclaracao'
  options?: string[]
  expectedAnswer?: string | number | boolean
  correctOptionIndex?: number
}

export interface CompanyDefaultQuestion {
  id: string
  question: string
  type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  enabled: boolean
}

export interface WSIQuestionsStageProps {
  wsiCandidates: WSIQuestionCandidate[]
  companyDefaultQuestions: CompanyDefaultQuestion[]
  onSetCompanyDefaultQuestions: (questions: CompanyDefaultQuestion[]) => void
  onToggleQuestionSelection: (id: string) => void
  onDeleteQuestion: (id: string) => void
  onUpdateExpectedAnswer: (id: string, answer: string | number | boolean) => void
  onUpdateCorrectOption: (id: string, optionIndex: number) => void
  isGeneratingWSI: boolean
  onGenerateWSIQuestions: (count: number, type: 'technical' | 'behavioral') => void
  showCustomQuestionForm: boolean
  onSetShowCustomQuestionForm: (show: boolean) => void
  customQuestionText: string
  onSetCustomQuestionText: (text: string) => void
  customQuestionType: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  onSetCustomQuestionType: (type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice') => void
  customQuestionRequired: boolean
  onSetCustomQuestionRequired: (required: boolean) => void
  onAddCustomQuestion: () => void
  highlightedFields?: Set<string>
}

export function WSIQuestionsStage({
  wsiCandidates,
  companyDefaultQuestions,
  onSetCompanyDefaultQuestions,
  onToggleQuestionSelection,
  onDeleteQuestion,
  onUpdateExpectedAnswer,
  onUpdateCorrectOption,
  isGeneratingWSI,
  onGenerateWSIQuestions,
  showCustomQuestionForm,
  onSetShowCustomQuestionForm,
  customQuestionText,
  onSetCustomQuestionText,
  customQuestionType,
  onSetCustomQuestionType,
  customQuestionRequired,
  onSetCustomQuestionRequired,
  onAddCustomQuestion,
  highlightedFields,
}: WSIQuestionsStageProps) {
  const selectedCount = wsiCandidates.filter(q => q.selected).length

  const isFieldHighlighted = (fieldId: string) => highlightedFields?.has(fieldId) ?? false

  const technicalQuestions = wsiCandidates.filter(q =>
    q.category === 'technical' || q.category === 'autodeclaracao_contexto' ||
    q.category === 'micro_case' || q.category === 'situacional' ||
    q.category === 'autodeclaracao' || !q.category
  )
  const behavioralQuestions = wsiCandidates.filter(q =>
    q.category === 'behavioral' || q.category === 'fit'
  )

  const renderQuestionCard = (q: WSIQuestionCandidate) => (
    <div
      key={q.id}
      className={cn(
 "p-3 rounded-md border transition-colors relative",
        q.selected
          ? "bg-gray-100 dark:bg-lia-bg-secondary border-gray-900"
          : "bg-lia-bg-primary border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-default"
      )}
    >
      <button
        onClick={() => onDeleteQuestion(q.id)}
        className="absolute top-2 right-2 lia-text-secondary hover:text-status-error transition-colors motion-reduce:transition-none focus-visible:ring-2 focus-visible:ring-gray-400 rounded-md"
        title="Remover pergunta"
        aria-label="Remover pergunta de triagem"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
      <div className="flex items-start gap-2 pr-6">
        <button
          onClick={() => onToggleQuestionSelection(q.id)}
          disabled={!q.selected && selectedCount >= 5}
          className={cn(
 "mt-0.5 w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 transition-colors",
            q.selected
              ? "bg-gray-900 text-white"
              : "border border-lia-border-subtle",
            !q.selected && selectedCount >= 5
              ? "opacity-50 cursor-not-allowed"
              : "hover:border-gray-900 dark:hover:border-gray-50"
          )}
        >
          {q.selected && <Check className="w-2.5 h-2.5" />}
        </button>

        <div className="flex-1">
          <p className="text-xs lia-text-strong">
            {q.question}
          </p>

          <div className="flex items-center gap-2 mt-2">
            <span className={cn(
 "px-2 py-0.5 text-xs rounded-full",
              q.type === 'yes-no' ? "bg-wedo-cyan/15 text-wedo-cyan-dark" :
              q.type === 'numeric' ? "bg-status-warning/15 text-status-warning" :
              q.type === 'multiple-choice' ? "bg-wedo-purple/15 text-wedo-purple" :
              "bg-gray-100 lia-text-base"
            )}>
              {q.type === 'yes-no' ? 'Sim/Não' :
               q.type === 'numeric' ? 'Numérica' :
               q.type === 'multiple-choice' ? 'Múltipla escolha' : 'Aberta'}
            </span>
            {q.required && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary">
                Obrigatória
              </span>
            )}
          </div>

          {q.selected && (
            <div className="mt-3 pt-3 border-t border-lia-border-subtle">
              <label className="text-xs font-semibold lia-text-secondary uppercase tracking-wide">
                Resposta esperada:
              </label>
              {q.type === 'yes-no' ? (
                <div className="flex gap-2 mt-1">
                  <button
                    onClick={() => onUpdateExpectedAnswer(q.id, true)}
                    className={cn(
 "flex-1 py-1.5 text-xs rounded-md transition-colors",
                      q.expectedAnswer === true
                        ? "bg-status-success text-white"
                        : "bg-gray-50 lia-text-secondary hover:bg-gray-200"
                    )}
                  >
                    Sim
                  </button>
                  <button
                    onClick={() => onUpdateExpectedAnswer(q.id, false)}
                    className={cn(
 "flex-1 py-1.5 text-xs rounded-md transition-colors",
                      q.expectedAnswer === false
                        ? "bg-status-error text-white"
                        : "bg-gray-50 lia-text-secondary hover:bg-gray-200"
                    )}
                  >
                    Não
                  </button>
                </div>
              ) : q.type === 'numeric' ? (
                <input
                  type="number"
                  value={q.expectedAnswer as number || ''}
                  onChange={(e) => onUpdateExpectedAnswer(q.id, parseInt(e.target.value) || 0)}
                  placeholder="Ex: 3 (anos mínimos)"
                  className="w-full mt-1 px-3 py-1.5 text-xs border border-lia-border-subtle rounded-md focus:outline-none focus:border-gray-400"
                />
              ) : q.type === 'multiple-choice' && q.options ? (
                <div className="flex flex-wrap gap-1 mt-1">
                  {q.options.map((opt, idx) => (
                    <button
                      key={idx}
                      onClick={() => onUpdateCorrectOption(q.id, idx)}
                      className={cn(
 "px-2 py-1 text-xs rounded-md transition-colors",
                        q.correctOptionIndex === idx
                          ? "bg-status-success text-white"
                          : "bg-gray-50 lia-text-secondary hover:bg-gray-200"
                      )}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              ) : (
                <input
                  type="text"
                  value={q.expectedAnswer as string || ''}
                  onChange={(e) => onUpdateExpectedAnswer(q.id, e.target.value)}
                  placeholder="Palavras-chave ou critérios esperados..."
                  className="w-full mt-1 px-3 py-1.5 text-xs border border-lia-border-subtle rounded-md focus:outline-none focus:border-gray-400"
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <Phone className="w-3.5 h-3.5 text-status-success" />
          <span className={`${textStyles.label} lia-text-secondary uppercase tracking-wide`}>
            Perguntas de Triagem WSI
          </span>
        </div>
        <div className="flex items-center gap-1">
          <span className={cn(
 "text-xs font-semibold",
            selectedCount === 5 ? "text-status-success" : "text-lia-text-secondary dark:text-lia-text-tertiary"
          )}>
            {selectedCount}
          </span>
          <span className="text-micro lia-text-secondary">/ 5 selecionadas</span>
        </div>
      </div>

      {companyDefaultQuestions.length > 0 ? (
        <div className="mb-4 p-3 bg-gray-50 rounded-md border border-lia-border-subtle">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Settings className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              <span className="text-xs font-semibold lia-text-secondary uppercase tracking-wide">
                Perguntas Padrão da Empresa
              </span>
              <span className="text-micro lia-text-secondary">({companyDefaultQuestions.filter(q => q.enabled).length}/{companyDefaultQuestions.length} ativas)</span>
            </div>
            <button
              onClick={() => onSetCompanyDefaultQuestions(companyDefaultQuestions.map(q => ({ ...q, enabled: false })))}
              className="text-micro text-lia-text-secondary dark:text-lia-text-tertiary hover:underline focus-visible:ring-2 focus-visible:ring-gray-400 rounded-md"
            >
              Desabilitar todas
            </button>
          </div>
          <div className="space-y-2">
            {companyDefaultQuestions.map(q => (
              <div key={q.id} className="flex items-center justify-between p-2 bg-lia-bg-primary rounded-md border border-lia-border-subtle">
                <div className="flex items-center gap-2 flex-1">
                  <button
                    onClick={() => onSetCompanyDefaultQuestions(
                      companyDefaultQuestions.map(cq => cq.id === q.id ? { ...cq, enabled: !cq.enabled } : cq)
                    )}
                    className={cn(
 "w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 transition-colors",
                      q.enabled
                        ? "bg-gray-900 text-white"
                        : "border border-lia-border-subtle hover:border-gray-900 dark:hover:border-gray-50"
                    )}
                  >
                    {q.enabled && <Check className="w-2.5 h-2.5" />}
                  </button>
                  <span className="text-xs lia-text-strong">{q.question}</span>
                </div>
                <span className={cn(
 "px-2 py-0.5 text-micro rounded-full",
                  q.type === 'yes-no' ? "bg-wedo-cyan/15 text-wedo-cyan-dark" :
                  q.type === 'numeric' ? "bg-status-warning/15 text-status-warning" :
                  "bg-gray-100 lia-text-base"
                )}>
                  {q.type === 'yes-no' ? 'Sim/Não' : q.type === 'numeric' ? 'Numérica' : 'Aberta'}
                </span>
              </div>
            ))}
          </div>
          <p className="text-micro lia-text-secondary mt-2 flex items-center gap-1">
            <Settings className="w-3 h-3" />
            Configure perguntas padrão em Configurações &gt; Triagem
          </p>
        </div>
      ) : (
        <div className="mb-4 p-3 bg-status-warning/15/30 rounded-md border border-status-warning/30/50">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-status-warning" />
            <span className="text-xs font-semibold text-status-warning uppercase tracking-wide">
              Perguntas da Empresa
            </span>
          </div>
          <p className="text-xs text-status-warning">
            Nenhuma pergunta padrão cadastrada.
          </p>
          <p className="text-micro text-status-warning mt-1 flex items-center gap-1">
            <Settings className="w-3 h-3" />
            Configure no menu Configurações &gt; Triagem
          </p>
        </div>
      )}

      {wsiCandidates.length > 0 && (
        <div className="space-y-3 max-h-content-lg overflow-y-auto pr-1">
          {technicalQuestions.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 bg-gray-50 px-3 py-1.5 rounded-md">
                <Code className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                <span className="text-xs font-semibold lia-text-secondary uppercase tracking-wide">
                  Validação Técnica
                </span>
                <span className="text-micro lia-text-secondary">({technicalQuestions.length})</span>
              </div>
              {technicalQuestions.map(renderQuestionCard)}
            </div>
          )}

          {behavioralQuestions.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 bg-gray-50 px-3 py-1.5 rounded-md">
                <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                <span className="text-xs font-semibold lia-text-secondary uppercase tracking-wide">
                  Fit Comportamental
                </span>
                <span className="text-micro lia-text-secondary">({behavioralQuestions.length})</span>
              </div>
              {behavioralQuestions.map(renderQuestionCard)}
            </div>
          )}
        </div>
      )}

      {isGeneratingWSI && (
        <div className="flex items-center justify-center py-4 bg-gray-50 rounded-md border border-lia-border-subtle" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-secondary dark:text-lia-text-tertiary" />
          <span className="ml-2 text-xs lia-text-secondary">Gerando perguntas com metodologia WSI...</span>
        </div>
      )}

      {!isGeneratingWSI && selectedCount < 5 && (
        <div className="flex gap-2">
          <button
            onClick={() => onGenerateWSIQuestions(3, 'technical')}
            className="flex-1 py-2 border border-dashed border-gray-900 rounded-md text-xs text-lia-text-secondary dark:text-lia-text-tertiary hover:bg-gray-50 dark:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2 focus-visible:ring-2 focus-visible:ring-gray-400"
            aria-label="Gerar perguntas técnicas WSI"
          >
            <Code className="w-3.5 h-3.5" /> Gerar perguntas técnicas
          </button>
          <button
            onClick={() => onGenerateWSIQuestions(3, 'behavioral')}
            className="flex-1 py-2 border border-dashed border-wedo-purple/30 rounded-md text-xs text-wedo-purple hover:bg-wedo-purple/5 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2 focus-visible:ring-2 focus-visible:ring-gray-400"
            aria-label="Gerar perguntas de fit cultural WSI"
          >
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" /> Gerar Fit Cultural
          </button>
        </div>
      )}

      {showCustomQuestionForm ? (
        <div className="p-3 bg-gray-50 rounded-md border border-lia-border-subtle space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold lia-text-secondary uppercase tracking-wide">
              Adicionar Pergunta Customizada
            </span>
            <button
              onClick={() => {
                onSetShowCustomQuestionForm(false)
                onSetCustomQuestionText('')
                onSetCustomQuestionType('open')
                onSetCustomQuestionRequired(false)
              }}
              className="lia-text-secondary hover:lia-text-secondary focus-visible:ring-2 focus-visible:ring-gray-400 rounded-md"
              aria-label="Fechar formulário de pergunta customizada"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <textarea
            value={customQuestionText}
            onChange={(e) => onSetCustomQuestionText(e.target.value)}
            placeholder="Digite sua pergunta aqui..."
            className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-md focus:outline-none focus:border-gray-400 resize-none"
            rows={2}
          />
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <label className="text-micro lia-text-secondary mb-1 block">Tipo de resposta:</label>
              <select
                value={customQuestionType}
                onChange={(e) => onSetCustomQuestionType(e.target.value as 'open' | 'yes-no' | 'numeric' | 'multiple-choice')}
                className="w-full px-2 py-1.5 text-xs border border-lia-border-subtle rounded-md focus:outline-none focus:border-gray-400"
              >
                <option value="open">Aberta</option>
                <option value="yes-no">Sim/Não</option>
                <option value="numeric">Numérica</option>
                <option value="multiple-choice">Múltipla escolha</option>
              </select>
            </div>
            <div className="flex items-center gap-2 pt-4">
              <button
                onClick={() => onSetCustomQuestionRequired(!customQuestionRequired)}
                className={cn(
 "w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 transition-colors",
                  customQuestionRequired
                    ? "bg-gray-900 text-white"
                    : "border border-lia-border-subtle hover:border-gray-900 dark:hover:border-gray-50"
                )}
              >
                {customQuestionRequired && <Check className="w-2.5 h-2.5" />}
              </button>
              <span className="text-micro lia-text-secondary">Eliminatória</span>
            </div>
          </div>
          <button
            onClick={onAddCustomQuestion}
            disabled={!customQuestionText.trim()}
            className={cn(
 "w-full py-2 rounded-md text-xs font-medium transition-colors flex items-center justify-center gap-2",
              customQuestionText.trim()
                ? "bg-gray-900 text-white hover:bg-gray-800 dark:hover:bg-gray-200"
                : "bg-gray-200 lia-text-secondary cursor-not-allowed"
            )}
          >
            <Plus className="w-3.5 h-3.5" /> Adicionar Pergunta
          </button>
        </div>
      ) : (
        <button
          onClick={() => onSetShowCustomQuestionForm(true)}
          className="w-full py-2 border border-dashed border-lia-border-subtle rounded-md text-xs lia-text-secondary hover:border-gray-900 dark:hover:border-gray-50 hover:lia-text-strong dark:hover:lia-text-subtle hover:bg-gray-50 dark:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
          aria-label="Adicionar pergunta de triagem customizada"
        >
          <Plus className="w-3.5 h-3.5" /> Adicionar pergunta customizada
        </button>
      )}

      <div className={cn(
 "p-2 rounded-md border",
        selectedCount === 5
          ? "bg-status-success/15 border-status-success/30/30"
          : "bg-gray-50 border-lia-border-default dark:border-lia-border-default"
      )}>
        <div className="flex items-center gap-2">
          {selectedCount === 5 ? (
            <CheckCircle2 className="w-3.5 h-3.5 text-status-success" />
          ) : (
            <AlertCircle className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
          )}
          <span className="text-micro lia-text-secondary">
            {selectedCount === 5
              ? "Triagem completa! Revise as respostas esperadas acima."
              : `Selecione mais ${5 - selectedCount} pergunta(s) para completar.`}
          </span>
        </div>
      </div>
    </div>
  )
}
