"use client"

/**
 * useNavigationIntent — Detecta intenção de navegação a partir de mensagem do usuário.
 *
 * Chama POST /api/backend-proxy/navigation-intent e retorna a página sugerida,
 * confiança e texto da sugestão. Usado pelo LiaChatPanel para mostrar link contextual.
 *
 * Threshold de confiança: 0.65 — abaixo disso, não sugere navegação.
 *
 * Compatível com Vue/Nuxt: mapeia para composable useNavigationIntent().
 */

import { useState, useCallback } from "react"

export interface NavigationIntentResult {
  page: string | null
  confidence: number
  hint: string | null
}

// Threshold at which a navigation suggestion is surfaced to the user.
// Below this level the page/hint are zeroed out and no suggestion is shown.
const CONFIDENCE_THRESHOLD = 0.65

export function useNavigationIntent() {
  const [result, setResult] = useState<NavigationIntentResult | null>(null)
  const [isDetecting, setIsDetecting] = useState(false)

  const detect = useCallback(async (message: string): Promise<NavigationIntentResult | null> => {
    if (!message.trim()) return null
    setIsDetecting(true)
    try {
      const res = await fetch("/api/backend-proxy/navigation-intent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      })
      if (!res.ok) return null
      const data = await res.json() as NavigationIntentResult
      const r = data.confidence >= CONFIDENCE_THRESHOLD ? data : { ...data, page: null, hint: null }
      setResult(r)
      return r
    } catch {
      return null
    } finally {
      setIsDetecting(false)
    }
  }, [])

  const clear = useCallback(() => setResult(null), [])

  return { result, isDetecting, detect, clear }
}
