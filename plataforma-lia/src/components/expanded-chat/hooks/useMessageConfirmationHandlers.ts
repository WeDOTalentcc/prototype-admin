"use client"

import type React from "react"
import type {
  Message,
  WizardMode,
  WSIQuestionCandidate,
} from "../types"
import type { WizardStage } from "../config"
import type {
  BasicInfoFields,
  TechnicalSkill,
  BehavioralCompetency,
  WSIQuestion,
  DetectedCriteria,
} from "../ExpandedChatContext"
import type { JobConfig } from "./usePublishingState"
import type { useWizardAnalytics } from "./useWizardAnalytics"

// ─────────────────────────────────────────────────────────────────────────────
// Context interface — dependencies needed by both confirmation handlers
// ─────────────────────────────────────────────────────────────────────────────

export interface MessageConfirmationHandlersContext {
  // ─── User ───────────────────────────────────────────────────────────────────
  user: { id?: string; email?: string; company?: string } | null
  resolvedCompanyId: string | null

  // ─── Mode flags ──────────────────────────────────────────────────────────────
  isInJobCreationMode: boolean

  // ─── Messages ────────────────────────────────────────────────────────────────
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setIsLoading: (val: boolean) => void

  // ─── WSI ─────────────────────────────────────────────────────────────────────
  awaitingWSIRegenerationConfirmation: boolean
  setAwaitingWSIRegenerationConfirmation: (val: boolean) => void
  wsiCandidates: WSIQuestionCandidate[]
  setWsiCandidates: React.Dispatch<React.SetStateAction<WSIQuestionCandidate[]>>
  basicInfoFields: BasicInfoFields
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]

  // ─── Sensitive fields (Fast Track post-confirm) ───────────────────────────────
  awaitingSensitiveFieldsConfirmation: boolean
  setAwaitingSensitiveFieldsConfirmation: (val: boolean) => void
  fastTrackAppliedData: { gestor: string; localidade: string; sourceJobTitle: string } | null
  setFastTrackAppliedData: (data: { gestor: string; localidade: string; sourceJobTitle: string } | null) => void
  setBasicInfoFields: React.Dispatch<React.SetStateAction<BasicInfoFields>>
  setJobConfig: React.Dispatch<React.SetStateAction<JobConfig>>
  setDetectedCriteria: React.Dispatch<React.SetStateAction<DetectedCriteria>>
  setCurrentStage: (stage: WizardStage) => void
  setWizardMode: (mode: WizardMode) => void

  // ─── Analytics ───────────────────────────────────────────────────────────────
  analytics: ReturnType<typeof useWizardAnalytics>
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook
// ─────────────────────────────────────────────────────────────────────────────

