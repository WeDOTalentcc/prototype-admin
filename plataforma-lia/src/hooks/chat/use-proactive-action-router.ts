"use client"

/**
 * useProactiveActionRouter — Listens to `lia:proactive-action` events dispatched
 * by ProactiveHintsList and routes each action to the appropriate handler.
 *
 * Design (PARTE F — fully conversational):
 *   - Navigation actions → dispatch `lia:navigation-hint` (reuses existing listener)
 *   - All data-modifying actions → chat-delegate (LIA asks follow-up questions inline;
 *     zero modals, zero window.prompt, zero new REST endpoints). Backend uses
 *     `awaitingStageConfirmation` pattern + `messageType: 'detected-fields'` for
 *     preview cards rendered inline in chat.
 *   - Import actions → navigate to existing Settings tabs that already have
 *     SmartImportZone / DocumentUploadCard infrastructure.
 *
 * Click on the card button IS the authorization — no second confirmation dialog.
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
}

const NAVIGATION_ACTIONS: Record<string, { page: string; subsection?: string }> = {
  navigate_to_settings: { page: "Configurações" },
  navigate_to_benefits_import: { page: "Configurações", subsection: "benefits-import" },
  navigate_to_company_data: { page: "Configurações", subsection: "company-data" },
}

// Actions handled via conversational chat — LIA asks follow-up questions inline,
// backend uses awaitingStageConfirmation + detected-fields messageType for previews.
// No modals, no window.prompt.
const CHAT_DELEGATE_PROMPTS: Record<string, (meta: Record<string, unknown>) => string> = {
  request_website_and_scrape: () =>
    "Quero analisar o site da minha empresa para preencher o perfil automaticamente.",
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
}

export function useProactiveActionRouter(opts: ProactiveActionRouterOptions = {}): void {
  const { sendChatMessage } = opts

  useEffect(() => {
    const handler = async (ev: Event) => {
      const detail = (ev as CustomEvent<ProactiveActionDetail>).detail
      if (!detail || !detail.action) return

      const { action, metadata = {} } = detail

      // 1. Navigation actions — reuse existing lia:navigation-hint listener
      if (action in NAVIGATION_ACTIONS) {
        const nav = NAVIGATION_ACTIONS[action]
        const targetPage =
          (metadata as { target_page?: string }).target_page === "settings"
            ? "Configurações"
            : (metadata as { page?: string }).page || nav.page
        window.dispatchEvent(
          new CustomEvent("lia:navigation-hint", {
            detail: {
              page: targetPage,
              subsection: nav.subsection ?? (metadata as { subsection?: string }).subsection,
              hint: null,
            },
          }),
        )
        return
      }

      // 2. Chat-delegating actions — push a proactive message into the chat
      //    Backend responds via awaitingStageConfirmation + detected-fields patterns
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

      // 3. Unknown action — log for future coverage
      console.warn("[ProactiveActionRouter] no handler for action:", action, detail)
    }

    window.addEventListener("lia:proactive-action", handler)
    return () => window.removeEventListener("lia:proactive-action", handler)
  }, [sendChatMessage])
}
