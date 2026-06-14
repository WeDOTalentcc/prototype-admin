"use client"

import React, { useRef, useCallback, useEffect, useState } from "react"
import { Send, Plus, Loader2, Paperclip, FileText, XCircle, AtSign, Lightbulb } from "lucide-react"
import { cn } from "@/lib/utils"
import { useTranslations } from 'next-intl'
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { ChatSuggestionsPanel } from "./ChatSuggestionsPanel"
import { useMentionAutocomplete } from "./useMentionAutocomplete"
import { useSlashCommands } from "./useSlashCommands"
import { MentionDropdown } from "./MentionDropdown"
import { SlashCommandDropdown } from "./SlashCommandDropdown"
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
  /** Triggered when a slash command is selected that executes a UI action (e.g. nova-conversa). */
  onExecuteSlashCommand?: (commandId: string) => void
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
  onExecuteSlashCommand,
}: Props) {
  const t = useTranslations('chat.input')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [showPlusMenu, setShowPlusMenu] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [cursorPosition, setCursorPosition] = useState(0)
  const [isDragOver, setIsDragOver] = useState(false)
  const isBusy = isStreaming || isCreating

  // Devolve o foco ao campo assim que a LIA termina de responder. O textarea
  // fica `disabled` enquanto isBusy (streaming/creating); ao desabilitar, o
  // browser tira o foco e NÃO o devolve sozinho ao reabilitar — por isso o
  // recrutador precisava clicar de novo. Refocamos só na transição
  // ocupado -> ocioso (não no mount) para não roubar foco indevidamente.
  const wasBusyRef = useRef(false)
  useEffect(() => {
    if (wasBusyRef.current && !isBusy && !isDisabled) {
      textareaRef.current?.focus()
    }
    wasBusyRef.current = isBusy
  }, [isBusy, isDisabled])

  // --- @mention autocomplete ---
  const onInsertMention = useCallback((triggerStart: number, mentionToken: string) => {
    setInputText(prev => {
      const before = prev.slice(0, triggerStart)
      const after = prev.slice(cursorPosition)
      return before + mentionToken + " " + after
    })
    setTimeout(() => {
      const el = textareaRef.current
      if (el) {
        const newPos = triggerStart + mentionToken.length + 1
        el.selectionStart = newPos
        el.selectionEnd = newPos
        setCursorPosition(newPos)
        el.focus()
      }
    }, 0)
  }, [setInputText, cursorPosition])

  const mention = useMentionAutocomplete({
    inputText,
    selectionStart: cursorPosition,
    onInsertMention,
  })

  // --- /slash commands ---
  const onExecuteCommand = useCallback((commandId: string) => {
    setInputText("")
    onExecuteSlashCommand?.(commandId)
  }, [setInputText, onExecuteSlashCommand])

  const onPrefillInput = useCallback((text: string) => {
    setInputText(prev => {
      const before = prev.slice(0, cursorPosition)
      const lastSlash = before.lastIndexOf("/")
      // Mirror the trigger rule in useInputDropdown.checkTrigger:
      // the slash must sit at the start of the input or be preceded
      // by whitespace. Lets the user fire `/cmd` mid-sentence.
      const validAnchor =
        lastSlash === 0 || (lastSlash > 0 && /\s/.test(before[lastSlash - 1] ?? ""))
      if (lastSlash < 0 || !validAnchor) return text
      return prev.slice(0, lastSlash) + text + prev.slice(cursorPosition)
    })
    setTimeout(() => {
      const el = textareaRef.current
      if (el) {
        el.focus()
        const newPos = el.value.length
        el.selectionStart = newPos
        el.selectionEnd = newPos
        setCursorPosition(newPos)
      }
    }, 0)
  }, [setInputText, cursorPosition])

  const slash = useSlashCommands({
    inputText,
    selectionStart: cursorPosition,
    onExecuteCommand,
    onPrefillInput,
  })

  // Stable destructured close handlers for mutex effects.
  const { close: closeMention } = mention
  const { close: closeSlash } = slash

  // Mutex: when /slash or @mention opens, close manual popovers.
  useEffect(() => {
    if (mention.isOpen || slash.isOpen) {
      setShowPlusMenu(false)
      setShowSuggestions(false)
    }
  }, [mention.isOpen, slash.isOpen])

  // Mutex: when manual popover opens, close the autocomplete dropdowns.
  useEffect(() => {
    if (showPlusMenu || showSuggestions) {
      closeMention()
      closeSlash()
    }
  }, [showPlusMenu, showSuggestions, closeMention, closeSlash])

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
    // Delegate to dropdowns when open (Arrow/Enter/Escape).
    if (mention.isOpen && mention.handleKeyDown(e)) return
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

  const handleTextareaSelect = useCallback((e: React.SyntheticEvent<HTMLTextAreaElement>) => {
    setCursorPosition((e.target as HTMLTextAreaElement).selectionStart ?? 0)
  }, [])

  const canSend = !isDisabled && !isBusy && inputText.trim().length > 0
  const showContext = contextPage && contextPage !== "Conversar"

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file && file.size <= 10 * 1024 * 1024) {
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
        "flex-shrink-0 px-4 pb-4 relative z-20",
        mode === "fullscreen" ? "max-w-[720px] mx-auto w-full" : ""
      )}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      {/* Drag overlay */}
      {isDragOver && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-md border-2 border-dashed border-wedo-cyan bg-wedo-cyan/5">
          <p className="text-sm font-medium text-lia-text-secondary">{t('dropFileHere')}</p>
        </div>
      )}
      {/* Attached file indicator */}
      {attachedFile && (
        <div className="flex items-center gap-2 mb-2 px-3 py-1.5 rounded-md bg-lia-bg-secondary border border-lia-border-subtle">
          <FileText className="w-3.5 h-3.5 text-wedo-cyan flex-shrink-0" />
          <span className="text-xs text-lia-text-primary truncate flex-1">
            {attachedFile.name}
          </span>
          <button
            onClick={() => setAttachedFile(null)}
            className="p-0.5 rounded hover:bg-lia-interactive-hover text-lia-text-tertiary hover:text-lia-text-secondary"
            aria-label={t('removeFile')}
          >
            <XCircle className="w-3 h-3" />
          </button>
        </div>
      )}

      <ChatSuggestionsPanel
        isOpen={showSuggestions}
        onClose={() => setShowSuggestions(false)}
        onSelectQuery={(query) => {
          setInputText(query)
          textareaRef.current?.focus()
        }}
        mode={mode}
      />

      {/* Input container — Notion-style with cyan focus ring */}
      <div className={cn(
        "relative rounded-md border bg-lia-bg-primary transition-colors motion-reduce:transition-none",
        "focus-within:border-wedo-cyan focus-within:ring-1 focus-within:ring-wedo-cyan/30",
        "border-lia-border-subtle"
      )}>
        {/* Context badge row */}
        {showContext && (
          <div className="px-3 pt-2.5">
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-lia-bg-secondary border border-lia-border-subtle text-micro text-lia-text-secondary">
              {contextPage}
            </span>
          </div>
        )}

        {/* Textarea */}
        <textarea data-testid="chat-input"
          ref={textareaRef}
          value={inputText}
          onChange={handleChange}
          onSelect={handleTextareaSelect}
          onClick={handleTextareaSelect}
          onKeyDown={handleKeyDown}
          placeholder={t('placeholder')}
          disabled={isBusy}
          rows={1}
          className={cn(
            "w-full resize-none bg-transparent px-3 py-2.5",
            "text-sm text-lia-text-primary placeholder:text-lia-text-disabled",
            "focus:outline-none disabled:opacity-50",
            "",
            showContext ? "pt-1.5" : ""
          )}
          aria-label={t('messageLabel')}
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
                title={t('addMenu')}
                aria-label={t('addMenuLabel')}
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
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-lia-text-secondary hover:bg-lia-bg-secondary"
                    >
                      <Paperclip className="w-4 h-4" />
                      {t('attachFile')}
                    </button>
                    <button
                      onClick={() => {
                        setInputText(prev => prev + "@")
                        textareaRef.current?.focus()
                        setShowPlusMenu(false)
                        setTimeout(() => {
                          const el = textareaRef.current
                          if (el) setCursorPosition(el.selectionStart ?? el.value.length)
                        }, 0)
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-lia-text-secondary hover:bg-lia-bg-secondary"
                    >
                      <AtSign className="w-4 h-4" />
                      {t('mentionJobCandidate')}
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

            <button
              type="button"
              onClick={() => setShowSuggestions(!showSuggestions)}
              disabled={isBusy}
              className={cn(
                "p-1.5 rounded-md transition-colors motion-reduce:transition-none disabled:opacity-40",
                showSuggestions
                  ? "text-wedo-cyan-text bg-wedo-cyan/10"
                  : "text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover"
              )}
              title={t('suggestionsTitle')}
              aria-label={t('suggestionsLabel')}
            >
              <Lightbulb className="w-4 h-4" />
            </button>

          </div>

          <div className="flex items-center gap-1">
            {/* Onda 4-P2-1 (2026-05-24): Auto label decorativo removido (era
                placeholder sem onClick/state; routing já é determinístico via
                domain_hint/intent_hint no orchestrator). */}

            {/* Voice */}
            <AudioRecordButton
              onTranscription={(text) => setInputText(prev => prev ? `${prev} ${text}` : text)}
              className="p-1.5"
            />

            {/* Send */}
            <button
              data-testid="chat-send-button"
              type="button"
              onClick={onSend}
              disabled={!canSend}
              className={cn(
                "p-1.5 rounded-md transition-colors motion-reduce:transition-none",
                canSend
                  ? "text-wedo-cyan-text hover:bg-wedo-cyan/10"
                  : "text-lia-text-disabled"
              )}
              aria-label={t('sendLabel')}
            >
              {isBusy
                ? <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                : <Send className="w-4 h-4" />
              }
            </button>
          </div>
        </div>

        {/* @mention dropdown — anchored above input container */}
        {mention.isOpen && (
          <MentionDropdown
            items={mention.items}
            selectedIndex={mention.selectedIndex}
            onSelect={mention.selectItem}
          />
        )}

        {/* /slash command dropdown — anchored above input container */}
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
