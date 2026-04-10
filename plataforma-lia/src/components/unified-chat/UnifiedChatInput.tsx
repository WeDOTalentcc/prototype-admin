"use client"

import React, { useRef, useCallback, useEffect, useState } from "react"
import { Send, Plus, Loader2, SlidersHorizontal, Paperclip, FileText, XCircle, AtSign, Globe, FileSearch } from "lucide-react"
import { cn } from "@/lib/utils"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import type { ChatMode } from "./unified-chat-types"
import { useMentionAutocomplete } from "./useMentionAutocomplete"
import { useSlashCommands } from "./useSlashCommands"
import { MentionDropdown } from "./MentionDropdown"
import { SlashCommandDropdown } from "./SlashCommandDropdown"

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
  currentScope?: "page" | "universal"
  onScopeChange?: (scope: "page" | "universal") => void
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
  currentScope = "page",
  onScopeChange,
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [showPlusMenu, setShowPlusMenu] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [cursorPosition, setCursorPosition] = useState(0)
  const isBusy = isStreaming || isCreating

  // --- Mention autocomplete ---
  const mention = useMentionAutocomplete({
    inputText,
    selectionStart: cursorPosition,
    onInsertMention: useCallback((triggerStart: number, mentionToken: string) => {
      setInputText(prev => {
        const before = prev.slice(0, triggerStart)
        const after = prev.slice(cursorPosition)
        return before + mentionToken + " " + after
      })
      // Move cursor after the inserted mention
      setTimeout(() => {
        const el = textareaRef.current
        if (el) {
          const newPos = triggerStart + mentionToken.length + 1
          el.selectionStart = newPos
          el.selectionEnd = newPos
          setCursorPosition(newPos)
        }
      }, 0)
    }, [setInputText, cursorPosition]),
  })

  // --- Slash commands ---
  const slash = useSlashCommands({
    inputText,
    selectionStart: cursorPosition,
    onExecuteCommand: useCallback((commandId: string) => {
      if (commandId === "nova-conversa") {
        setInputText("")
        // Could dispatch a "new conversation" event here
      }
    }, [setInputText]),
    onPrefillInput: useCallback((text: string) => {
      setInputText(text)
      setTimeout(() => {
        const el = textareaRef.current
        if (el) {
          el.selectionStart = text.length
          el.selectionEnd = text.length
          setCursorPosition(text.length)
          el.focus()
        }
      }, 0)
    }, [setInputText]),
  })

  // Close other dropdowns when one opens (mutex)
  useEffect(() => {
    if (mention.isOpen) {
      setShowPlusMenu(false)
      setShowSettings(false)
    }
  }, [mention.isOpen])

  useEffect(() => {
    if (slash.isOpen) {
      setShowPlusMenu(false)
      setShowSettings(false)
    }
  }, [slash.isOpen])

  useEffect(() => {
    if (showPlusMenu) {
      mention.close()
      slash.close()
    }
  }, [showPlusMenu])

  useEffect(() => {
    if (showSettings) {
      mention.close()
      slash.close()
    }
  }, [showSettings])

  // Auto-resize textarea
  const adjustHeight = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    const maxH = mode === "floating" ? 120 : 160
    el.style.height = Math.min(el.scrollHeight, maxH) + "px"
  }, [mode])

  useEffect(() => {
    adjustHeight()
  }, [inputText, adjustHeight])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Delegate to mention dropdown first
    if (mention.isOpen && mention.handleKeyDown(e)) return
    // Then slash commands
    if (slash.isOpen && slash.handleKeyDown(e)) return

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (!isDisabled && inputText.trim()) onSend()
    }
  }, [mention, slash, isDisabled, inputText, onSend])

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value)
    setCursorPosition(e.target.selectionStart ?? 0)
  }, [setInputText])

  const handleSelect = useCallback((e: React.SyntheticEvent<HTMLTextAreaElement>) => {
    setCursorPosition((e.target as HTMLTextAreaElement).selectionStart ?? 0)
  }, [])

  const canSend = !isDisabled && !isBusy && inputText.trim().length > 0
  const showContext = contextPage && contextPage !== "Chat LIA"

  return (
    <div className={cn(
      "flex-shrink-0 px-4 pb-4",
      mode === "fullscreen" ? "max-w-[720px] mx-auto w-full" : ""
    )}>
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

      {/* Input container */}
      <div className={cn(
        "relative rounded-xl border bg-lia-bg-primary transition-colors motion-reduce:transition-none",
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
          onChange={handleChange}
          onSelect={handleSelect}
          onClick={handleSelect}
          onKeyDown={handleKeyDown}
          placeholder="Faca qualquer coisa com a LIA..."
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
                aria-label="Menu de adicao"
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
                        setTimeout(() => {
                          const el = textareaRef.current
                          if (el) setCursorPosition(el.selectionStart)
                        }, 0)
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-lia-text-secondary hover:bg-lia-bg-secondary font-['Open_Sans',sans-serif]"
                    >
                      <AtSign className="w-4 h-4" />
                      Inserir @mencao
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

            {/* Settings/scope popover */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowSettings(!showSettings)}
                disabled={isBusy}
                className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none disabled:opacity-40"
                title="Configuracoes de contexto"
                aria-label="Configuracoes de conversa"
              >
                <SlidersHorizontal className="w-4 h-4" />
              </button>

              {showSettings && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowSettings(false)} />
                  <div className="absolute left-0 bottom-full mb-1 z-50 w-52 rounded-md border border-lia-border-subtle bg-lia-bg-primary py-1">
                    <div className="px-3 py-1.5 text-xs text-lia-text-disabled font-['Open_Sans',sans-serif]">
                      Escopo do contexto
                    </div>
                    <button
                      onClick={() => {
                        onScopeChange?.("page")
                        setShowSettings(false)
                      }}
                      className={cn(
                        "w-full flex items-center gap-2.5 px-3 py-2 text-sm font-['Open_Sans',sans-serif]",
                        "hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none",
                        currentScope === "page" ? "text-lia-text-primary" : "text-lia-text-secondary"
                      )}
                    >
                      <FileSearch className="w-4 h-4" />
                      <span className="flex-1 text-left">Contexto da pagina</span>
                      {currentScope === "page" && (
                        <span className="text-wedo-cyan text-xs">&#10003;</span>
                      )}
                    </button>
                    <button
                      onClick={() => {
                        onScopeChange?.("universal")
                        setShowSettings(false)
                      }}
                      className={cn(
                        "w-full flex items-center gap-2.5 px-3 py-2 text-sm font-['Open_Sans',sans-serif]",
                        "hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none",
                        currentScope === "universal" ? "text-lia-text-primary" : "text-lia-text-secondary"
                      )}
                    >
                      <Globe className="w-4 h-4" />
                      <span className="flex-1 text-left">Universal</span>
                      {currentScope === "universal" && (
                        <span className="text-wedo-cyan text-xs">&#10003;</span>
                      )}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1">
            {/* Auto label (like Notion) */}
            <span className="text-xs text-lia-text-disabled font-['Open_Sans',sans-serif] mr-1">
              Auto
            </span>

            {/* Voice */}
            <AudioRecordButton
              onTranscription={(text) => setInputText(prev => prev ? prev + " " + text : text)}
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

        {/* Mention dropdown - positioned above the input container */}
        {mention.isOpen && (
          <MentionDropdown
            items={mention.items}
            selectedIndex={mention.selectedIndex}
            onSelect={mention.selectItem}
          />
        )}

        {/* Slash command dropdown - positioned above the input container */}
        {slash.isOpen && (
          <SlashCommandDropdown
            items={slash.items}
            selectedIndex={slash.selectedIndex}
            onSelect={slash.selectItem}
          />
        )}
      </div>
    </div>
  )
}
