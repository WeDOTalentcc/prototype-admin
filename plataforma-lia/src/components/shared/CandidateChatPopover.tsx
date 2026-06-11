"use client"

import { useState, useRef, useCallback } from "react"
import { MessageSquareDashed, MessageSquare, Send, ExternalLink, X, Sparkles } from "lucide-react"
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
  const hoverTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const closeTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const inputRef = useRef<HTMLInputElement>(null)
  const { openEntityChat } = useLiaEntitySelection()

  const openPopover = useCallback(() => {
    clearTimeout(closeTimerRef.current)
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

  const firstName = candidateName.split(" ")[0]

  return (
    <div
      className={`relative inline-flex items-center gap-1 group/lia-hover ${className ?? ""}`}
      onMouseEnter={handleTriggerEnter}
      onMouseLeave={handleTriggerLeave}
    >
      {children}

      {/* Hint icon — só aparece no hover, invisible at rest */}
      <MessageSquareDashed
        className="w-3 h-3 text-lia-primary opacity-0 group-hover/lia-hover:opacity-50 transition-opacity duration-150 pointer-events-none flex-shrink-0"
        aria-hidden="true"
      />

      {isOpen && (
        <div
          role="dialog"
          aria-label={`Mini chat sobre ${candidateName}`}
          className="absolute top-full left-0 z-[9999] mt-1.5 w-72 rounded-xl border border-lia-border-default bg-white dark:bg-lia-bg-elevated shadow-lg shadow-black/8 dark:shadow-black/30"
          onMouseEnter={handlePopoverEnter}
          onMouseLeave={scheduleClose}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-lia-border-subtle">
            <div className="flex items-center gap-1.5 min-w-0">
              <Sparkles className="w-3.5 h-3.5 text-lia-primary flex-shrink-0" />
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

          {/* Loading */}
          {isLoading && (
            <div className="px-3 py-2.5 text-xs text-lia-text-disabled border-b border-lia-border-subtle flex items-center gap-2">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-lia-primary animate-pulse" />
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-lia-primary animate-pulse [animation-delay:200ms]" />
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-lia-primary animate-pulse [animation-delay:400ms]" />
            </div>
          )}

          {/* Input */}
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

          {/* Footer */}
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
        </div>
      )}
    </div>
  )
}
