"use client"
import usePersonaName from "@/hooks/company/usePersonaName"

import React from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Brain, X, Send, User, Plus, Eraser, History } from "lucide-react"
import { FileUploadButton, FileAnalysisResult } from "@/components/ui/file-upload-button"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { MessageFeedback } from "@/components/chat/message-feedback"
import { cleanAgentResponse, parseChatMarkdown, escapeHtml } from "@/lib/chat-format"
import { sanitizeHtml } from "@/lib/sanitize"
import { ThinkingDots } from "@/components/ui/thinking-dots"
import { toast } from "sonner"

interface LiaExpandedPanelProps {
  title?: string
  description?: string
  onClose: () => void
  onNewChat?: () => void
  onClearChat?: () => void
  onToggleHistory?: () => void
  width?: number
  height?: string
  resizable?: boolean
  onResize?: (e: React.MouseEvent) => void
  contextPills?: React.ReactNode
  quickActions?: React.ReactNode
  tabs?: React.ReactNode
  children: React.ReactNode
  footer?: React.ReactNode
  className?: string
}

export function LiaExpandedPanel({
  title = "IA",
  description,
  onClose,
  onNewChat,
  onClearChat,
  onToggleHistory,
  width,
  height = "calc(100vh - 12rem)",
  resizable = true,
  onResize,
  contextPills,
  quickActions,
  tabs,
  children,
  footer,
  className = ""
}: LiaExpandedPanelProps) {
  return (
    <div 
      className={`flex-shrink-0 transition-colors motion-reduce:transition-none duration-300 relative group ${className}`}
      style={{width: width ? `${width}px` : undefined}}
    >
      <Card 
        className="flex flex-col overflow-hidden bg-lia-bg-primary border border-lia-border-subtle" 
        style={{height}}
      >
        {/* Header Padronizado */}
        <div 
          className="flex-shrink-0 px-4 py-3" 
         
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0">
                <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
              </div>
              <div className="min-w-0 flex-1">
                <h3 
                  className="text-base-ui font-bold leading-tight truncate text-lia-text-primary" 
                  
                >
                  {title}
                </h3>
                {description && (
                  <p 
                    className="text-xs leading-tight truncate mt-0.5 text-lia-text-secondary" 
                   
                  >
                    {description}
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-1">
              {onNewChat && (
                <button
                  onClick={onNewChat}
                  className="p-1.5 rounded-lg text-lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                  title="Novo chat"
                  aria-label="Iniciar novo chat"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              )}
              {onClearChat && (
                <button
                  onClick={onClearChat}
                  className="p-1.5 rounded-lg text-lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                  title="Limpar mensagens"
                  aria-label="Limpar mensagens"
                >
                  <Eraser className="w-3.5 h-3.5" />
                </button>
              )}
              {onToggleHistory && (
                <button
                  onClick={onToggleHistory}
                  className="p-1.5 rounded-lg text-lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                  title="Histórico"
                  aria-label="Ver histórico de conversas"
                >
                  <History className="w-3.5 h-3.5" />
                </button>
              )}
              {(onNewChat || onClearChat || onToggleHistory) && (
                <div className="w-px h-5 bg-lia-border-subtle mx-0.5" />
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-7 w-7 p-0 rounded-full hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none flex-shrink-0"
              >
                <X className="w-4 h-4 text-lia-text-secondary" />
              </Button>
            </div>
          </div>
        </div>

        {/* Context Pills (quando há itens selecionados) */}
        {contextPills && (
          <div 
            className="flex-shrink-0 px-4 py-3 bg-wedo-cyan/[0.04]"
          >
            {contextPills}
          </div>
        )}

        {/* Quick Actions */}
        {quickActions && (
          <div 
            className="flex-shrink-0 px-4 py-3" 
           
          >
            {quickActions}
          </div>
        )}

        {/* Tabs */}
        {tabs && (
          <div 
            className="flex-shrink-0 px-4 pt-2" 
           
          >
            {tabs}
          </div>
        )}

        {/* Main Content - Scrollable */}
        <div 
          className="flex-1 overflow-y-auto"
         
        >
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div 
            className="flex-shrink-0 p-4" 
           
          >
            {footer}
          </div>
        )}
      </Card>

      {/* Barra de Redimensionamento */}
      {resizable && onResize && (
        <div
          className="absolute right-0 top-0 w-2 h-full cursor-ew-resize group/resize flex items-center justify-center z-10"
          onMouseDown={onResize}
        >
          <div className="w-0.5 h-12 bg-lia-border-default group-hover/resize:bg-lia-border-medium rounded-full transition-colors motion-reduce:transition-none" />
        </div>
      )}
    </div>
  )
}

interface LiaTabButtonProps {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
  variant?: 'pill' | 'underline'
}

export function LiaTabButton({ 
  active, 
  onClick, 
  icon, 
  label,
  variant = 'pill'
}: LiaTabButtonProps) {
  if (variant === 'pill') {
    return (
      <button
        onClick={onClick}
        className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-[width,height] ${
 active ? 'bg-lia-text-secondary text-white' : 'text-lia-text-secondary hover:bg-lia-interactive-hover'
        }`}
      >
        <div className="flex items-center gap-1.5">
          {icon}
          <span>{label}</span>
        </div>
      </button>
    )
  }

  return (
    <button
      onClick={onClick}
      className="pb-2.5 text-xs font-medium transition-colors motion-reduce:transition-none relative"
     
    >
      <div className={`flex items-center gap-1.5 ${active ? 'text-lia-text-primary' : 'lia-text-secondary hover:text-lia-text-secondary'}`}>
        {icon}
        <span>{label}</span>
      </div>
      {active && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-lia-text-primary" />
      )}
    </button>
  )
}

interface LiaQuickActionChipProps {
  icon: React.ReactNode
  label: string
  onClick: () => void
}

export function LiaQuickActionChip({ icon, label, onClick }: LiaQuickActionChipProps) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-lia-bg-primary border border-lia-border-subtle rounded-full hover:border-lia-text-primary hover:bg-lia-bg-secondary transition-[width,height]"
     
    >
      <span className="flex-shrink-0 text-lia-text-secondary">{icon}</span>
      {label}
    </button>
  )
}

interface LiaChatInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  onFileAnalyzed?: (analysis: FileAnalysisResult) => void
  placeholder?: string
  isLoading?: boolean
  variant?: 'inline' | 'textarea'
  showFileUpload?: boolean
  showAudioRecord?: boolean
}

export function LiaChatInput({
  value,
  onChange,
  onSubmit,
  onFileAnalyzed,
  placeholder = "Como posso te ajudar hoje?",
  isLoading = false,
  variant = 'inline',
  showFileUpload = true,
  showAudioRecord = true
}: LiaChatInputProps) {
const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && value.trim() && !isLoading) {
      e.preventDefault()
      onSubmit()
    }
  }

  const handleFilesSelected = (files: File[]) => {
    toast.info("Arquivo recebido", { description: `Analisando ${files.length} arquivo(s)...` })
  }

  const handleFileAnalyzed = (file: File, analysis: FileAnalysisResult) => {
    if (analysis.success) {
      toast.success("Análise concluída", { description: `${file.name} foi analisado com sucesso.` })
      if (onFileAnalyzed) {
        onFileAnalyzed(analysis)
      }
    } else {
      toast.error("Erro na análise", { description: analysis.error || "Não foi possível analisar o arquivo." })
    }
  }

  const handleTranscription = (text: string) => {
    onChange(value ? `${value} ${text}` : text)
    toast.info("Transcrição concluída", { description: "O texto foi adicionado ao campo de mensagem." })
  }

  const handleRecordingStart = () => {
    toast.success("Gravando...", { description: "Fale sua mensagem. Clique novamente para parar." })
  }

  if (variant === 'textarea') {
    return (
      <div className="space-y-3">
        <textarea
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          data-testid="chat-input"
          className="w-full h-32 p-4 text-sm rounded-xl border border-lia-border-subtle bg-lia-bg-secondary focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 transition-colors motion-reduce:transition-none resize-none text-lia-text-primary"
        />
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            {showFileUpload && (
              <FileUploadButton
                onFilesSelected={handleFilesSelected}
                onFileAnalyzed={handleFileAnalyzed}
                disabled={isLoading}
                showPreview={false}
              />
            )}
            {showAudioRecord && (
              <AudioRecordButton
                onTranscription={handleTranscription}
                onRecordingStart={handleRecordingStart}
                disabled={isLoading}
              />
            )}
          </div>
          <Button
            className={`h-10 px-6 text-sm font-medium rounded-md ${value.trim() ? 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active' : 'bg-lia-bg-tertiary text-lia-text-tertiary'}`}
            
            onClick={onSubmit}
            disabled={!value.trim() || isLoading}
          >
            Enviar
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-[24px] border border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary">
      <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center">
        <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
      </div>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        data-testid="chat-input"
        className="flex-1 text-base-ui bg-transparent focus:outline-none min-w-0 text-lia-text-primary placeholder:text-lia-text-disabled"
       
      />
      <div className="flex items-center gap-1 flex-shrink-0">
        {showFileUpload && (
          <FileUploadButton
            onFilesSelected={handleFilesSelected}
            onFileAnalyzed={handleFileAnalyzed}
            disabled={isLoading}
            showPreview={false}
          />
        )}
        {showAudioRecord && (
          <AudioRecordButton
            onTranscription={handleTranscription}
            onRecordingStart={handleRecordingStart}
            disabled={isLoading}
          />
        )}
        <button
          type="button"
          onClick={onSubmit}
          disabled={!value.trim() || isLoading}
          className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-colors motion-reduce:transition-none ${
 value.trim() && !isLoading
              ? 'bg-wedo-cyan text-white hover:opacity-90'
              : 'bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-secondary cursor-not-allowed'
          }`}
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}

interface LiaChatMessageProps {
  type: 'user' | 'lia'
  content: string
  timestamp?: Date
  messageId?: string
  sessionId?: string
}

export function LiaChatMessage({ type, content, timestamp, messageId, sessionId }: LiaChatMessageProps) {
  const personaName = usePersonaName()
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  }

  if (type === 'user') {
    const userHtml = escapeHtml(content).replace(/\n/g, '<br/>')
    return (
      <div className="flex justify-end items-start gap-2">
        <div className="flex flex-col items-end gap-1">
          <div 
            data-testid="chat-message"
            data-role="user"
            className="max-w-[85%] px-3.5 py-2.5 bg-lia-bg-tertiary rounded-[14px] rounded-br-[4px] ml-auto"
          >
            <div 
              className="text-base-ui leading-relaxed text-lia-text-secondary" 
             
              dangerouslySetInnerHTML={{ __html: sanitizeHtml(userHtml) }}
            />
          </div>
          {timestamp && (
            <span className="text-xs text-lia-text-secondary px-1" >
              {formatTime(timestamp)}
            </span>
          )}
        </div>
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-lia-interactive-active dark:bg-lia-bg-elevated flex items-center justify-center mt-0.5">
          <User className="w-3.5 h-3.5 text-lia-text-tertiary" />
        </div>
      </div>
    )
  }

  const liaHtml = parseChatMarkdown(cleanAgentResponse(content))
  return (
    <div className="flex items-start gap-2.5">
      <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1 flex flex-col gap-1">
        <div className="flex items-center gap-1.5 px-1">
          <span className="text-xs font-bold text-lia-text-primary" >
            {personaName}
          </span>
        </div>
        <div 
          data-testid="chat-message"
          data-role="lia"
          className="max-w-[85%] px-3.5 py-2.5 bg-wedo-cyan/[0.04] rounded-[14px] rounded-bl-[4px]"
        >
          <div 
            className="text-base-ui leading-relaxed text-lia-text-secondary" 
           
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(liaHtml) }}
          />
        </div>
        <MessageFeedback
          sessionId={sessionId || 'expanded-panel'}
          messageId={messageId || `lia-msg-${content.slice(0, 20).replace(/\s+/g, '-')}`}
          originalResponse={content}
          className="px-1"
        />
        {timestamp && (
          <span className="text-xs text-lia-text-secondary px-1" >
            {formatTime(timestamp)}
          </span>
        )}
      </div>
    </div>
  )
}

export function LiaLoadingIndicator() {
  return (
    <div className="flex items-start gap-2.5">
      <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-1.5 mb-1 px-1">
          <span className="text-xs font-bold text-lia-text-primary" >
            {personaName}
          </span>
        </div>
        <div className="bg-wedo-cyan/[0.04] rounded-[14px] rounded-bl-[4px] p-3 inline-block">
          <div className="flex items-center gap-1">
            <ThinkingDots dotClassName="bg-wedo-cyan" size="md" />
          </div>
        </div>
      </div>
    </div>
  )
}
