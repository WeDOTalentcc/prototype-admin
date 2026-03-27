"use client"

import React from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Brain, X, Send, User, Plus, Eraser, History } from "lucide-react"
import { FileUploadButton, FileAnalysisResult } from "@/components/ui/file-upload-button"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { MessageFeedback } from "@/components/chat/message-feedback"
import { cleanAgentResponse, parseChatMarkdown, escapeHtml } from "@/lib/chat-format"
import { useToast } from "@/hooks/use-toast"

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
  title = "LIA",
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
      className={`flex-shrink-0 transition-all duration-300 relative group ${className}`}
      style={{ width: width ? `${width}px` : undefined }}
    >
      <Card 
        className="flex flex-col overflow-hidden bg-white dark:bg-gray-900" 
        style={{ 
          border: '1px solid var(--gray-200)',
          height
        }}
      >
        {/* Header Padronizado */}
        <div 
          className="flex-shrink-0 px-4 py-3" 
          style={{ backgroundColor: 'var(--gray-50)' }}
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0">
                <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
              </div>
              <div className="min-w-0 flex-1">
                <h3 
                  className="text-base-ui font-bold leading-tight truncate text-gray-900 dark:text-gray-50" 
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  {title}
                </h3>
                {description && (
                  <p 
                    className="text-xs leading-tight truncate mt-0.5 text-gray-500" 
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
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
                  className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                  title="Novo chat"
                  aria-label="Iniciar novo chat"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              )}
              {onClearChat && (
                <button
                  onClick={onClearChat}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                  title="Limpar mensagens"
                  aria-label="Limpar mensagens"
                >
                  <Eraser className="w-3.5 h-3.5" />
                </button>
              )}
              {onToggleHistory && (
                <button
                  onClick={onToggleHistory}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                  title="Histórico"
                  aria-label="Ver histórico de conversas"
                >
                  <History className="w-3.5 h-3.5" />
                </button>
              )}
              {(onNewChat || onClearChat || onToggleHistory) && (
                <div className="w-px h-5 bg-gray-200 mx-0.5" />
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0"
              >
                <X className="w-4 h-4 text-gray-500" />
              </Button>
            </div>
          </div>
        </div>

        {/* Context Pills (quando há itens selecionados) */}
        {contextPills && (
          <div 
            className="flex-shrink-0 px-4 py-3" 
            style={{ 
              backgroundColor: 'rgba(0, 184, 184, 0.04)',
              borderBottom: '1px solid var(--gray-200)' 
            }}
          >
            {contextPills}
          </div>
        )}

        {/* Quick Actions */}
        {quickActions && (
          <div 
            className="flex-shrink-0 px-4 py-3" 
            style={{ borderBottom: '1px solid var(--gray-200)' }}
          >
            {quickActions}
          </div>
        )}

        {/* Tabs */}
        {tabs && (
          <div 
            className="flex-shrink-0 px-4 pt-2" 
            style={{ borderBottom: '1px solid var(--gray-200)' }}
          >
            {tabs}
          </div>
        )}

        {/* Main Content - Scrollable */}
        <div 
          className="flex-1 overflow-y-auto"
          style={{ backgroundColor: 'var(--gray-50)' }}
        >
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div 
            className="flex-shrink-0 p-4" 
            style={{ backgroundColor: 'var(--gray-50)' }}
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
          <div className="w-0.5 h-12 bg-gray-300 group-hover/resize:bg-gray-500 rounded-full transition-colors" />
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
        className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
          active ? 'text-white' : 'text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800'
        }`}
        style={{ fontFamily: 'Open Sans, sans-serif', ...(active ? { backgroundColor: 'var(--gray-600)' } : {}) }}
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
      className="pb-2.5 text-xs font-medium transition-colors relative"
      style={{ fontFamily: 'Open Sans, sans-serif' }}
    >
      <div className={`flex items-center gap-1.5 ${active ? 'text-gray-800' : 'text-gray-500 hover:text-gray-700'}`}>
        {icon}
        <span>{label}</span>
      </div>
      {active && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-900 dark:bg-gray-50" />
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
      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white border border-gray-200 rounded-full hover:border-gray-900 dark:hover:border-gray-50 hover:bg-gray-50 dark:bg-gray-800/50 transition-all"
      style={{ fontFamily: 'Open Sans, sans-serif' }}
    >
      <span className="flex-shrink-0 text-gray-700">{icon}</span>
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
  const { toast } = useToast()

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && value.trim() && !isLoading) {
      e.preventDefault()
      onSubmit()
    }
  }

  const handleFilesSelected = (files: File[]) => {
    toast({
      title: "Arquivo recebido",
      description: `Analisando ${files.length} arquivo(s)...`,
    })
  }

  const handleFileAnalyzed = (file: File, analysis: FileAnalysisResult) => {
    if (analysis.success) {
      toast({
        title: "Análise concluída",
        description: `${file.name} foi analisado com sucesso.`,
      })
      if (onFileAnalyzed) {
        onFileAnalyzed(analysis)
      }
    } else {
      toast({
        title: "Erro na análise",
        description: analysis.error || "Não foi possível analisar o arquivo.",
        variant: "destructive",
      })
    }
  }

  const handleTranscription = (text: string) => {
    onChange(value ? `${value} ${text}` : text)
    toast({
      title: "Transcrição concluída",
      description: "O texto foi adicionado ao campo de mensagem.",
    })
  }

  const handleRecordingStart = () => {
    toast({
      title: "Gravando...",
      description: "Fale sua mensagem. Clique novamente para parar.",
    })
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
          className="w-full h-32 p-4 text-sm rounded-md border focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 transition-all resize-none text-gray-950 dark:text-gray-50"
          style={{ 
            border: '1px solid var(--gray-200)',
            fontFamily: 'Open Sans, sans-serif',
            backgroundColor: 'var(--gray-50)'
          }}
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
            className={`h-10 px-6 text-sm font-medium rounded-md ${value.trim() ? 'bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200' : 'bg-gray-100 text-gray-400'}`}
            style={{
              fontFamily: 'Open Sans, sans-serif'
            }}
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
    <div className="flex items-center gap-2 px-3 py-2 rounded-[24px] border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center">
        <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
      </div>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        data-testid="chat-input"
        className="flex-1 text-base-ui bg-transparent focus:outline-none min-w-0 text-gray-900 dark:text-gray-50 placeholder:text-gray-400"
        style={{ fontFamily: 'Open Sans, sans-serif' }}
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
          className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-colors ${
            value.trim() && !isLoading
              ? 'bg-chat-cyan text-white hover:opacity-90'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
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
            className="max-w-[85%] px-3.5 py-2.5 bg-gray-100 dark:bg-gray-800 rounded-[14px] rounded-br-[4px] ml-auto"
          >
            <div 
              className="text-base-ui leading-relaxed text-gray-700 dark:text-gray-200" 
              style={{ fontFamily: 'Open Sans, sans-serif' }}
              dangerouslySetInnerHTML={{ __html: userHtml }}
            />
          </div>
          {timestamp && (
            <span className="text-xs text-gray-400 px-1" style={{ fontFamily: 'Inter, sans-serif' }}>
              {formatTime(timestamp)}
            </span>
          )}
        </div>
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center mt-0.5">
          <User className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
        </div>
      </div>
    )
  }

  const liaHtml = parseChatMarkdown(cleanAgentResponse(content))
  return (
    <div className="flex items-start gap-2.5">
      <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1 flex flex-col gap-1">
        <div className="flex items-center gap-1.5 px-1">
          <span className="text-xs font-bold text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Inter, sans-serif' }}>
            LIA
          </span>
        </div>
        <div 
          data-testid="chat-message"
          data-role="lia"
          className="max-w-[85%] px-3.5 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-[14px] rounded-bl-[4px]"
        >
          <div 
            className="text-base-ui leading-relaxed text-gray-700 dark:text-gray-200" 
            style={{ fontFamily: 'Open Sans, sans-serif' }}
            dangerouslySetInnerHTML={{ __html: liaHtml }}
          />
        </div>
        <MessageFeedback
          sessionId={sessionId || 'expanded-panel'}
          messageId={messageId || `lia-msg-${content.slice(0, 20).replace(/\s+/g, '-')}`}
          originalResponse={content}
          className="px-1"
        />
        {timestamp && (
          <span className="text-xs text-gray-400 px-1" style={{ fontFamily: 'Inter, sans-serif' }}>
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
        <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-1.5 mb-1 px-1">
          <span className="text-xs font-bold text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Inter, sans-serif' }}>
            LIA
          </span>
        </div>
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-[14px] rounded-bl-[4px] p-3 inline-block">
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 bg-chat-cyan rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-1.5 h-1.5 bg-chat-cyan rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-1.5 h-1.5 bg-chat-cyan rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    </div>
  )
}
