"use client"

import React, { useState, useRef, useCallback, useEffect } from"react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Card, CardContent } from"@/components/ui/card"
import { VariableSelector } from"@/components/ui/variable-selector"
import {
  Brain, Wand2, Loader2, Check, X, AlertCircle,
  Mail, MessageSquare, ChevronDown, RefreshCw
} from"lucide-react"
import { useCommunicationTemplates, CommunicationTemplate, TemplateSituation } from"@/hooks/chat/use-communication-templates"
import { ThinkingDots } from"@/components/ui/thinking-dots"

export type MessageChannel = 'email' | 'whatsapp'
export type ToneStyle = 'profissional' | 'caloroso' | 'urgente' | 'follow_up'

interface MessageComposerProps {
  channel: MessageChannel
  situation?: TemplateSituation
  initialSubject?: string
  initialMessage?: string
  onSubjectChange?: (subject: string) => void
  onMessageChange?: (message: string) => void
  onTemplateSelect?: (template: CommunicationTemplate) => void
  showTemplateSelector?: boolean
  showLiaAdjust?: boolean
  showVariableSelector?: boolean
  candidateContext?: {
    name?: string
    role?: string
    location?: string
    skills?: string[]
  }
  jobContext?: {
    title?: string
    department?: string
  }
  className?: string
}

const TONE_OPTIONS: { value: ToneStyle; label: string }[] = [
  { value: 'profissional', label: 'Profissional' },
  { value: 'caloroso', label: 'Caloroso' },
  { value: 'urgente', label: 'Urgente' },
  { value: 'follow_up', label: 'Follow-up' }
]

