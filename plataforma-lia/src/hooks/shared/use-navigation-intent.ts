"use client"

/**
 * useNavigationIntent — Detecta intenção de navegação a partir de mensagem do usuário.
 *
 * Chama POST /api/backend-proxy/navigation-intent e retorna a página sugerida,
 * confiança, hint e o **modo de dispatch** desejado:
 *
 *  - `mode: "ask"`     — emitir o evento `lia:navigation-hint` e deixar a
 *                        LIA perguntar (no chat) se o recrutador quer ir
 *                        para a página sugerida. Padrão quando o usuário
 *                        está em qualquer rota que NÃO seja a página alvo.
 *  - `mode: "navigate"`— compatibilidade legacy (callers diretos). O hook
 *                        em si nunca devolve esse modo; existe apenas para
 *                        outros emissores do mesmo evento.
 *  - `page: null`      — supressão: o usuário já está na página alvo (ex.:
 *                        já em `/chat` e a sugestão é "Vagas" para abrir o
 *                        wizard, que roda no próprio chat fullscreen).
 *
 * Threshold de confiança: 0.65 — abaixo disso, não sugere navegação.
 *
 * Task #1165: tornar context-aware. Antes só comparávamos a confiança e
 * disparávamos `router.push` cego. Isso arrancava o recrutador da tela
 * `/chat` durante as etapas iniciais (conversacionais) do wizard de
 * criação de vaga. Agora o hook consulta `window.location.pathname` e:
 *   1. Se já estamos em `/chat` e o alvo é a página de vagas, devolve
 *      `page=null` (sem dispatch).
 *   2. Caso contrário, anota `mode="ask"` para que o `DashboardApp`
 *      proponha a transição no chat ao invés de redirecionar.
 *
 * Compatível com Vue/Nuxt: mapeia para composable useNavigationIntent().
 */

import { useState, useCallback } from "react"

export type NavigationIntentMode = "ask" | "navigate"

export interface NavigationIntentResult {
  page: string | null
  confidence: number
  hint: string | null
  /**
   * Como o consumidor do evento `lia:navigation-hint` deve agir.
   * `undefined` é tratado como `"navigate"` (legacy) pelos handlers.
   */
  mode?: NavigationIntentMode
}

// Threshold at which a navigation suggestion is surfaced to the user.
// Below this level the page/hint are zeroed out and no suggestion is shown.
const CONFIDENCE_THRESHOLD = 0.65

/**
 * Pages whose "ambiente dedicado" pode ser substituído pelo `/chat`
 * fullscreen — i.e., se o recrutador já está no chat grande, não vale a
 * pena arrastá-lo para essas rotas: o fluxo (ex.: wizard de criação de
 * vaga) roda 100% via conversa nas primeiras etapas.
 *
 * Vive como const exportada para que os testes possam afirmar o
 * contrato sem duplicar a lista.
 */
export const CHAT_FIRST_TARGET_PAGES: ReadonlySet<string> = new Set([
  "Vagas",
])

function getCurrentPathname(): string {
  if (typeof window === "undefined") return ""
  try {
    return window.location.pathname || ""
  } catch {
    return ""
  }
}

/**
 * Pure helper — decide o `mode` (ou suprime via `page=null`) a partir da
 * resposta do backend e da rota atual. Exportada para os testes
 * unitários cobrirem os 3 ramos (já-em-/chat → suprime; outra rota →
 * ask; sem sugestão → passthrough).
 */

/**
 * Frases imperativas de navegação — o recrutador está MANDANDO ir para uma
 * página, não perguntando. Neste caso, navegamos direto sem pedir confirmação.
 * Exemplos: "me leve para vagas", "vai para pipeline", "abre o kanban".
 */
const NAV_IMPERATIVE_RE =
  /(me\s+lev[ae]\w*|lev[ae]-?me|v[aá]\s+par[ao]|vamos\s+par[ao]|ir?\s+par[ao]|abr[ae]\s|acess[ae]\w*|entr[ae]\s+em|naveg[ae]\s+par[ao]|mostrar?\s+[ao]?s?\s*p[áa]gin)/i

export function resolveNavigationIntentMode(
  raw: NavigationIntentResult,
  pathname: string,
  originalMessage?: string,
): NavigationIntentResult {
  if (raw.confidence < CONFIDENCE_THRESHOLD || !raw.page) {
    return { ...raw, page: null, hint: null }
  }
  const isOnChat = /\/chat(?:\/|$)/.test(pathname)
  if (isOnChat && CHAT_FIRST_TARGET_PAGES.has(raw.page)) {
    // Already on the chat fullscreen — wizard roda aqui mesmo. Não
    // emitir hint para não disparar router.push e arrancar o usuário.
    return { ...raw, page: null, hint: null, mode: undefined }
  }
  // Imperativo explícito → navegação direta sem confirmação.
  if (originalMessage && NAV_IMPERATIVE_RE.test(originalMessage)) {
    return { ...raw, mode: "navigate" }
  }
  return { ...raw, mode: "ask" }
}

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
      const r = resolveNavigationIntentMode(data, getCurrentPathname(), message)
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
