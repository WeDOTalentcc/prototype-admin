"use client"

import { useCallback, useEffect } from "react"
import {
  AJUDA_REGEX,
  buildAjudaHelpMarkdown,
  findSlashCommandByToken,
  findSlashCommandByVerb,
} from "../slash-commands"
// Types imported as needed by consumers

/**
 * useWizardIntegration — Phase D.1 Cross-feature integration.
 *
 * Connects the wizard with:
 * - @mention: reference jobs/candidates during creation
 * - File upload: JD PDF → auto-populates wizard intake
 * - /commands: /criar vaga → starts wizard
 * - Navigation hints: auto-navigate after handoff
 *
 * Place in UnifiedChat to wire all features together.
 */

interface Props {
  isWizardActive: boolean
  currentStage: string | null
  sendMessage: (text: string) => void
  /**
   * Called when a slash command is fully resolved on the client (no
   * backend round-trip). Today only `/ajuda` uses this; keeping the
   * surface as a generic `(commandId, payload)` tuple lets future local
   * commands like `/definir` migrate here without changing the contract.
   */
  onLocalCommand?: (commandId: string, payload: { responseMarkdown: string; rawInput: string }) => void
}

// Type-safe custom event helper
function onCustomEvent(name: string, handler: (e: CustomEvent) => void) {
  window.addEventListener(name, handler as EventListener)
  return () => window.removeEventListener(name, handler as EventListener)
}

export function useWizardIntegration({
  isWizardActive,
  currentStage,
  sendMessage,
  onLocalCommand,
}: Props) {

  // D.1: File upload → wizard intake
  useEffect(() => {
    function handleFileConfirmed(e: CustomEvent) {
      const { file, type, consentAcknowledged } = e.detail || {}
      if (type === "jd" && file?.name) {
        // Task #838 / M-01: ao confirmar consentimento aqui (mesma sessao),
        // memoriza no sessionStorage para que `useSmartFileUpload` nao volte a
        // perguntar nas proximas JDs do mesmo tab. Isso e defesa em profundidade
        // alem do preflight contra `/jd-import/consent-status`.
        if (consentAcknowledged === true && typeof window !== "undefined") {
          try { window.sessionStorage.setItem("lia-jd-upload-consent", "1") } catch { /* quota */ }
        }
        // Task #865 — actually starting the wizard now happens AFTER the
        // async worker reports `completed` (see `useJdUploadProgress`).
        // Firing `sendMessage("Criar vaga…")` here would race with the
        // upload, so this branch only persists the consent flag now and
        // lets the upload hook drive the wizard from the WS event.
      }
    }

    function handleFileUpload(e: CustomEvent) {
      const { file, type } = e.detail || {}
      if (type === "cv") {
        // CV goes to screening (not wizard)
        sendMessage(`Analisar curriculo: ${file?.name || "arquivo"}`)
      }
    }

    const cleanupConfirmed = onCustomEvent("lia:file-upload-confirmed", handleFileConfirmed)
    const cleanupCv = onCustomEvent("lia:file-upload-cv", handleFileUpload)
    return () => { cleanupConfirmed(); cleanupCv() }
  }, [sendMessage])

  // D.1: Wizard question edit/regenerate/remove + calibration events
  useEffect(() => {
    if (!isWizardActive) return

    function handleEditQuestion(e: CustomEvent) {
      const { index, newText, type: eventType, candidateId } = e.detail || {}

      // Calibration approve/reject events reuse this channel
      if (eventType === "calibration_approve" && candidateId) {
        sendMessage(`Aprovar candidato para calibracao: ${candidateId}`)
        return
      }
      if (eventType === "calibration_reject" && candidateId) {
        sendMessage(`Rejeitar candidato da calibracao: ${candidateId}`)
        return
      }

      // Question edit
      sendMessage(`Editar pergunta ${(index || 0) + 1}: ${newText || ""}`)
    }

    function handleRegenerateQuestion(e: CustomEvent) {
      const { index } = e.detail || {}
      sendMessage(`Regenerar pergunta ${(index || 0) + 1}`)
    }

    function handleRemoveQuestion(e: CustomEvent) {
      const { index } = e.detail || {}
      sendMessage(`Remover pergunta ${(index || 0) + 1}`)
    }

    const c1 = onCustomEvent("lia:wizard-edit-question", handleEditQuestion)
    const c2 = onCustomEvent("lia:wizard-regenerate-question", handleRegenerateQuestion)
    const c3 = onCustomEvent("lia:wizard-remove-question", handleRemoveQuestion)
    return () => { c1(); c2(); c3() }
  }, [isWizardActive, sendMessage])

  // Prefill message listener (used by DonePanel "Criar outra vaga")
  useEffect(() => {
    function handlePrefill(e: CustomEvent) {
      const { message } = e.detail || {}
      if (message) {
        sendMessage(message)
      }
    }
    return onCustomEvent("lia:prefill-message", handlePrefill)
  }, [sendMessage])

  // D.1: Handoff auto-navigation
  useEffect(() => {
    if (currentStage === "handoff") {
      // Dispatch navigation hint for dashboard to handle
      window.dispatchEvent(new CustomEvent("lia:navigation-hint", {
        detail: {
          page: "jobs",
          hint: "Vaga publicada! Navegando para a pagina da vaga...",
        },
      }))
    }
  }, [currentStage])

  // D.1: /commands → wizard (supports cross @mention+/command)
  // The set of recognised commands lives in `../slash-commands.ts` — keep it
  // as the single source of truth for product, docs and tests.
  const handleSlashCommand = useCallback((command: string) => {
    const cmd = command.trim()

    // `/ajuda` is a fully-local command — no backend round-trip. The help
    // text is built from the canonical SLASH_COMMANDS list so every chat
    // surface (UnifiedChat and any future popovers) renders identical
    // copy. Surfaces that don't pass `onLocalCommand` fall through to
    // backend dispatch, preserving prior behaviour.
    if (AJUDA_REGEX.test(cmd)) {
      if (onLocalCommand) {
        onLocalCommand("ajuda", {
          responseMarkdown: buildAjudaHelpMarkdown(),
          rawInput: cmd,
        })
        return true
      }
      return false
    }

    // Bare command, e.g. "/criar vaga", "/job", "/pipeline".
    const bareMatch = cmd.match(/^\/[\w\u00C0-\u017F][\w\u00C0-\u017F\s]*$/i)
    if (bareMatch) {
      const found = findSlashCommandByToken(cmd)
      const message = found?.buildBareMessage?.()
      if (message) {
        sendMessage(message)
        return true
      }
    }

    // Cross form: "/command @target" (e.g., "/buscar @NomeCandidato").
    const crossMatch = cmd.match(/^\/(\w+)\s+@(.+)$/i)
    if (crossMatch) {
      const verb = crossMatch[1]
      const mention = crossMatch[2].trim()
      const found = findSlashCommandByVerb(verb)
      const message = found?.buildMentionMessage?.(mention)
      if (message) {
        sendMessage(message)
        return true
      }
      // Unknown cross command — forward as-is so the backend can react.
      sendMessage(cmd)
      return true
    }

    // Free-form fallback: "/buscar <query>" without an @mention.
    if (/^\/buscar\b/i.test(cmd)) {
      sendMessage(cmd.replace(/^\/buscar\s*/i, "Buscar: "))
      return true
    }

    return false
  }, [sendMessage])

  return {
    handleSlashCommand,
  }
}
