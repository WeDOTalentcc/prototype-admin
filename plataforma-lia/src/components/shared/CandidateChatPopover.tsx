"use client"

import { useState, useRef, useCallback, useEffect } from "react"
import { createPortal } from "react-dom"
import { MessageSquareDashed, MessageSquare, Send, ExternalLink, X, Brain } from "lucide-react"
import { useLiaEntitySelection } from "@/hooks/shared/use-lia-entity-selection"

interface CandidateChatPopoverProps {
  candidateId: string | number
  candidateName: string
  children: React.ReactNode
  jobId?: string | number
  className?: string
}

export function CandidateChatPopover({
  candidateId,
  candidateName,
  children,
  jobId,
  className,
}: CandidateChatPopoverProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [question, setQuestion] = useState("")
  const [answer, setAnswer] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // Portal positioning — computed from trigger getBoundingClientRect()
  const [popoverPos, setPopoverPos] = useState<{ bottom: number; left: number } | null>(null)
  // isMounted guard ensures createPortal only runs client-side (no SSR mismatch)
  const [isMounted, setIsMounted] = useState(false)

  const triggerRef = useRef<HTMLDivElement>(null)
  const hoverTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const closeTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const inputRef = useRef<HTMLInputElement>(null)
  const { openEntityChat } = useLiaEntitySelection()

  useEffect(() => {
    setIsMounted(true)
  }, [])

  const openPopover = useCallback(() => {
    clearTimeout(closeTimerRef.current)
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      setPopoverPos({
        // Anchor ABOVE the trigger: distance from bottom of viewport to trigger top, plus gap
        bottom: window.innerHeight - rect.top + 6,
        // Clamp so popover never overflows right edge
        left: Math.min(rect.left, window.innerWidth - 292),
      })
    }
    setIsOpen(true)
    setTimeout(() => inputRef.current?.focus(), 60)
  }, [])

  const scheduleClose = useCallback(() => {
    closeTimerRef.current = setTimeout(() => {
      setIsOpen(false)
    }, 200)
  }, [])

  const handleTriggerEnter = useCallback(() => {
    clearTimeout(hoverTimerRef.current)
    hoverTimerRef.current = setTimeout(openPopover, 420)
  }, [openPopover])

  const handleTriggerLeave = useCallback(() => {
    clearTimeout(hoverTimerRef.current)
    scheduleClose()
  }, [scheduleClose])

  const handlePopoverEnter = useCallback(() => {
    clearTimeout(closeTimerRef.current)
  }, [])

  const handleSubmit = useCallback(async () => {
    if (!question.trim() || isLoading) return
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/backend-proxy/candidates/${candidateId}/quick-ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question.trim(),
          job_id: jobId ? String(jobId) : undefined,
        }),
      })
      if (!res.ok) throw new Error(String(res.status))
      const data = await res.json()
      const payload = data?.data ?? data
      setAnswer(payload.answer ?? "")
      setQuestion("")
    } catch {
      setError("Não foi possível responder. Tente no chat completo.")
    } finally {
      setIsLoading(false)
    }
  }, [question, candidateId, jobId, isLoading])

  const handleOpenFullChat = useCallback(() => {
    setIsOpen(false)
    openEntityChat({ type: "candidate", id: String(candidateId), name: candidateName })
  }, [openEntityChat, candidateId, candidateName])

  const cleanName = candidateName.replace(/^\[DEMO\]\s*/i, "").trim()
  const firstName = cleanName.split(" ")[0] || candidateName.split(" ")[0]

  return (
    <div
      ref={triggerRef}
      className={`relative inline-flex items-center gap-1 group/lia-hover ${className ?? ""}`}
      onMouseEnter={handleTriggerEnter}
      onMouseLeave={handleTriggerLeave}
    >
      {children}

      {/* Hint icon — invisible at rest, subtle on hover */}
      <MessageSquareDashed
        className="w-3 h-3 text-lia-primary opacity-0 group-hover/lia-hover:opacity-50 transition-opacity duration-150 pointer-events-none flex-shrink-0"
        aria-hidden="true"
      />

      {/* Portal: renders into document.body, escapes all overflow/transform stacking contexts */}
      {isMounted && isOpen && popoverPos && createPortal(
        <div
          role="dialog"
          aria-label={`Mini chat sobre ${candidateName}`}
          style={{
            position: "fixed",
            bottom: `${popoverPos.bottom}px`,
            left: `${popoverPos.left}px`,
            zIndex: 99999,
            width: "288px",
          }}
          className="rounded-xl border border-lia-border-default bg-white dark:bg-lia-bg-elevated shadow-lg shadow-black/8 dark:shadow-black/30"
          onMouseEnter={handlePopoverEnter}
          onMouseLeave={scheduleClose}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-lia-border-subtle">
            <div className="flex items-center gap-1.5 min-w-0">
              <Brain className="w-3.5 h-3.5 text-lia-primary flex-shrink-0" />
              <span className="text-xs font-medium text-lia-text-secondary truncate">
                {candidateName}
              </span>
            </div>
            <button
              className="p-0.5 rounded hover:bg-lia-bg-subtle text-lia-text-disabled hover:text-lia-text-secondary transition-colors flex-shrink-0 ml-2"
              onClick={() => setIsOpen(false)}
              aria-label="Fechar"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Answer area */}
          {answer && (
            <div className="px-3 py-2.5 text-xs text-lia-text-primary leading-relaxed max-h-32 overflow-y-auto border-b border-lia-border-subtle">
              {answer}
            </div>
          )}

          {/* Loading dots */}
          {isLoading && (
            <div className="px-3 py-2.5 border-b border-lia-border-subtle flex items-center gap-2">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-lia-primary animate-pulse" />
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-lia-primary animate-pulse [animation-delay:200ms]" />
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-lia-primary animate-pulse [animation-delay:400ms]" />
            </div>
          )}

          {/* Input row */}
          <div className="p-2">
            <div className="flex items-center gap-1.5 rounded-lg bg-lia-bg-subtle px-2.5 py-1.5">
              <input
                ref={inputRef}
                className="flex-1 text-xs bg-transparent outline-none text-lia-text-primary placeholder:text-lia-text-disabled min-w-0"
                placeholder={answer ? "Outra pergunta..." : `Pergunte sobre ${firstName}...`}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSubmit()
                  if (e.key === "Escape") setIsOpen(false)
                }}
                disabled={isLoading}
              />
              <button
                className="shrink-0 text-lia-primary disabled:opacity-30 hover:opacity-70 transition-opacity"
                onClick={handleSubmit}
                disabled={!question.trim() || isLoading}
                aria-label="Enviar pergunta"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
            {error && (
              <p className="text-micro text-status-error mt-1 px-0.5">{error}</p>
            )}
          </div>

          {/* Footer link */}
          <div className="px-3 pb-2.5">
            <button
              className="flex items-center gap-1 text-micro text-lia-primary hover:opacity-70 transition-opacity"
              onClick={handleOpenFullChat}
            >
              <MessageSquare className="w-3 h-3" />
              Ver no chat completo
              <ExternalLink className="w-2.5 h-2.5" />
            </button>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}
