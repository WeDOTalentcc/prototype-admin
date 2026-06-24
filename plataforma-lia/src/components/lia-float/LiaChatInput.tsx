"use client"

import React from "react"
import { Loader2, Send, Paperclip, FileText, XCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { ContextBadge } from "@/components/lia-float/ContextBadge"

export interface LiaChatInputProps {
  inputText: string
  setInputText: React.Dispatch<React.SetStateAction<string>>
  maxInputChars: number
  attachedCvFile: File | null
  setAttachedCvFile: (v: File | null) => void
  cvFileInputRef: React.RefObject<HTMLInputElement | null>
  inputRef: React.RefObject<HTMLInputElement | null>
  handleCvFileAttach: (e: React.ChangeEvent<HTMLInputElement>) => void
  handleCvFileButtonClick: () => void
  handleSend: () => void
  handleKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void
  isCreating: boolean
  isStreaming: boolean
  isScreening: boolean
  hitlPending: { action: string; description: string } | null
  canSend: boolean
  contextPage?: string | null
  contextDismissed?: boolean
  onContextDismiss?: () => void
}

export function LiaChatInput({
  inputText,
  setInputText,
  maxInputChars,
  attachedCvFile,
  setAttachedCvFile,
  cvFileInputRef,
  inputRef,
  handleCvFileAttach,
  handleCvFileButtonClick,
  handleSend,
  handleKeyDown,
  isCreating,
  isStreaming,
  isScreening,
  hitlPending,
  canSend,
  contextPage,
  contextDismissed = false,
  onContextDismiss,
}: LiaChatInputProps) {
  const showBadge = !contextDismissed && !!contextPage && contextPage !== "Conversar"

  return (
    <div className="px-4 pb-4 pt-2 flex-shrink-0 border-t border-lia-border-subtle">
      {attachedCvFile && (
        <div className="flex items-center gap-2 mb-2 px-2 py-1.5 rounded-lg bg-lia-bg-secondary border border-lia-border-subtle">
          <FileText className="w-3.5 h-3.5 text-wedo-cyan flex-shrink-0" />
          <span className="text-xs text-lia-text-primary truncate flex-1">{attachedCvFile.name}</span>
          <button
            onClick={() => setAttachedCvFile(null)}
            className="p-0.5 rounded hover:bg-lia-interactive-hover text-lia-text-tertiary hover:text-lia-text-secondary"
            aria-label="Remover arquivo"
          >
            <XCircle className="w-3 h-3" />
          </button>
        </div>
      )}
      <div className="flex items-center gap-2 px-3 py-2 rounded-[24px] bg-lia-bg-primary border border-lia-border-subtle">
        {showBadge && (
          <ContextBadge
            contextPage={contextPage}
            onRemove={onContextDismiss}
          />
        )}
        <input
          ref={inputRef}
          type="text"
          value={inputText}
          onChange={(e) => {
            if (e.target.value.length <= maxInputChars) setInputText(e.target.value)
          }}
          onKeyDown={handleKeyDown}
          placeholder={hitlPending ? "Confirme ou cancele a ação acima..." : "Envie mensagem para a LIA..."}
          disabled={isCreating || isStreaming || !!hitlPending}
          maxLength={maxInputChars}
          aria-label="Mensagem para a LIA"
          className="flex-1 text-base-ui bg-transparent focus:outline-none text-lia-text-primary placeholder:text-lia-text-disabled disabled:opacity-50 min-w-0"
        />
        <input
          ref={cvFileInputRef}
          type="file"
          accept=".pdf,.docx,.doc,.txt,.xls,.xlsx"
          onChange={handleCvFileAttach}
          className="hidden"
          aria-hidden="true"
        />
        <button
          type="button"
          onClick={handleCvFileButtonClick}
          disabled={isCreating || isStreaming || isScreening || !!hitlPending}
          title="Anexar CV (PDF, DOCX, XLS — máx 10MB)"
          aria-label="Anexar currículo"
          className={cn(
            "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-colors motion-reduce:transition-none",
            isScreening
              ? "text-wedo-cyan-text animate-pulse"
              : "text-lia-text-disabled hover:text-lia-text-secondary disabled:opacity-40"
          )}
        >
          {isScreening
            ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
            : <Paperclip className="w-3.5 h-3.5" />
          }
        </button>
        <AudioRecordButton
          onTranscription={(text) => setInputText(prev => prev ? `${prev} ${text}` : text)}
          className="p-1.5"
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={!canSend}
          aria-label="Enviar mensagem"
          className={cn(
            "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-colors",
            canSend
              ? "bg-wedo-cyan text-white hover:opacity-90"
              : "bg-lia-interactive-active text-lia-text-disabled"
          )}
        >
          {isCreating || isStreaming
            ? <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none text-white" />
            : <Send className="w-3.5 h-3.5" />
          }
        </button>
      </div>
      {inputText.length > maxInputChars * 0.9 && (
        <p className="text-xs text-lia-text-secondary mt-1 text-right">
          {inputText.length}/{maxInputChars}
        </p>
      )}
    </div>
  )
}
