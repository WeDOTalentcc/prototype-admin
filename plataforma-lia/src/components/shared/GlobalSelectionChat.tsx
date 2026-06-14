"use client"

import React, { useState, useRef, useCallback, useEffect } from "react"
import { createPortal } from "react-dom"
import { MessageSquareDashed, RefreshCw, ExternalLink, X } from "lucide-react"
import { usePathname } from "next/navigation"
import { useTextSelection } from "@/hooks/shared/use-text-selection"
import { useInlineChatSubmit } from "@/hooks/shared/use-inline-chat-submit"
import { useLiaFloat } from "@/contexts/lia-float-context"

export function GlobalSelectionChat() {
  const { selection, clear: clearSelection } = useTextSelection()
  const pathname = usePathname()
  const { open: openMainChat } = useLiaFloat()
  const { answer, isLoading, error, submit, reset } = useInlineChatSubmit()

  const [isChatOpen, setIsChatOpen] = useState(false)
  const [intent, setIntent] = useState<"answer" | "suggest_rewrite">("answer")
  const [question, setQuestion] = useState("")
  const [isMounted, setIsMounted] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const frozenRef = React.useRef<{ text: string; rect: DOMRect } | null>(null)

  useEffect(() => { setIsMounted(true) }, [])

  // Close on route change
  useEffect(() => {
    setIsChatOpen(false)
    setQuestion("")
    clearSelection()
    reset()
  }, [pathname]) // eslint-disable-line react-hooks/exhaustive-deps

  const openChat = useCallback((chosenIntent: "answer" | "suggest_rewrite") => {
    setIntent(chosenIntent)
    frozenRef.current = { text: selection.text, rect: selection.rect! }
    setIsChatOpen(true)
    reset()
    setQuestion("")
    setTimeout(() => inputRef.current?.focus(), 60)
  }, [reset])

  const handleClose = useCallback(() => {
    setIsChatOpen(false)
    setQuestion("")
    reset()
    clearSelection()
    window.getSelection()?.removeAllRanges()
  }, [clearSelection, reset])

  const handleSubmit = useCallback(async () => {
    if (isLoading) return
    const q = question.trim() ||
      (intent === "suggest_rewrite" ? "Reescreva este trecho com linguagem mais clara e inclusiva." : "")
    if (!q) return
    await submit(q, "text_selection", {
      selected_text: frozenRef.current?.text ?? selection.text,
      page_url: pathname,
    }, intent)
    setQuestion("")
  }, [question, intent, isLoading, submit, pathname])

  const handleOpenFullChat = useCallback(() => {
    handleClose()
    openMainChat()
  }, [handleClose, openMainChat])

  if (!isMounted) return null
  if (!isChatOpen && (!selection.isActive || !selection.rect)) return null

  const rect = (isChatOpen ? frozenRef.current?.rect : null) ?? selection.rect
  // Toolbar: appears just above the selection
  const toolbarStyle: React.CSSProperties = {
    position: "fixed",
    top: Math.max(8, rect.top - 40),
    left: Math.min(rect.left, window.innerWidth - 220),
    zIndex: 99998,
  }
  // Chat popover: appears above selection, anchored left
  const chatStyle: React.CSSProperties = {
    position: "fixed",
    top: Math.max(8, rect.top - 8),
    transform: "translateY(-100%)",
    left: Math.min(rect.left, window.innerWidth - 292),
    zIndex: 99999,
    width: "288px",
  }

  return createPortal(
    <>
      {/* Toolbar — dark pill shown on selection */}
      {!isChatOpen && (
        <div
          style={toolbarStyle}
          className="flex items-center gap-0 bg-zinc-900 rounded-md shadow-lg overflow-hidden"
          onMouseDown={(e) => e.preventDefault()}
        >
          <button
            className="flex items-center gap-1.5 text-[11px] text-zinc-200 hover:text-white hover:bg-zinc-700 px-2.5 py-1.5 transition-colors"
            onClick={() => openChat("answer")}
          >
            <MessageSquareDashed className="w-3 h-3" />
            Perguntar
          </button>
          <div className="w-px h-4 bg-zinc-700 shrink-0" />
          <button
            className="flex items-center gap-1.5 text-[11px] text-zinc-200 hover:text-white hover:bg-zinc-700 px-2.5 py-1.5 transition-colors"
            onClick={() => openChat("suggest_rewrite")}
          >
            <RefreshCw className="w-3 h-3" />
            Reescrever
          </button>
        </div>
      )}

      {/* Chat popover */}
      {isChatOpen && (
        <div
          role="dialog"
          aria-label="LIA — chat inline"
          style={chatStyle}
          className="rounded-lg border border-zinc-200 bg-white shadow-lg shadow-black/5"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Selected text preview */}
          <div className="px-3 pt-2.5 pb-2 border-b border-zinc-100 flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <p className="text-[10px] text-zinc-400 mb-0.5">
                {intent === "suggest_rewrite" ? "Reescrever:" : "Sobre:"}
              </p>
              <p className="text-[11px] text-zinc-500 line-clamp-2 italic leading-relaxed">
                "{(frozenRef.current?.text ?? selection.text).slice(0, 100)}{(frozenRef.current?.text ?? selection.text).length > 100 ? "…" : ""}"
              </p>
            </div>
            <button
              className="shrink-0 text-zinc-400 hover:text-zinc-600 transition-colors mt-0.5"
              onClick={handleClose}
              aria-label="Fechar"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Answer */}
          {answer && (
            <div className="px-3 pt-2.5 pb-2 text-xs text-zinc-700 leading-relaxed border-b border-zinc-100">
              {answer}
            </div>
          )}

          {/* Loading */}
          {isLoading && (
            <div className="px-3 pt-2.5 pb-2 border-b border-zinc-100 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-300 animate-pulse" />
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-300 animate-pulse [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-300 animate-pulse [animation-delay:300ms]" />
            </div>
          )}

          {/* Input */}
          <div className="flex items-center px-3 py-2.5 gap-2">
            <input
              ref={inputRef}
              className="flex-1 text-xs text-zinc-800 placeholder:text-zinc-400 bg-transparent outline-none min-w-0"
              placeholder={
                intent === "suggest_rewrite"
                  ? "Instrução (opcional)…"
                  : "Pergunte sobre este trecho…"
              }
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSubmit()
                if (e.key === "Escape") handleClose()
              }}
              disabled={isLoading}
            />
            {!isLoading && (intent === "suggest_rewrite" || question.trim()) && (
              <span className="text-[10px] text-zinc-400 border border-zinc-200 rounded px-1.5 py-0.5 shrink-0 select-none leading-none">
                ↵
              </span>
            )}
          </div>

          {/* Footer */}
          <div className="px-3 pb-2.5 flex items-center justify-between">
            {error
              ? <span className="text-[10px] text-zinc-400">{error}</span>
              : <span />
            }
            <button
              className="flex items-center gap-1 text-[10px] text-zinc-400 hover:text-zinc-600 transition-colors ml-auto"
              onClick={handleOpenFullChat}
            >
              Chat completo
              <ExternalLink className="w-2.5 h-2.5" />
            </button>
          </div>
        </div>
      )}
    </>,
    document.body
  )
}