export function MessageComposer({
  channel,
  situation,
  initialSubject = '',
  initialMessage = '',
  onSubjectChange,
  onMessageChange,
  onTemplateSelect,
  showTemplateSelector = true,
  showLiaAdjust = true,
  showVariableSelector = true,
  candidateContext,
  jobContext,
  className
}: MessageComposerProps) {
  const [subject, setSubject] = useState(initialSubject)
  const [message, setMessage] = useState(initialMessage)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [toneStyle, setToneStyle] = useState<ToneStyle>('profissional')
  const [aiPrompt, setAiPrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [aiResultModal, setAiResultModal] = useState<{
    show: boolean
    newSubject: string
    newBody: string
    changesMade: string[]
  } | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  
  const messageTextareaRef = useRef<HTMLTextAreaElement>(null)
  const subjectInputRef = useRef<HTMLInputElement>(null)
  const [focusedField, setFocusedField] = useState<'subject' | 'message'>('message')

  const { templates, loading: templatesLoading } = useCommunicationTemplates({
    channel,
    autoLoad: showTemplateSelector
  })

  const filteredTemplates = situation 
    ? templates.filter(t => t.situation === situation)
    : templates

  useEffect(() => {
    setSubject(initialSubject)
  }, [initialSubject])

  useEffect(() => {
    setMessage(initialMessage)
  }, [initialMessage])

  const handleSubjectChange = useCallback((value: string) => {
    setSubject(value)
    onSubjectChange?.(value)
  }, [onSubjectChange])

  const handleMessageChange = useCallback((value: string) => {
    setMessage(value)
    onMessageChange?.(value)
  }, [onMessageChange])

  const handleTemplateSelect = useCallback((template: CommunicationTemplate) => {
    setSelectedTemplateId(template.id)
    setSubject(template.subject || '')
    setMessage(template.body)
    onSubjectChange?.(template.subject || '')
    onMessageChange?.(template.body)
    onTemplateSelect?.(template)
  }, [onSubjectChange, onMessageChange, onTemplateSelect])

  const insertVariableAtCursor = useCallback((variable: string) => {
    const textarea = focusedField === 'message' ? messageTextareaRef.current : null
    const input = focusedField === 'subject' ? subjectInputRef.current : null
    
    if (textarea) {
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const newText = message.slice(0, start) + variable + message.slice(end)
      handleMessageChange(newText)
      
      setTimeout(() => {
        const newCursorPos = start + variable.length
        textarea.setSelectionRange(newCursorPos, newCursorPos)
        textarea.focus()
      }, 0)
    } else if (input && channel === 'email') {
      const start = input.selectionStart || 0
      const end = input.selectionEnd || 0
      const newText = subject.slice(0, start) + variable + subject.slice(end)
      handleSubjectChange(newText)
      
      setTimeout(() => {
        const newCursorPos = start + variable.length
        input.setSelectionRange(newCursorPos, newCursorPos)
        input.focus()
      }, 0)
    }
  }, [focusedField, message, subject, channel, handleMessageChange, handleSubjectChange])

  const handleAdjustWithLIA = async () => {
    if (!aiPrompt.trim() && !toneStyle) return
    
    setIsGenerating(true)
    setErrorMessage(null)
    
    try {
      const promptText = aiPrompt.trim() || `Ajuste o tom para ${toneStyle}`
      
      const response = await fetch('/api/backend-proxy/email-templates/adjust', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: selectedTemplateId || 'temp',
          prompt: promptText,
          current_subject: subject,
          current_body: message,
          channel: channel,
          context: {
            candidate: candidateContext,
            job: jobContext,
            tone: toneStyle
          }
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        if (result.success && result.data) {
          setAiResultModal({
            show: true,
            newSubject: result.data.subject || subject,
            newBody: result.data.body,
            changesMade: result.data.changes_made || ['Ajustes aplicados']
          })
        }
      } else {
        const errorData = await response.json().catch(() => ({}))
        setErrorMessage(errorData.details?.detail || 'Erro ao ajustar com a IA')
        setTimeout(() => setErrorMessage(null), 5000)
      }
    } catch (err) {
      setErrorMessage('Erro ao conectar com o serviço de IA')
      setTimeout(() => setErrorMessage(null), 5000)
    } finally {
      setIsGenerating(false)
      setAiPrompt('')
    }
  }

  const handleConfirmAIAdjustment = () => {
    if (!aiResultModal) return
    handleSubjectChange(aiResultModal.newSubject)
    handleMessageChange(aiResultModal.newBody)
    setSuccessMessage('Ajustes de IA aplicados ao texto atual.')
    setTimeout(() => setSuccessMessage(null), 4000)
    setAiResultModal(null)
  }

  const handleCancelAIAdjustment = () => {
    setAiResultModal(null)
  }

  return (
    <div className={className}>
      {successMessage && (
        <div className="mb-3 px-3 py-2 rounded-xl flex items-center gap-2 bg-lia-interactive-active/30 border border-wedo-cyan/30 text-lia-text-secondary">
          <Check className="w-4 h-4 text-lia-text-secondary" />
          <span className="text-xs">{successMessage}</span>
        </div>
      )}
      
      {errorMessage && (
        <div className="mb-3 bg-status-error/10 border border-status-error/30 text-status-error px-3 py-2 rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span className="text-xs">{errorMessage}</span>
        </div>
      )}

      {showTemplateSelector && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide">
              Templates
            </label>
            <span className="text-micro flex items-center gap-1 text-lia-text-secondary">
              <Brain className="w-3 h-3 text-wedo-cyan" />
              IA disponível
            </span>
          </div>
          <div className="space-y-1.5 max-h-[150px] overflow-y-auto" role="status" aria-live="polite" aria-label="Carregando...">
            {templatesLoading ? (
              <div className="flex items-center justify-center py-4" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
                <span className="text-xs text-lia-text-secondary ml-2">Carregando templates...</span>
              </div>
            ) : filteredTemplates.length === 0 ? (
              <div className="py-3 text-center">
                <span className="text-xs text-lia-text-secondary">Nenhum template disponível</span>
              </div>
            ) : (
              filteredTemplates.slice(0, 5).map((template) => (
                <button
                  key={template.id}
                  onClick={() => handleTemplateSelect(template)}
                  className={`w-full p-2.5 rounded-md border text-left transition-colors motion-reduce:transition-none ${
 selectedTemplateId === template.id
                      ? 'border-lia-border-medium bg-lia-bg-secondary'
                      : 'border-lia-border-subtle hover:border-lia-border-default hover:bg-lia-bg-secondary'
                  }`}
                >
                  <div className="text-xs font-medium text-lia-text-primary">
                    {template.name}
                  </div>
                  {template.subject && channel === 'email' && (
                    <div className="text-micro text-lia-text-secondary mt-0.5 truncate">
                      Assunto: {template.subject}
                    </div>
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}

      <div className="space-y-3">
        {channel === 'email' && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide">
                Assunto
              </label>
              {showVariableSelector && (
                <VariableSelector
                  onSelect={insertVariableAtCursor}
                  trigger={
                    <button 
                      className="text-micro flex items-center gap-1 px-2 py-1 rounded-full hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none text-lia-text-secondary"
                      onFocus={() => setFocusedField('subject')}
                    >
                      <span>Inserir Variável</span>
                    </button>
                  }
                />
              )}
            </div>
            <input
              ref={subjectInputRef}
              type="text"
              value={subject}
              onChange={(e) => handleSubjectChange(e.target.value)}
              onFocus={() => setFocusedField('subject')}
              className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium focus:outline-none"
             
              placeholder="Assunto do email..."
            />
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide">
              {channel === 'email' ? 'Mensagem' : 'Mensagem WhatsApp'}
            </label>
            {showVariableSelector && (
              <VariableSelector
                onSelect={insertVariableAtCursor}
                trigger={
                  <button 
                    className="text-micro flex items-center gap-1 px-2 py-1 rounded-full hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none text-lia-text-secondary"
                    onFocus={() => setFocusedField('message')}
                  >
                    <span>Inserir Variável</span>
                  </button>
                }
              />
            )}
          </div>
          <textarea
            ref={messageTextareaRef}
            value={message}
            onChange={(e) => handleMessageChange(e.target.value)}
            onFocus={() => setFocusedField('message')}
            rows={8}
            className="w-full px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium focus:outline-none resize-none"
           
            placeholder={channel === 'email' ? 'Escreva sua mensagem...' : 'Escreva sua mensagem WhatsApp...'}
          />
        </div>
      </div>

      {showLiaAdjust && (
        <Card className="mt-4 rounded-xl border border-lia-border-subtle bg-lia-bg-primary">
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                <Brain className="w-4 h-4 text-wedo-cyan" />
              </div>
              <div className="flex-1">
                <span className="text-base-ui font-semibold text-lia-text-primary">
                  Ajustar com IA
                </span>
                <p className="text-xs text-lia-text-secondary">
                  Ajustes são aplicados apenas neste envio
                </p>
              </div>
              <select
                value={toneStyle}
                onChange={(e) => setToneStyle(e.target.value as ToneStyle)}
                className="text-xs border border-lia-border-subtle rounded-md px-2 py-1.5 bg-lia-bg-primary focus:outline-none focus:ring-1 focus:ring-lia-border-medium"
               
              >
                {TONE_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            
            <div className="flex gap-2">
              <input
                type="text"
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !isGenerating && handleAdjustWithLIA()}
                placeholder="Ex: Torne mais formal e adicione urgência..."
                disabled={isGenerating}
                className="flex-1 px-3 py-2 text-xs border border-lia-border-subtle rounded-xl bg-lia-bg-primary focus:ring-2 focus:ring-lia-border-subtle focus:border-lia-border-medium focus:outline-none disabled:bg-lia-bg-secondary disabled:lia-text-secondary"
               
              />
              <Button
                onClick={handleAdjustWithLIA}
                disabled={isGenerating || (!aiPrompt.trim() && !message.trim())}
                className={`gap-1.5 rounded-md py-2 px-3 text-xs min-w-[100px] text-white ${isGenerating ? 'bg-wedo-cyan' : 'bg-lia-text-secondary'}`}
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                    Ajustando...
                  </>
                ) : (
                  <>
                    <Wand2 className="w-3.5 h-3.5" />
                    Ajustar
                  </>
                )}
              </Button>
            </div>

            {isGenerating && (
              <div className="flex items-center gap-2 p-2 rounded-md bg-wedo-cyan/[.08]">
                <div className="flex gap-1">
                  <ThinkingDots dotClassName="bg-lia-btn-primary-bg" size="md" />
                </div>
                <span className="text-xs">
                  A IA está analisando e ajustando a mensagem...
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {aiResultModal?.show && (
        <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-xl bg-lia-bg-primary">
            <div className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                    <Brain className="w-5 h-5 text-wedo-cyan" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-lia-text-primary">
                      Ajustes da IA
                    </h3>
                    <p className="text-xs text-lia-text-secondary">
                      Revise as alterações sugeridas
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={handleCancelAIAdjustment} className="rounded-md">
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <CardContent className="p-4 space-y-4 overflow-y-auto">
              <div>
                <label className="block text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">
                  Alterações Realizadas
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {aiResultModal.changesMade.map((change, idx) => (
                    <Chip density="relaxed" variant="neutral" muted key={idx} className="px-2 py-0.5 rounded-full bg-lia-interactive-active/30 text-lia-text-secondary">
                      <Check className="w-3 h-3 mr-1" />
                      {change}
                    </Chip>
                  ))}
                </div>
              </div>
              
              {channel === 'email' && aiResultModal.newSubject && (
                <div>
                  <label className="block text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">
                    Novo Assunto
                  </label>
                  <div className="p-3 bg-lia-bg-secondary rounded-xl text-xs text-lia-text-primary">
                    {aiResultModal.newSubject}
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">
                  Nova Mensagem
                </label>
                <div className="p-3 bg-lia-bg-secondary rounded-xl text-xs text-lia-text-primary whitespace-pre-wrap max-h-content-md overflow-y-auto">
                  {aiResultModal.newBody}
                </div>
              </div>

              <div className="p-3 rounded-xl border border-status-warning/30 bg-status-warning/10">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-status-warning mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-status-warning">
                    Os ajustes serão aplicados apenas a esta mensagem. O template original permanece inalterado.
                  </p>
                </div>
              </div>
            </CardContent>
            <div className="border-t border-lia-border-subtle p-4 flex items-center justify-end gap-3">
              <Button variant="outline" onClick={handleCancelAIAdjustment} className="rounded-xl px-4 py-2 text-xs">
                Cancelar
              </Button>
              <Button 
                onClick={handleConfirmAIAdjustment}
                className="rounded-xl px-4 py-2 text-xs gap-1.5 bg-lia-btn-primary-bg text-lia-btn-primary-text"
              >
                <Check className="w-3.5 h-3.5" />
                Aplicar Ajustes
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

export type { MessageComposerProps }
