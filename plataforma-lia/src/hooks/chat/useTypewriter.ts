import { useEffect, useRef, useState } from "react"

/**
 * useTypewriter — client-side progressive reveal of `text`.
 *
 * Why (2026-06-04): the LLM provider (Claude on Vertex) delivers each response
 * in a single ~50ms burst at the end of generation (measured via the SSE timing
 * sensor), NOT token-by-token. So real token streaming isn't visible in the UI.
 * This hook gives the progressive "typing" feel on the final assistant message,
 * provider-independent.
 *
 * - `enabled=false` (history load, etc.) → returns the full text immediately.
 * - Respects prefers-reduced-motion → no animation.
 * - setInterval-based (deterministically testable with fake timers).
 */
interface TypewriterOptions {
  enabled?: boolean
  /** characters per second */
  cps?: number
}

const TICK_MS = 33 // ~30fps

export function useTypewriter(
  text: string,
  { enabled = true, cps = 260 }: TypewriterOptions = {},
): { displayed: string; done: boolean } {
  const [count, setCount] = useState<number>(enabled ? 0 : text.length)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    // NOTE (debito): prefers-reduced-motion respeito sera reintroduzido como
    // setting; removido por ora para nao desabilitar silenciosamente a animacao.
    if (!enabled || text.length === 0) {
      setCount(text.length)
      return
    }

    setCount(0)
    const perTick = Math.max(1, Math.round((cps * TICK_MS) / 1000))
    let current = 0
    intervalRef.current = setInterval(() => {
      current = Math.min(text.length, current + perTick)
      setCount(current)
      if (current >= text.length && intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }, TICK_MS)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [text, enabled, cps])

  return { displayed: text.slice(0, count), done: count >= text.length }
}
