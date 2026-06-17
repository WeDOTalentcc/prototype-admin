"use client"

/**
 * AutomationFromChatBridge — Sprint D.3 canonical impeccable.
 *
 * Bridge entre chat LIA (intent_hint: "create_automation") e AutomationsTab.
 * Listener pro evento window `lia:create-automation` com detail = partial state
 * (trigger/conditions/actions/name/source).
 *
 * Pattern alinhado com OnboardingChatBanner CustomEvent dispatch
 * (commit 98450640c90). Componente headless (return null) — só side effect.
 *
 * Fluxo:
 *  1. Chat LIA emite `intent_hint: "create_automation"` → reels metadata
 *  2. Algum handler upstream dispara `window.dispatchEvent(new CustomEvent(
 *     "lia:create-automation", { detail: <partial SentenceBuilderState> }))`
 *  3. Este bridge intercepta, persiste em sessionStorage e navega para
 *     `/configuracoes?section=recrutamento-lia&subsection=automacoes&view=builder`
 *  4. AutomationsTab no mount hidrata builder com sessionStorage payload
 *
 * Audit ref:
 *  - AUTOMATIONS_SPRINT_PLAN_ADR.md Sprint D.3
 *  - AUTOMATIONS_IMPECCABLE_CRITIQUE.md (LIA chat shortcut canonical)
 *  - AUTOMATIONS_FRONTEND_AUDIT.md
 */

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export interface CreateAutomationDetail {
  trigger?: { type: string; params?: Record<string, unknown> }
  conditions?: Array<{ field: string; operator: string; value: unknown }>
  actions?: Array<{ type: string; params?: Record<string, unknown> }>
  name?: string
  source?: "chat" | "proactive" | "manual"
}

export const LIA_PENDING_AUTOMATION_STORAGE_KEY = "lia-pending-automation-state"
export const LIA_CREATE_AUTOMATION_EVENT = "lia:create-automation"
export const AUTOMATION_BUILDER_PATH =
  "/configuracoes?section=recrutamento-lia&subsection=automacoes&view=builder"

export function AutomationFromChatBridge() {
  const router = useRouter()

  useEffect(() => {
    if (typeof window === "undefined") return

    const handler = (e: Event) => {
      const detail = (e as CustomEvent<CreateAutomationDetail>).detail ?? {}
      // Persist payload em sessionStorage pra AutomationsTab consumir
      // no mount (hidratação do builder com state vindo do chat).
      try {
        window.sessionStorage.setItem(
          LIA_PENDING_AUTOMATION_STORAGE_KEY,
          JSON.stringify(detail),
        )
      } catch {
        // sessionStorage indisponivel (private mode, storage quota, etc.)
        // REGRA 4 anti-silent-fallback: log warn, mas continua navegação
        // (Builder abre em modo vazio — UX degraded mas não broken).
        console.warn(
          "[AutomationFromChatBridge] sessionStorage unavailable; navigating without state",
        )
      }
      router.push(AUTOMATION_BUILDER_PATH)
    }

    window.addEventListener(
      LIA_CREATE_AUTOMATION_EVENT,
      handler as EventListener,
    )
    return () => {
      window.removeEventListener(
        LIA_CREATE_AUTOMATION_EVENT,
        handler as EventListener,
      )
    }
  }, [router])

  return null
}
