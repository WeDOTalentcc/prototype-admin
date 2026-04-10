"use client"

import { useCallback, useEffect } from "react"
import type { WizardStagePayload } from "./wizard-types"

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
  onWizardStage?: (payload: WizardStagePayload) => void
}

export function useWizardIntegration({
  isWizardActive,
  currentStage,
  sendMessage,
  onWizardStage,
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

    window.addEventListener("lia:file-upload-confirmed" as any, handleFileConfirmed)
    window.addEventListener("lia:file-upload-cv" as any, handleFileUpload)
    return () => {
      window.removeEventListener("lia:file-upload-confirmed" as any, handleFileConfirmed)
      window.removeEventListener("lia:file-upload-cv" as any, handleFileUpload)
    }
  }, [sendMessage])

  // D.1: Wizard question edit/regenerate/remove events
  useEffect(() => {
    if (!isWizardActive) return

    function handleEditQuestion(e: CustomEvent) {
      const { index, newText } = e.detail || {}
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

    window.addEventListener("lia:wizard-edit-question" as any, handleEditQuestion)
    window.addEventListener("lia:wizard-regenerate-question" as any, handleRegenerateQuestion)
    window.addEventListener("lia:wizard-remove-question" as any, handleRemoveQuestion)
    return () => {
      window.removeEventListener("lia:wizard-edit-question" as any, handleEditQuestion)
      window.removeEventListener("lia:wizard-regenerate-question" as any, handleRegenerateQuestion)
      window.removeEventListener("lia:wizard-remove-question" as any, handleRemoveQuestion)
    }
  }, [isWizardActive, sendMessage])

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
