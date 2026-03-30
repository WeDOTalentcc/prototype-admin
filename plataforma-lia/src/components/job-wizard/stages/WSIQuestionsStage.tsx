'use client'

import React, { useState } from 'react'
import { 
  Phone, Settings, Plus, Trash2, Check, Brain,  
  Code, Target, MessageCircle, Loader2 
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWizardContext } from '../WizardContext'
import type { WSIQuestionCandidate } from '../types'

const QUESTION_CATEGORIES = [
  { id: 'technical', label: 'Técnica', icon: Code },
  { id: 'behavioral', label: 'Comportamental', icon: Brain },
  { id: 'situacional', label: 'Situacional', icon: Target },
  { id: 'autodeclaracao', label: 'Autodeclaração', icon: MessageCircle },
]

/**
 * WSI Questions Stage Component
 * 
 * Business Rule: Company Default Questions vs WSI Generated Questions
 * ================================================================
 * - WSI Generated Questions: Limit of 5 questions selected by user
 * - Company Default Questions: ADDITIONAL to the 5-question limit
 *   - These are pre-configured questions from the company settings
 *   - They do NOT count towards the 5-question limit
 *   - They have an independent "enabled" toggle
 *   - They are included in the final screening but separately
 * 
 * This means:
 * - User selects up to 5 WSI questions (mandatory or suggested)
 * - User can enable 0+ company default questions (in addition)
 * - Total questions in screening = selected WSI (≤5) + enabled company questions
 */