export function useMessageConfirmationHandlers(ctx: MessageConfirmationHandlersContext) {
  const {
    user,
    isInJobCreationMode,
    setMessages,
    setIsLoading,
    awaitingWSIRegenerationConfirmation,
    setAwaitingWSIRegenerationConfirmation,
    wsiCandidates,
    setWsiCandidates,
    basicInfoFields,
    technicalSkills,
    behavioralCompetencies,
    awaitingSensitiveFieldsConfirmation,
    setAwaitingSensitiveFieldsConfirmation,
    fastTrackAppliedData,
    setFastTrackAppliedData,
    setBasicInfoFields,
    setJobConfig,
    setDetectedCriteria,
    setCurrentStage,
    setWizardMode,
    analytics,
  } = ctx

  // ── Interceptor 5: awaiting WSI regeneration confirmation ─────────────────
  const handleWSIRegenConfirmation = async (content: string): Promise<boolean> => {
    if (!isInJobCreationMode || !awaitingWSIRegenerationConfirmation) return false
    const lowerContent = content.toLowerCase().trim()

    const affirmativePatterns = ["sim", "pode", "atualiz", "regen", "ok", "claro", "por favor", "quero"]
    const negativePatterns = ["não", "nao", "deixa", "mantém", "mantem", "fica", "assim mesmo"]

    const isAffirmative = affirmativePatterns.some(p => lowerContent.includes(p))
    const isNegative = negativePatterns.some(p => lowerContent.includes(p))

    if (isAffirmative && !isNegative) {
      setAwaitingWSIRegenerationConfirmation(false)
      setIsLoading(true)
      try {
        const { regenerateWSIQuestions } = await import("@/services/lia-api")
        const currentQuestions = wsiCandidates.map((q, idx) => ({
          id: q.id || `wsi-${idx}`,
          question_text: q.question,
          question_type: (q.type || "open") as "open" | "yes-no" | "numeric" | "multiple-choice",
          competency_validated: q.competency || null,
          competency_type: null as null,
        }))
        const result = await regenerateWSIQuestions({
          company_id: ctx.resolvedCompanyId ?? "",
          job_title: basicInfoFields.cargo,
          current_questions: currentQuestions,
          technical_skills: technicalSkills.map(s => s.name),
          behavioral_competencies: behavioralCompetencies.map(c => c.name),
          seniority: undefined,
          max_questions: 10,
        })
        if (result.success && result.questions.length > 0) {
          setWsiCandidates(result.questions.map((q, idx) => ({
            id: `wsi-regen-${idx}-${Date.now()}`,
            question: q.question_text,
            type: (q.question_type || "open") as WSIQuestion["type"],
            required: true,
            selected: true,
            batch: 0,
            isWSI: true,
            competency: q.competency_validated ?? undefined,
          })))
          analytics.trackSuggestion("fast_track_wsi_regenerated", true)
          const successMessage: Message = {
            id: `wsi-regen-success-${Date.now()}`,
            role: "assistant",
            content: `Pronto! Gerei **${result.questions.length} novas perguntas WSI** baseadas nas competências atualizadas. Você pode revisar e ajustar no painel ao lado.`,
            timestamp: new Date(),
          }
          setMessages(prev => [...prev, successMessage])
        } else if (!result.success) {
          const warningMessage: Message = {
            id: `wsi-regen-warning-${Date.now()}`,
            role: "assistant",
            content: "A regeneração não foi possível. Manterei as perguntas atuais - você pode editá-las manualmente no painel.",
            timestamp: new Date(),
          }
          setMessages(prev => [...prev, warningMessage])
        }
      } catch {
        const errorMessage: Message = {
          id: `wsi-regen-error-${Date.now()}`,
          role: "assistant",
          content: "Tive um problema ao regenerar as perguntas. Você pode tentar novamente mais tarde ou editar manualmente.",
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, errorMessage])
      } finally {
        setIsLoading(false)
      }
      return true
    }

    if (isNegative) {
      setAwaitingWSIRegenerationConfirmation(false)
      const keepMessage: Message = {
        id: `wsi-keep-${Date.now()}`,
        role: "assistant",
        content: "Tudo bem! Manterei as perguntas WSI atuais. Se mudar de ideia, é só me avisar.",
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, keepMessage])
      return true
    }

    return false
  }

  // ── Interceptor 6: awaiting sensitive fields confirmation (Fast Track) ─────
  const handleSensitiveFieldsConfirmation = async (content: string): Promise<boolean> => {
    if (!isInJobCreationMode || !awaitingSensitiveFieldsConfirmation) return false
    const lowerContent = content.toLowerCase().trim()

    const gestorPatterns = [
      /gestor(?:\s+(?:[eé]|vai ser|será))?\s+(?:o\s+|a\s+)?([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+?)(?:\s*[,.]|$)/i,
      /(?:o\s+|a\s+)?([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ]+(?:\s+[A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ]+)*)\s+(?:[eé]\s+)?(?:o\s+)?gestor/i,
      /gestor(?:a)?[:\s]+([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+?)(?:\s*[,.]|$)/i,
    ]
    let extractedGestor = ""
    for (const pattern of gestorPatterns) {
      const match = content.match(pattern)
      if (match && match[1]) {
        extractedGestor = match[1].trim()
        break
      }
    }
    if (lowerContent.includes("mesmo") || lowerContent.includes("anterior") || lowerContent.includes("igual")) {
      if (fastTrackAppliedData?.gestor) extractedGestor = fastTrackAppliedData.gestor
    }

    let extractedLocation = ""
    const locationPatterns = [
      /(?:localiza[çc][aã]o|cidade|local|onde)[:\s]+([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s\-]+?)(?:\s*[,.]|$)/i,
      /(?:em|para)\s+([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s\-]+?)(?:\s*[,.]|$)/i,
    ]
    if ((lowerContent.includes("sim") || lowerContent.includes("mesmo") || lowerContent.includes("continua")) && fastTrackAppliedData?.localidade) {
      extractedLocation = fastTrackAppliedData.localidade
    } else if (lowerContent.includes("remoto") || lowerContent.includes("home office")) {
      extractedLocation = "Remoto"
    } else {
      for (const pattern of locationPatterns) {
        const match = content.match(pattern)
        if (match && match[1]) {
          extractedLocation = match[1].trim()
          break
        }
      }
    }
    if (!extractedLocation && fastTrackAppliedData?.localidade) {
      extractedLocation = fastTrackAppliedData.localidade
    }

    let isAffirmativeAction = false
    let affirmativeCriteria = ""
    const affirmativeNegativePatterns = [
      /n[aã]o\s+[eé]\s+afirmativa/i,
      /n[aã]o\s+afirmativa/i,
      /n[aã]o,?\s*(?:n[aã]o\s+)?[eé]?\s*afirmativa/i,
    ]
    const affirmativePositivePatterns = [
      /afirmativa\s+(?:para\s+)?(mulheres?|pcd|pessoas?\s+com\s+defici[êe]ncia|negr[oa]s?|lgbtq?\+?|50\+)/i,
      /(?:sim|[eé])\s+afirmativa/i,
      /vaga\s+afirmativa/i,
    ]
    const isNegativeAffirmative = affirmativeNegativePatterns.some(p => p.test(lowerContent))
    if (!isNegativeAffirmative) {
      for (const pattern of affirmativePositivePatterns) {
        const match = content.match(pattern)
        if (match) {
          isAffirmativeAction = true
          if (match[1]) affirmativeCriteria = match[1].trim()
          break
        }
      }
    }

    if (extractedGestor) setBasicInfoFields(prev => ({ ...prev, gestor: extractedGestor }))
    if (extractedLocation) setBasicInfoFields(prev => ({ ...prev, localidade: extractedLocation }))
    if (isAffirmativeAction) {
      setJobConfig(prev => ({ ...prev, isAffirmative: true }))
      if (affirmativeCriteria) setDetectedCriteria(prev => ({ ...prev, affirmativeCriteriaPrimary: affirmativeCriteria }))
    } else if (isNegativeAffirmative) {
      setJobConfig(prev => ({ ...prev, isAffirmative: false }))
    }

    setAwaitingSensitiveFieldsConfirmation(false)
    setFastTrackAppliedData(null)

    const confirmationParts: string[] = []
    if (extractedGestor) confirmationParts.push(`gestor: **${extractedGestor}**`)
    if (extractedLocation) confirmationParts.push(`localização: **${extractedLocation}**`)
    if (isAffirmativeAction) {
      confirmationParts.push(`vaga afirmativa: **Sim${affirmativeCriteria ? ` (${affirmativeCriteria})` : ""}**`)
    } else {
      confirmationParts.push(`vaga afirmativa: **Não**`)
    }

    const confirmMessage: Message = {
      id: `fasttrack-confirm-${Date.now()}`,
      role: "assistant",
      content: `Perfeito! Registrei ${confirmationParts.join(", ")}.\n\nAgora você pode revisar todos os detalhes no painel lateral e publicar quando estiver pronto!`,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, confirmMessage])
    setCurrentStage("review-publish")
    setWizardMode("create_from_scratch")
    return true
  }

  return {
    handleWSIRegenConfirmation,
    handleSensitiveFieldsConfirmation,
  }
}
