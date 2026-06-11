"use client"

import { useState, useRef, useCallback, useEffect } from "react"
import { createPortal } from "react-dom"
import { MessageSquareDashed, ExternalLink } from "lucide-react"
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
  const [popoverPos, setPopoverPos] = useState<{ bottom: number; left: number } | null>(null)
  const [isMounted, setIsMounted] = useState(false)

  const triggerRef = useRef<HTMLDivElement>(null)
  const hoverTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const closeTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const inputRef = useRef<HTMLInputElement>(null)
  const { openEntityChat } = useLiaEntitySelection()

  useEffect(() => { setIsMounted(true) }, [])

  const openPopover = useCallback(() => {
    clearTimeout(closeTimerRef.current)
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      setPopoverPos({
        bottom: window.innerHeight - rect.top + 6,
        left: Math.min(rect.left, window.innerWidth - 292),
      })
    }
    setIsOpen(true)
    setTimeout(() => inputRef.current?.focus(), 60)
  }, [])

  const scheduleClose = useCallback(() => {
    closeTimerRef.current = setTimeout(() => setIsOpen(false), 200)
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
      if (!res.ok) {
        const body = await res.text().catch(() => "")
        console.error("[quick-ask] HTTP", res.status, "id:", candidateId, body)
        setError(`Erro ${res.status}`)
        return
      }
      const data = await res.json()
      const payload = data?.data ?? data
      setAnswer(payload.answer ?? "")
      setQuestion("")
    } catch (err) {
      console.error("[quick-ask] fetch error:", err)
      setError("Sem resposta. Tente no chat.")
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

      <MessageSquareDashed
        className="w-3 h-3 text-zinc-400 opacity-0 group-hover/lia-hover:opacity-60 transition-opacity duration-150 pointer-events-none flex-shrink-0"
        aria-hidden="true"
      />

      {isMounted && isOpen && popoverPos && createPortal(
        <div
          role="dialog"
          aria-label={`Pergunta rápida sobre ${candidateName}`}
          style={{
            position: "fixed",
            bottom: `${popoverPos.bottom}px`,
            left: `${popoverPos.left}px`,
            zIndex: 99999,
            width: "288px",
          }}
          className="rounded-lg border border-zinc-200 bg-white shadow-lg shadow-black/5"
          onMouseEnter={handlePopoverEnter}
          onMouseLeave={scheduleClose}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Resposta — aparece após envio */}
          {answer && (
            <div className="px-3 pt-3 pb-2.5 text-xs text-zinc-700 leading-relaxed border-b border-zinc-100">
              {answer}
            </div>
          )}

          {/* Loading */}
          {isLoading && (
            <div className="px-3 pt-3 pb-2.5 border-b border-zinc-100 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-300 animate-pulse" />
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-300 animate-pulse [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-300 animate-pulse [animation-delay:300ms]" />
            </div>
          )}

          {/* Input row */}
          <div className="flex items-center px-3 py-2.5 gap-2">
            <input
              ref={inputRef}
              className="flex-1 text-xs text-zinc-800 placeholder:text-zinc-400 bg-transparent outline-none min-w-0"
              placeholder={answer ? `Outra pergunta sobre ${firstName}…` : `Pergunte sobre ${firstName}…`}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSubmit()
                if (e.key === "Escape") setIsOpen(false)
              }}
              disabled={isLoading}
            />
            {question.trim() && !isLoading && (
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
        </div>,
        document.body
      )}
    </div>
  )
}