export function WSIQuestionsStage() {
  const {
    wsiCandidates,
    setWsiCandidates,
    companyDefaultQuestions,
    setCompanyDefaultQuestions,
    isGeneratingWSI
  } = useWizardContext()

  const [showCustomQuestionForm, setShowCustomQuestionForm] = useState(false)
  const [customQuestionText, setCustomQuestionText] = useState('')
  const [customQuestionType, setCustomQuestionType] = useState<'open' | 'yes-no' | 'numeric' | 'multiple-choice'>('open')
  const [customQuestionCategory, setCustomQuestionCategory] = useState<string>('technical')

  // Business Rule: Count only AI-generated WSI questions towards the 5-question limit
  // Company default questions are NOT included in this count
  const selectedCount = wsiCandidates.filter(q => q.selected).length
  const enabledCompanyQuestionsCount = companyDefaultQuestions.filter(q => q.enabled).length

  const toggleQuestionSelection = (id: string) => {
    setWsiCandidates(prev => {
      const question = prev.find(q => q.id === id)
      if (!question) return prev
      
      // Check if we're at max selected (5) and trying to select another
      if (!question.selected && selectedCount >= 5) {
        return prev
      }
      
      return prev.map(q => q.id === id ? { ...q, selected: !q.selected } : q)
    })
  }

  const toggleWSIFlag = (id: string) => {
    setWsiCandidates(prev => prev.map(q => 
      q.id === id ? { ...q, isWSI: !q.isWSI } : q
    ))
  }

  const updateCategory = (id: string, category: string) => {
    setWsiCandidates(prev => prev.map(q => 
      q.id === id ? { ...q, category: category as WSIQuestionCandidate['category'] } : q
    ))
  }

  const deleteQuestion = (id: string) => {
    setWsiCandidates(prev => prev.filter(q => q.id !== id))
  }

  // Business Rule: Company questions are INDEPENDENT of the 5-question limit
  // These are additional questions from company settings and do not count towards the limit
  const toggleCompanyQuestion = (id: string) => {
    setCompanyDefaultQuestions(prev => prev.map(q => 
      q.id === id ? { ...q, enabled: !q.enabled } : q
    ))
  }

  const addCustomQuestion = () => {
    if (!customQuestionText.trim()) return
    
    const newQuestion: WSIQuestionCandidate = {
      id: `custom-${Date.now()}`,
      question: customQuestionText.trim(),
      type: customQuestionType,
      required: true,
      selected: selectedCount < 5,
      batch: 0,
      isWSI: true,
      category: customQuestionCategory as WSIQuestionCandidate['category']
    }
    
    setWsiCandidates(prev => [...prev, newQuestion])
    setCustomQuestionText('')
    setShowCustomQuestionForm(false)
  }

  const getCategoryIcon = (category?: string) => {
    const cat = QUESTION_CATEGORIES.find(c => c.id === category)
    if (!cat) return MessageCircle
    return cat.icon
  }

  const renderQuestion = (question: WSIQuestionCandidate) => {
    const CategoryIcon = getCategoryIcon(question.category)
    
    return (
      <div 
        key={question.id}
        className={cn(
 "p-3 rounded-md border transition-colors",
          question.selected
            ? "bg-gray-50 dark:bg-lia-bg-secondary/50 border-gray-900"
            : "bg-lia-bg-primary border-lia-border-subtle hover:border-lia-border-default dark:border-lia-border-default"
        )}
      >
        <div className="flex items-start gap-2">
          {/* Selection checkbox */}
          <button
            onClick={() => toggleQuestionSelection(question.id)}
            disabled={!question.selected && selectedCount >= 5}
            className={cn(
 "w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors",
              question.selected
                ? "bg-gray-900 text-white"
                : selectedCount >= 5
                  ? "border border-lia-border-subtle cursor-not-allowed"
                  : "border-2 border-lia-border-subtle hover:border-gray-900 dark:hover:border-gray-50"
            )}
          >
            {question.selected && <Check className="w-3 h-3" strokeWidth={3} />}
          </button>
          
          {/* Question content */}
          <div className="flex-1 min-w-0">
            <p className="text-xs lia-text-strong leading-relaxed">
              {question.question}
            </p>
            
            {/* Question metadata */}
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              {/* Category badge */}
              <span className={cn(
 "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-micro font-medium",
                question.category === 'technical' ? "bg-wedo-cyan/10 text-wedo-cyan-dark" :
                question.category === 'behavioral' ? "bg-wedo-purple/10 text-wedo-purple" :
                question.category === 'situacional' ? "bg-status-warning/10 text-status-warning" :
                "bg-gray-50 lia-text-base"
              )}>
                <CategoryIcon className="w-2.5 h-2.5" />
                {QUESTION_CATEGORIES.find(c => c.id === question.category)?.label || 'Geral'}
              </span>
              
              {/* Type badge */}
              <span className="px-1.5 py-0.5 bg-gray-100 lia-text-secondary rounded-full text-micro">
                {question.type === 'yes-no' ? 'Sim/Não' :
                 question.type === 'numeric' ? 'Numérica' :
                 question.type === 'multiple-choice' ? 'Múltipla escolha' :
                 'Aberta'}
              </span>
              
              {/* WSI flag */}
              <button
                onClick={() => toggleWSIFlag(question.id)}
                className={cn(
 "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-micro font-medium transition-colors",
                  question.isWSI
                    ? "bg-status-success/10 text-status-success"
                    : "bg-gray-100 lia-text-secondary hover:bg-status-success/10"
                )}
              >
                <Brain className="w-2.5 h-2.5 text-wedo-cyan" />
                WSI
              </button>
            </div>
          </div>
          
          {/* Delete button */}
          <button
            onClick={() => deleteQuestion(question.id)}
            className="p-1 lia-text-secondary hover:text-status-error transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2.5">
      {/* Header with counter */}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <Phone className="w-3.5 h-3.5 text-whatsapp-green" />
          <span className="text-micro font-semibold lia-text-secondary uppercase tracking-wide">
            Perguntas de Triagem WSI
          </span>
        </div>
        <div className="flex items-center gap-1 flex-wrap justify-end">
          <span className={cn(
 "text-xs font-semibold",
            selectedCount === 5 ? "text-status-success" : "text-lia-text-secondary dark:text-lia-text-tertiary"
          )}>
            {selectedCount}
          </span>
          <span className="text-micro lia-text-secondary">/ 5 selecionadas</span>
          {enabledCompanyQuestionsCount > 0 && (
            <>
              <span className="text-micro lia-text-secondary">(+</span>
              <span className="text-micro font-medium text-lia-text-secondary dark:text-lia-text-tertiary">{enabledCompanyQuestionsCount}</span>
              <span className="text-micro lia-text-secondary">da empresa)</span>
            </>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={cn(
 "h-full transition-[width,height] duration-300",
            selectedCount >= 5 ? "bg-status-success" : 
            selectedCount >= 3 ? "bg-gray-900" : "bg-status-warning"
          )}
          style={{width: `${(selectedCount / 5) * 100}%`}}
        />
      </div>

      {/* Company Default Questions Section */}
      {companyDefaultQuestions.length > 0 && (
        <div className="mb-4 p-3 bg-gray-50 rounded-md border border-lia-border-subtle">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Settings className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              <span className="text-xs font-semibold lia-text-secondary uppercase tracking-wide">
                Perguntas Padrão da Empresa
              </span>
              <span className="text-micro lia-text-secondary">
                ({companyDefaultQuestions.filter(q => q.enabled).length}/{companyDefaultQuestions.length} ativas)
              </span>
            </div>
            <button
              onClick={() => setCompanyDefaultQuestions(prev => prev.map(q => ({ ...q, enabled: false })))}
              className="text-micro text-lia-text-secondary dark:text-lia-text-tertiary hover:underline"
            >
              Desabilitar todas
            </button>
          </div>
          {/* Business Rule Note: These questions are ADDITIONAL to the 5-question limit */}
          <div className="mb-2 p-2 bg-wedo-cyan/10 rounded-md border border-wedo-cyan/30">
            <p className="text-micro text-wedo-cyan-dark">
              💡 <strong>Nota:</strong> Estas perguntas são <strong>adicionais</strong> às 5 perguntas WSI. Elas não contam no limite.
            </p>
          </div>
          <div className="space-y-2">
            {companyDefaultQuestions.map(q => (
              <div key={q.id} className="flex items-center justify-between p-2 bg-lia-bg-primary rounded-md border border-lia-border-subtle">
                <div className="flex items-center gap-2 flex-1">
                  <button
                    onClick={() => toggleCompanyQuestion(q.id)}
                    className={cn(
 "w-4 h-4 rounded-md flex items-center justify-center flex-shrink-0 transition-colors",
                      q.enabled 
                        ? "bg-gray-900 text-white" 
                        : "border-2 border-lia-border-subtle hover:border-gray-900 dark:hover:border-gray-50"
                    )}
                  >
                    {q.enabled && <Check className="w-2.5 h-2.5" strokeWidth={3} />}
                  </button>
                  <span className={cn(
 "text-xs",
                    q.enabled ? "lia-text-strong" : "lia-text-secondary"
                  )}>
                    {q.question}
                  </span>
                </div>
                <span className="px-1.5 py-0.5 bg-gray-100 lia-text-secondary rounded-full text-micro">
                  {q.type === 'yes-no' ? 'Sim/Não' : q.type === 'numeric' ? 'Numérica' : q.type === 'multiple-choice' ? 'Múltipla' : 'Aberta'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Loading indicator */}
      {isGeneratingWSI && (
        <div className="p-4 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md border border-lia-border-default dark:border-lia-border-default flex items-center justify-center gap-2">
          <Loader2 className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary animate-spin" />
          <span className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
            Gerando perguntas personalizadas para esta vaga...
          </span>
        </div>
      )}

      {/* AI Generated Questions */}
      {wsiCandidates.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            <span className="text-micro font-semibold lia-text-secondary uppercase tracking-wide">
              Perguntas Sugeridas por LIA
            </span>
          </div>
          {wsiCandidates.map(renderQuestion)}
        </div>
      )}

      {/* Add Custom Question Button */}
      <button
        onClick={() => setShowCustomQuestionForm(true)}
        className="w-full py-2 px-3 rounded-md border border-dashed border-gray-900 text-lia-text-secondary dark:text-lia-text-tertiary text-xs font-medium hover:bg-gray-50 dark:bg-lia-bg-secondary/50 transition-colors flex items-center justify-center gap-1.5"
      >
        <Plus className="w-3.5 h-3.5" />
        Adicionar Pergunta Personalizada
      </button>

      {/* Custom Question Form */}
      {showCustomQuestionForm && (
        <div className="p-3 bg-gray-50 rounded-md border border-lia-border-subtle space-y-2">
          <textarea
            value={customQuestionText}
            onChange={(e) => setCustomQuestionText(e.target.value)}
            placeholder="Digite sua pergunta personalizada..."
            className="w-full px-3 py-2 border border-lia-border-subtle rounded-md text-xs resize-none"
            rows={2}
            autoFocus
          />
          <div className="flex gap-2">
            <select
              value={customQuestionType}
              onChange={(e) => setCustomQuestionType(e.target.value as WSIQuestionCandidate['type'])}
              className="flex-1 px-3 py-1.5 border border-lia-border-subtle rounded-md text-xs bg-lia-bg-primary"
            >
              <option value="open">Aberta</option>
              <option value="yes-no">Sim/Não</option>
              <option value="numeric">Numérica</option>
              <option value="multiple-choice">Múltipla Escolha</option>
            </select>
            <select
              value={customQuestionCategory}
              onChange={(e) => setCustomQuestionCategory(e.target.value)}
              className="flex-1 px-3 py-1.5 border border-lia-border-subtle rounded-md text-xs bg-lia-bg-primary"
            >
              {QUESTION_CATEGORIES.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.label}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => {
                setShowCustomQuestionForm(false)
                setCustomQuestionText('')
              }}
              className="flex-1 py-1.5 px-3 rounded-md border border-lia-border-subtle text-xs lia-text-secondary"
            >
              Cancelar
            </button>
            <button
              onClick={addCustomQuestion}
              disabled={!customQuestionText.trim()}
              className="flex-1 py-1.5 px-3 rounded-md bg-gray-900 text-white text-xs disabled:opacity-50"
            >
              Adicionar
            </button>
          </div>
        </div>
      )}

      {/* Instructions */}
      {wsiCandidates.length === 0 && !isGeneratingWSI && (
        <div className="p-4 bg-status-warning/10 rounded-md border border-status-warning/30 text-center">
          <p className="text-xs text-status-warning">
            Complete as etapas anteriores para que a LIA gere perguntas de triagem personalizadas para esta vaga.
          </p>
        </div>
      )}
    </div>
  )
}

export default WSIQuestionsStage
