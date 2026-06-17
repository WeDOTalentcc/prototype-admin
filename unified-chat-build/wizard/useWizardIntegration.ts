"use client"

import { useCallback, useEffect } from "react"
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
}: Props) {

  // D.1: File upload → wizard intake
  useEffect(() => {
    function handleFileConfirmed(e: CustomEvent) {
      const { file, type } = e.detail || {}
      if (type === "jd" && file?.name) {
        // JD file auto-starts wizard
        sendMessage(`Criar vaga a partir do arquivo: ${file.name}`)
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
  const handleSlashCommand = useCallback((command: string) => {
    const cmd = command.trim()
    const cmdLower = cmd.toLowerCase()

    // Simple commands
    if (cmdLower === "/criar vaga" || cmdLower === "/nova vaga") {
      sendMessage("Criar nova vaga")
      return true
    }
    if (cmdLower === "/ajuda") {
      sendMessage("/ajuda")
      return true
    }
    if (cmdLower === "/pipeline") {
      sendMessage("Mostrar pipeline de vagas abertas")
      return true
    }
    if (cmdLower === "/relatorio") {
      sendMessage("Gerar relatorio semanal de recrutamento")
      return true
    }

    // Cross: /command @mention (e.g., "/buscar @NomeCandidato")
    const crossMatch = cmd.match(/^\/(\w+)\s+@(.+)$/i)
    if (crossMatch) {
      const action = crossMatch[1].toLowerCase()
      const mention = crossMatch[2].trim()

      if (action === "buscar") {
        sendMessage(`Buscar candidato: ${mention}`)
        return true
      }
      if (action === "pipeline") {
        sendMessage(`Pipeline da vaga: ${mention}`)
        return true
      }
      if (action === "relatorio") {
        sendMessage(`Relatorio da vaga: ${mention}`)
        return true
      }
      if (action === "feedback") {
        sendMessage(`Enviar feedback para: ${mention}`)
        return true
      }
      if (action === "agendar") {
        sendMessage(`Agendar entrevista com: ${mention}`)
        return true
      }
      // Unknown cross command — send as-is
      sendMessage(cmd)
      return true
    }

    // /command without match — pass through
    if (cmdLower.startsWith("/buscar")) {
      sendMessage(cmd.replace(/^\/buscar\s*/i, "Buscar: "))
      return true
    }

    return false
  }, [sendMessage])

  return {
    handleSlashCommand,
  }
}
