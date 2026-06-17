"use client"

import { useCallback, useEffect, useState } from "react"
import {
  AJUDA_REGEX,
  buildAjudaHelpMarkdown,
  findSlashCommandByToken,
  findSlashCommandByVerb,
} from "../slash-commands"

/**
 * useWizardIntegration — Phase D.1 Cross-feature integration.
 *
 * Connects the wizard with:
 * - @mention: reference jobs/candidates during creation
 * - File upload: JD PDF → auto-populates wizard intake
 * - /commands: /criar vaga → starts wizard
 * - Navigation hints: auto-navigate after handoff
 * - wizard_step_response: drives split-view panel state (E.1 / E.7)
 *
 * Place in UnifiedChat to wire all features together.
 */

// --- Panel type driven by wizard_step_response ---

export type ActivePanelType = "jd_review" | "wsi_review" | "calibration" | null

interface WizardStepResponse {
  missing_fields?: string[]
  requires_approval?: boolean
  approval_context?: Record<string, unknown>
  stage_name?: string
  detected_criteria?: Record<string, unknown>
}

/**
 * Determine which side-panel to open based on the stage_name in
 * wizard_step_response.
 */
function determinePanelType(stepResponse: WizardStepResponse): ActivePanelType {
  const stage = (stepResponse.stage_name ?? "").toLowerCase()
  if (stage.includes("jd_enrichment") || stage.includes("review")) return "jd_review"
  if (stage.includes("wsi_questions") || stage.includes("wsi")) return "wsi_review"
  if (stage.includes("calibration")) return "calibration"
  return null
}

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
  // E.1 / E.7: Split-view state driven by wizard_step_response
  const [activePanelType, setActivePanelType] = useState<ActivePanelType>(null)
  const [missingFields, setMissingFields] = useState<string[]>([])

  // E.1: Process wizard_step_response from WS message metadata.
  // Call this from the WS message handler whenever a new message arrives.
  const handleWizardStepResponse = useCallback((message: { metadata?: Record<string, unknown> }) => {
    const stepResponse = message?.metadata?.wizard_step_response as WizardStepResponse | undefined
    if (!stepResponse) return

    // Onda 33 — always reconcile missing_fields with the latest payload so the
    // banner in UnifiedChat does not surface STALE warnings after the recruiter
    // fixes the pending intake fields. Previous behavior only SET on non-empty,
    // never cleared, which kept the banner pinned indefinitely.
    if (Array.isArray(stepResponse.missing_fields)) {
      setMissingFields(stepResponse.missing_fields)
    } else {
      setMissingFields([])
    }

    // Drive split-view panel
    if (stepResponse.requires_approval === true) {
      const panelType = determinePanelType(stepResponse)
      setActivePanelType(panelType)
    } else if (stepResponse.requires_approval === false) {
      // Close the panel when approval is no longer required
      setActivePanelType(null)
      // Onda 33 — also clear the banner when the wizard exits this step.
      setMissingFields([])
    }
  }, [])

  // Fix G (2026-05-27 -- WIZARD_DEEP_DIVE_2026-05-27_POST_PR18 P1-NOVO-#4):
  // wire `handleWizardStepResponse` via `lia:wizard-stage-payload` window event
  // (mesmo event canonical do Fix B). Antes deste fix, o handler era orfao
  // desde a Onda 33 -- nenhum caller invocava, missingFields sempre vazio,
  // banner "Campos obrigatorios em aberto" nunca aparecia em UnifiedChat:948.
  //
  // Adapter shape: extrai missing_fields direto do detail.data (canonical
  // wizard_stage payload) E backward-compat com message_metadata.wizard_step_response
  // caso backend emita esse shape no futuro. Cleanup canonical no return.
  useEffect(() => {
    if (typeof window === "undefined") return
    const handler = (e: Event) => {
      const detail = ((e as CustomEvent).detail ?? {}) as Record<string, unknown>
      const data = (detail.data as Record<string, unknown>) ?? {}

      // Path 1 canonical: missing_fields direto no wizard_stage payload.
      const missing = data.missing_fields
      if (Array.isArray(missing)) {
        setMissingFields(missing.map(String))
      } else if (detail.requires_approval === false) {
        // Stage avancou sem pendencias -- limpar banner residual.
        setMissingFields([])
      }

      // Path 2 backward-compat: message_metadata.wizard_step_response shape
      // (Onda 33 original). Se backend emitir esse blob, o handler trata.
      const wsr = data.wizard_step_response
      if (wsr && typeof wsr === "object") {
        handleWizardStepResponse({ metadata: { wizard_step_response: wsr } })
      }
    }
    window.addEventListener("lia:wizard-stage-payload", handler)
    return () =>
      window.removeEventListener("lia:wizard-stage-payload", handler)
  }, [handleWizardStepResponse])

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
      const { index, newText, type: eventType, candidateId, reason } = e.detail || {}

      // Calibration approve/reject/skip: persist feedback + comment via API (fire-and-forget),
      // then forward to LLM so orchestrator can update calibration state.
      if ((eventType === "calibration_approve" || eventType === "calibration_reject" || eventType === "calibration_skip") && candidateId) {
        const feedbackKind =
          eventType === "calibration_approve" ? "like" :
          eventType === "calibration_reject" ? "dislike" : "skip"

        // Captura persistente: like/dislike + comentário → BE (best-effort, não bloqueia UX)
        fetch("/api/backend-proxy/search/calibration/feedback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ candidate_id: candidateId, feedback: feedbackKind, reason: reason ?? null }),
        }).catch(() => {})

        if (eventType === "calibration_approve") {
          sendMessage(`Aprovar candidato para calibracao: ${candidateId}` + (reason ? `. Comentario: ${reason}` : ""))
        } else if (eventType === "calibration_reject") {
          sendMessage(`Rejeitar candidato da calibracao: ${candidateId}` + (reason ? `. Comentario: ${reason}` : ""))
        } else {
          sendMessage(`Pular candidato da calibracao: ${candidateId}`)
        }
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

    // Onda 33 — drag-to-reorder dispatched by WsiQuestionsPanel.
    function handleReorderQuestions(e: CustomEvent) {
      const { fromIndex, toIndex } = e.detail || {}
      if (typeof fromIndex !== "number" || typeof toIndex !== "number") return
      sendMessage(`Reordenar pergunta ${fromIndex + 1} para posicao ${toIndex + 1}`)
    }

    // Task #1067 — "Tentar novamente" no banner de fallback do wizard.
    // FallbackBanner (em JdEnrichment/BigFive/Salary/WsiQuestions panels)
    // dispara este evento com `{ stage: "jd_enrichment" | "bigfive" |
    // "salary" | "wsi_questions" }`. Reenviamos como mensagem de chat
    // pra que o WizardReActAgent reexecute o nó correspondente sem o
    // recrutador precisar digitar.
    function handleRetryStage(e: CustomEvent) {
      const { stage } = e.detail || {}
      if (typeof stage !== "string" || !stage) return
      const labelByStage: Record<string, string> = {
        jd_enrichment: "enriquecimento da descrição",
        bigfive: "perfil Big Five",
        salary: "benchmark de salário",
        wsi_questions: "perguntas WSI",
      }
      const label = labelByStage[stage] ?? stage
      sendMessage(`Tentar novamente: ${label}`)
    }

    // Botao "Gerar novas" (todas) do WsiQuestionsPanel (item 2 polish
    // 2026-06-05). Caminho PROVADO sendMessage->classifier (mesmo dos
    // per-question), NAO sendApproval — que no-opa sem hitlRef no estagio do
    // wizard. O wsi_questions_gate classifica como regenerate_all.
    function handleRegenerateAll() {
      sendMessage("Regenerar todas as perguntas de triagem")
    }

    // W2-B: adicionar pergunta do banco da empresa ao set WSI
    function handleAddBankQuestion(e: CustomEvent) {
      const { questionId } = (e as CustomEvent<{ questionId: string }>).detail || {}
      if (!questionId) return
      // Mensagem estruturada: UUID literal — o wizard extrai exatamente
      sendMessage(`Adicionar do banco pergunta id=${questionId}`)
    }

    const c1 = onCustomEvent("lia:wizard-edit-question", handleEditQuestion)
    const c2 = onCustomEvent("lia:wizard-regenerate-question", handleRegenerateQuestion)
    const c3 = onCustomEvent("lia:wizard-remove-question", handleRemoveQuestion)
    const c4 = onCustomEvent("lia:wizard-reorder-questions", handleReorderQuestions)
    const c5 = onCustomEvent("lia:wizard-retry-stage", handleRetryStage)
    const c6 = onCustomEvent("lia:wizard-regenerate-all", handleRegenerateAll)
    const c7 = onCustomEvent("lia:wizard-add-bank-question", handleAddBankQuestion)
    return () => { c1(); c2(); c3(); c4(); c5(); c6(); c7() }
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
    const bareMatch = cmd.match(/^\/[\wÀ-ſ][\wÀ-ſ\s]*$/i)
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
  }, [sendMessage, onLocalCommand])

  return {
    handleSlashCommand,
    // E.1 / E.7: Split-view state
    activePanelType,
    missingFields,
    handleWizardStepResponse,
  }
}
