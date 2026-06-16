"use client"

import { useState, useCallback } from "react"

export type ContextType = "text_selection" | "candidate" | "job" | "page"
export type Intent = "answer" | "suggest_rewrite" | "defer"

export interface InlineChatContextData {
  candidate_id?: string
  job_id?: string
  selected_text?: string
  page_url?: string
  page_title?: string
}

export function useInlineChatSubmit() {
  const [answer, setAnswer] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = useCallback(async (
    question: string,
    contextType: ContextType,
    contextData: InlineChatContextData,
    intent: Intent = "answer",
  ) => {
    if (!question.trim() || isLoading) return
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/backend-proxy/inline-chat/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question.trim(),
          context_type: contextType,
          context_data: contextData,
          intent,
        }),
      })
      if (!res.ok) {
        const body = await res.text().catch(() => "")
        console.error("[inline-chat] HTTP", res.status, body)
        setError(`Erro ${res.status}`)
        return
      }
      const data = await res.json()
      const payload = data?.data ?? data
      setAnswer(payload.answer ?? "")
    } catch (err) {
      console.error("[inline-chat] fetch error:", err)
      setError("Sem resposta. Tente no chat.")
    } finally {
      setIsLoading(false)
    }
  }, [isLoading])

  const reset = useCallback(() => {
    setAnswer(null)
    setError(null)
  }, [])

  return { answer, isLoading, error, submit, reset }
}
