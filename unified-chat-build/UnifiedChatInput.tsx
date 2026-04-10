"use client"

import React, { useRef, useCallback, useEffect, useState } from "react"
import { Send, Plus, Loader2, SlidersHorizontal, Paperclip, FileText, XCircle, AtSign, Briefcase, Users } from "lucide-react"
import { cn } from "@/lib/utils"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import type { ChatMode } from "./unified-chat-types"

interface Props {
  mode: ChatMode
  inputText: string
  setInputText: React.Dispatch<React.SetStateAction<string>>
  onSend: () => void
  isStreaming: boolean
  isCreating: boolean
  isDisabled: boolean
  contextPage?: string | null
  attachedFile: File | null
  setAttachedFile: (f: File | null) => void
  fileInputRef: React.RefObject<HTMLInputElement | null>
  onFileButtonClick: () => void
  onFileAttach: (e: React.ChangeEvent<HTMLInputElement>) => void
}

export function UnifiedChatInput({
  mode,
  inputText,
  setInputText,
  onSend,
  isStreaming,
  isCreating,
  isDisabled,
  contextPage,
  attachedFile,
  setAttachedFile,
  fileInputRef,
  onFileButtonClick,
  onFileAttach,
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [showPlusMenu, setShowPlusMenu] = useState(false)
  const isBusy = isStreaming || isCreating

  // Auto-resize textarea
  const adjustHeight = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    const maxH = mode === "floating" ? 120 : 160
    el.style.height = `${Math.min(el.scrollHeight, maxH)}px`
  }, [mode])

  useEffect(() => {
    adjustHeight()
  }, [inputText, adjustHeight])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (!isDisabled && inputText.trim()) onSend()
    }
  }, [isDisabled, inputText, onSend])

  const canSend = !isDisabled && !isBusy && inputText.trim().length > 0
  const showContext = contextPage && contextPage !== "Chat LIA"
  const [isDragOver, setIsDragOver] = useState(false)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file && file.size <= 10 * 1024 * 1024) {
      // Simulate file input change
      const dt = new DataTransfer()
      dt.items.add(file)
      if (fileInputRef.current) {
        fileInputRef.current.files = dt.files
        fileInputRef.current.dispatchEvent(new Event("change", { bubbles: true }))
      }
    }
  }, [fileInputRef])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false)
  }, [])

  return (
    <div
      className={cn(
        "flex-shrink-0 px-4 pb-4 relative",
        mode === "fullscreen" ? "max-w-[720px] mx-auto w-full" : ""
      )}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      {/* Drag overlay */}
      {isDragOver && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-xl border-2 border-dashed border-wedo-cyan bg-wedo-cyan/5">
          <p className="text-sm font-medium text-wedo-cyan font-['Open_Sans',sans-serif]">Solte o arquivo aqui</p>
        </div>
      )}
      {/* Attached file indicator */}
      {attachedFile && (
        <div className="flex items-center gap-2 mb-2 px-3 py-1.5 rounded-md bg-lia-bg-secondary border border-lia-border-subtle">
          <FileText className="w-3.5 h-3.5 text-wedo-cyan flex-shrink-0" />
          <span className="text-xs text-lia-text-primary truncate flex-1 font-['Open_Sans',sans-serif]">
            {attachedFile.name}
          </span>
          <button
            onClick={() => setAttachedFile(null)}
            className="p-0.5 rounded hover:bg-lia-interactive-hover text-lia-text-tertiary hover:text-lia-text-secondary"
            aria-label="Remover arquivo"
          >
            <XCircle className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Input container — Notion-style with cyan focus ring */}
      <div className={cn(
        "rounded-xl border bg-lia-bg-primary transition-colors motion-reduce:transition-none",
        "focus-within:border-wedo-cyan focus-within:ring-1 focus-within:ring-wedo-cyan/30",
        "border-lia-border-subtle"
      )}>
        {/* Context badge row */}
        {showContext && (
          <div className="px-3 pt-2.5">
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-lia-bg-secondary border border-lia-border-subtle text-xs text-lia-text-secondary font-['Open_Sans',sans-serif]">
              {contextPage}
            </span>
          </div>
        )}

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Faça qualquer coisa com a LIA..."
          disabled={isBusy}
          rows={1}
          className={cn(
            "w-full resize-none bg-transparent px-3 py-2.5",
            "text-sm text-lia-text-primary placeholder:text-lia-text-disabled",
            "focus:outline-none disabled:opacity-50",
            "font-['Open_Sans',sans-serif]",
            showContext ? "pt-1.5" : ""
          )}
          aria-label="Mensagem para a LIA"
        />

        {/* Bottom toolbar */}
        <div className="flex items-center justify-between px-3 pb-2.5">
          <div className="flex items-center gap-1">
            {/* Plus menu (Notion-style) */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowPlusMenu(!showPlusMenu)}
                disabled={isBusy}
                className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none disabled:opacity-40"
                title="Adicionar"
                aria-label="Menu de adição"
              >
                <Plus className="w-4 h-4" />
              </button>

              {showPlusMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowPlusMenu(false)} />
                  <div className="absolute left-0 bottom-full mb-1 z-50 w-56 rounded-md border border-lia-border-subtle bg-lia-bg-primary py-1">
                    <button
                      onClick={() => {
                        onFileButtonClick()
                        setShowPlusMenu(false)
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-lia-text-secondary hover:bg-lia-bg-secondary font-['Open_Sans',sans-serif]"
                    >
                      <Paperclip className="w-4 h-4" />
                      Anexar PDF, DOCX ou CSV
                    </button>
                    <button
                      onClick={() => {
                        setInputText(prev => prev + "@")
                        textareaRef.current?.focus()
                        setShowPlusMenu(false)
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-lia-text-secondary hover:bg-lia-bg-secondary font-['Open_Sans',sans-serif]"
                    >
                      <AtSign className="w-4 h-4" />
                      Mencionar vaga ou candidato
                    </button>
                  </div>
                </>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.doc,.txt,.xls,.xlsx,.csv"
              onChange={onFileAttach}
              className="hidden"
              aria-hidden="true"
            />

            {/* Settings/filter */}
            <button
              type="button"
              disabled={isBusy}
              className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none disabled:opacity-40"
              title="Configurações de contexto"
              aria-label="Configurações de conversa"
            >
              <SlidersHorizontal className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-1">
            {/* Auto label (like Notion) */}
            <span className="text-xs text-lia-text-disabled font-['Open_Sans',sans-serif] mr-1">
              Auto
            </span>

            {/* Voice */}
            <AudioRecordButton
              onTranscription={(text) => setInputText(prev => prev ? `${prev} ${text}` : text)}
              className="p-1.5"
            />

            {/* Send */}
            <button
              type="button"
              onClick={onSend}
              disabled={!canSend}
              className={cn(
                "p-1.5 rounded-md transition-colors motion-reduce:transition-none",
                canSend
                  ? "text-wedo-cyan hover:bg-wedo-cyan/10"
                  : "text-lia-text-disabled"
              )}
              aria-label="Enviar mensagem"
            >
              {isBusy
                ? <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                : <Send className="w-4 h-4" />
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
