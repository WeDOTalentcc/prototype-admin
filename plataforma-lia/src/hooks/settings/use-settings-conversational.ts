"use client"

import { useCallback } from "react"

export type SettingsActionId =
  | "configure_profile"
  | "configure_culture"
  | "configure_tech_stack"
  | "configure_benefits"
  | "configure_workforce"
  | "configure_hiring_policy"
  | "configure_persona"
  | "analyze_website"
  | "process_document"
  | "prefill_section"

export type PrefillSection =
  | "basic"
  | "culture"
  | "tech_stack"
  | "benefits"
  | "workforce"
  | "policy"
  | "compensation"

const SECTION_LABELS: Record<PrefillSection, string> = {
  basic: "Dados Básicos",
  culture: "Cultura & EVP",
  tech_stack: "Tech Stack",
  benefits: "Benefícios",
  workforce: "Workforce Planning",
  policy: "Políticas de Recrutamento",
  compensation: "Plano de Remuneração",
}

export interface SettingsActionEventDetail {
  actionId: SettingsActionId
  section: string
  field?: string
  prompt?: string
  payload?: Record<string, unknown>
  source?: "chat" | "ui" | "onboarding"
  autoSend?: boolean
}

const ACTION_TO_TAB: Record<SettingsActionId, string> = {
  configure_profile: "minha-empresa",
  configure_culture: "minha-empresa",
  configure_tech_stack: "minha-empresa",
  configure_benefits: "minha-empresa",
  configure_workforce: "minha-empresa",
  configure_hiring_policy: "minha-empresa",
  configure_persona: "lia-personalizacao",
  analyze_website: "minha-empresa",
  process_document: "minha-empresa",
  prefill_section: "minha-empresa",
}

export const SETTINGS_ACTION_EVENT = "lia:settings-action"
export const SETTINGS_OPEN_TAB_EVENT = "settings-open-tab"

export function useSettingsConversational() {
  const dispatchAction = useCallback((detail: SettingsActionEventDetail) => {
    if (typeof window === "undefined") return
    const tab = detail.section || ACTION_TO_TAB[detail.actionId] || "minha-empresa"
    window.dispatchEvent(
      new CustomEvent(SETTINGS_ACTION_EVENT, {
        detail: { ...detail, section: tab },
      }),
    )
    window.dispatchEvent(
      new CustomEvent(SETTINGS_OPEN_TAB_EVENT, { detail: tab }),
    )
  }, [])

  const sendChatPrompt = useCallback((prompt: string, autoSend = false) => {
    if (typeof window === "undefined") return
    // Usa o evento canonico ja consumido pelo UnifiedChat (InlineChatBridge / useSmartFileUpload)
    window.dispatchEvent(
      new CustomEvent("lia:prefill-message", {
        detail: { message: prompt, source: "settings", autoSend },
      }),
    )
  }, [])

  const triggerAction = useCallback(
    (actionId: SettingsActionId, opts?: Partial<SettingsActionEventDetail>) => {
      const detail: SettingsActionEventDetail = {
        actionId,
        section: opts?.section || ACTION_TO_TAB[actionId],
        field: opts?.field,
        prompt: opts?.prompt,
        payload: opts?.payload,
        source: opts?.source || "ui",
      }
      dispatchAction(detail)
      if (detail.prompt) {
        sendChatPrompt(detail.prompt, detail.autoSend ?? false)
      }
    },
    [dispatchAction, sendChatPrompt],
  )

  /**
   * Ask LIA to fill the missing fields of a single section.
   *
   * The chat prompt includes the section key + missing labels so the agent
   * scopes its conversational follow-up to that area only. FairnessGuard /
   * PII / HITL still apply on the agent side — this just pre-narrows the
   * conversation. Triggered both by UI buttons and by free-text commands
   * such as "preenche meus benefícios".
   */
  const triggerPrefillSection = useCallback(
    (
      section: PrefillSection,
      missingLabels: string[] = [],
      opts?: { autoSend?: boolean },
    ) => {
      const label = SECTION_LABELS[section]
      const missingClause = missingLabels.length
        ? `Os campos ainda pendentes são: ${missingLabels.slice(0, 12).join(", ")}.`
        : "Liste primeiro o que ainda falta nessa seção."
      const prompt = [
        `[ACTION:prefill_section]`,
        `[target_section:${section}]`,
        ``,
        `Quero preencher a seção "${label}" da minha empresa.`,
        missingClause,
        `Faça perguntas focadas APENAS nesta seção, uma de cada vez, e ao final peça minha confirmação antes de salvar (FairnessGuard, PII e HITL continuam valendo).`,
      ].join("\n")

      const detail: SettingsActionEventDetail = {
        actionId: "prefill_section",
        section: "minha-empresa",
        prompt,
        payload: { target_section: section, missing: missingLabels },
        source: "ui",
      }
      dispatchAction(detail)
      // T6 (#993): autoSend default true — alinha com analyzeWebsite e
      // com contrato "ações do hub disparam ação real" (preferência
      // replit.md "Chat é a interface principal"). Caller pode opt-out
      // explicitamente passando { autoSend: false }.
      sendChatPrompt(prompt, opts?.autoSend ?? true)
    },
    [dispatchAction, sendChatPrompt],
  )

  return {
    triggerAction,
    triggerPrefillSection,
    dispatchAction,
    sendChatPrompt,
    ACTION_TO_TAB,
    SECTION_LABELS,
  }
}

/**
 * Heuristic parser for free-text commands like "preenche meus benefícios"
 * coming from the chat. Returns the matching section key or `null`.
 * Exported so the chat layer can pre-route the prompt before sending it
 * to LIA, mirroring how `target_section` is propagated for uploads.
 */
export function detectPrefillSectionCommand(text: string): PrefillSection | null {
  if (!text) return null
  const t = text.toLowerCase()
  const isFillIntent =
    /\b(preenche|preencher|completa|completar|atualiza|atualizar)\b/.test(t)
  if (!isFillIntent) return null
  // PR1 (#1001) — "dados básicos"/"perfil"/"cnpj" rota pra `basic`. Vem
  // antes de benefits/culture/etc. para que termos cadastrais (cnpj,
  // razão social, hr_email) não sejam capturados por outras seções.
  if (/dados\s+b[aá]sicos|perfil\s+(da\s+)?empresa|cnpj|raz[aã]o\s+social|nome\s+fantasia|hr\s*email|email\s+do\s+rh/.test(t))
    return "basic"
  if (/benef[ií]cios?/.test(t)) return "benefits"
  if (/cultura|evp|valores|miss[aã]o/.test(t)) return "culture"
  if (/tech\s*stack|stack|tecnolog/.test(t)) return "tech_stack"
  if (/workforce|headcount|departament|organograma/.test(t)) return "workforce"
  if (/pol[ií]tic|recrutament|pipeline/.test(t)) return "policy"
  if (/remunera|sal[aá]ri|compensation|cargos? e sal/.test(t)) return "compensation"
  return null
}
