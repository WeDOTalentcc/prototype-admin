"use client"

/**
 * useProactiveActionRouter — Listens to `lia:proactive-action` events dispatched
 * by ProactiveHintsList and routes each action to the appropriate handler.
 *
 * Design (PARTE E decisions):
 *   - Navigation actions → re-dispatch `lia:navigation-hint` (reuses existing listener)
 *   - Data-modifying actions → POST /api/v1/proactive-actions/accept (E.4)
 *   - Chat-delegating actions → send a proactive message into the active chat
 *
 * Click on the card button IS the authorization — no second confirmation dialog.
 * Destructive actions use dry-run preview (handled server-side by E.4 endpoint).
 */
import { useEffect } from "react"

export interface ProactiveActionDetail {
  type: string
  action: string | null
  metadata: Record<string, unknown>
}

export interface ProactiveActionRouterOptions {
  /** Callback that sends a proactive message as if the user typed it.
   *  Wire to the active chat's send function (useChatSocket or expanded-chat). */
  sendChatMessage?: (message: string) => void
  /** Optional company_id for REST action calls; falls back to JWT if omitted. */
  companyId?: string
}

const NAVIGATION_ACTIONS = new Set<string>([
  "navigate_to_settings",
])

// Actions that are best handled via a chat message (LIA's agent loop picks up the tool)
const CHAT_DELEGATE_PROMPTS: Record<string, (meta: Record<string, unknown>) => string> = {
  suggest_recruiting_policy: () =>
    "Sim, por favor sugira uma política de recrutamento baseline para nossa empresa.",
  culture_onboarding: () =>
    "Sim, quero configurar o perfil cultural da empresa agora. Pode me fazer as perguntas.",
  batch_enrich_contacts: (meta) => {
    const count = typeof meta.count === "number" ? meta.count : 0
    return count > 0
      ? `Sim, enriqueça em lote os ${count} candidatos sem contato.`
      : "Sim, enriqueça em lote os candidatos sem contato."
  },
  suggest_screening_questions: () =>
    "Sim, sugira um conjunto de perguntas de triagem para esta vaga.",
  import_benefits: () =>
    "Sim, quero importar benefícios. Pode me guiar ou aceitar uma lista.",
}

// Actions that go straight to REST endpoint (E.4) for server-side execution with preview
const REST_ACTIONS = new Set<string>([
  "request_website_and_scrape",
])

async function acceptViaRest(
  action: string,
  type: string,
  metadata: Record<string, unknown>,
): Promise<{ success: boolean; message?: string; data?: unknown } | null> {
  try {
    const res = await fetch("/api/backend-proxy/proactive-actions?path=accept-hint", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, hint_type: type, metadata }),
    })
    if (!res.ok) {
      console.error("[ProactiveActionRouter] REST accept failed:", res.status)
      return null
    }
    return await res.json()
  } catch (err) {
    console.error("[ProactiveActionRouter] REST accept error:", err)
    return null
  }
}

export function useProactiveActionRouter(opts: ProactiveActionRouterOptions = {}): void {
  const { sendChatMessage } = opts

  useEffect(() => {
    const handler = async (ev: Event) => {
      const detail = (ev as CustomEvent<ProactiveActionDetail>).detail
      if (!detail || !detail.action) return

      const { type, action, metadata = {} } = detail

      // 1. Navigation actions — reuse existing lia:navigation-hint listener
      if (NAVIGATION_ACTIONS.has(action)) {
        const target =
          (metadata as { target_page?: string }).target_page === "settings"
            ? "Configurações"
            : (metadata as { page?: string }).page || "Configurações"
        window.dispatchEvent(
          new CustomEvent("lia:navigation-hint", {
            detail: { page: target, hint: null },
          }),
        )
        return
      }

      // 2. Chat-delegating actions — push a proactive message into the chat
      if (action in CHAT_DELEGATE_PROMPTS) {
        const msg = CHAT_DELEGATE_PROMPTS[action](metadata)
        if (sendChatMessage) {
          sendChatMessage(msg)
        } else {
          // Fallback: broadcast an event that chat listeners can pick up
          window.dispatchEvent(
            new CustomEvent("lia:send-proactive-message", { detail: { message: msg } }),
          )
        }
        return
      }

      // 3. REST actions — delegate to backend endpoint (E.4)
      if (REST_ACTIONS.has(action)) {
        // For request_website_and_scrape: prompt user for URL first
        let enrichedMeta = metadata
        if (action === "request_website_and_scrape") {
          const url = window.prompt(
            "Informe o site da sua empresa para eu preencher automaticamente " +
              "(nome, setor, cultura, benefícios):",
            "",
          )
          if (!url || !url.trim()) return
          enrichedMeta = { ...metadata, url: url.trim() }
        }
        const result = await acceptViaRest(action, type, enrichedMeta)
        if (result?.success && sendChatMessage && result.message) {
          // Surface backend's response in the chat so user sees what happened
          sendChatMessage(result.message)
        }
        return
      }

      // 4. Unknown action — log for future coverage
      console.warn("[ProactiveActionRouter] no handler for action:", action, detail)
    }

    window.addEventListener("lia:proactive-action", handler)
    return () => window.removeEventListener("lia:proactive-action", handler)
  }, [sendChatMessage])
}
