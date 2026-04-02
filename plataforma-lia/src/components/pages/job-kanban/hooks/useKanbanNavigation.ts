"use client"

import { useRef, useEffect, useCallback } from "react"
import { type KanbanCandidate, type DynamicStage } from "@/components/kanban"
import { toast } from "sonner"

interface UseKanbanNavigationProps {
  jobId: string | undefined
  candidatesData: Record<string, Record<string, unknown>[]>
  dynamicStages: DynamicStage[]
  openTransition: (candidates: KanbanCandidate[], from: string, to: string) => void
  setTransitionInitialPrompt: (p: string) => void
  setTransitionAllowStageSelection: (v: boolean) => void
  setLiaPromptValue: (v: string) => void
  setShowExpandedLIA: (v: boolean) => void
  setPreviewCandidate: (c: Record<string, unknown> | null) => void
  setIsPreviewOpen: (v: boolean) => void
  // pendingCommunicationAction useEffect props
  setUnifiedModalCandidate: (c: unknown) => void
  setUnifiedModalType: (t: string) => void
  setUnifiedModalOpen: (v: boolean) => void
}

export function useKanbanNavigation({
  jobId,
  candidatesData,
  dynamicStages,
  openTransition,
  setTransitionInitialPrompt,
  setTransitionAllowStageSelection,
  setLiaPromptValue,
  setShowExpandedLIA,
  setPreviewCandidate,
  setIsPreviewOpen,
  setUnifiedModalCandidate,
  setUnifiedModalType,
  setUnifiedModalOpen,
}: UseKanbanNavigationProps) {
  const pendingNavigationRef = useRef<{
    nav: {
      candidateId?: string
      candidateName?: string
      jobId?: string
      jobTitle?: string
      currentStage?: string
      interviewType?: string
      action?: string
      openTransitionModal?: boolean
    }
    prompt: string | null
  } | null>(null)

  const processPendingNavigation = useCallback(() => {
    if (!pendingNavigationRef.current) return false
    const allCands = Object.values(candidatesData).flat()
    if (allCands.length === 0) return false

    const { nav, prompt } = pendingNavigationRef.current
    pendingNavigationRef.current = null

    const matched = allCands.find(
      (c: Record<string, unknown>) =>
        (nav.candidateId && String(c.id) === String(nav.candidateId)) ||
        (nav.candidateName && c.name === nav.candidateName)
    )

    if (nav.openTransitionModal) {
      if (matched) {
        const candidateStage = Object.entries(candidatesData).find(
          ([, cands]) => (cands as Record<string, unknown>[]).some((c: Record<string, unknown>) => c.id === matched.id)
        )

        let fromStage = candidateStage?.[0] || nav.currentStage || ""
        let toStage = fromStage

        if (nav.action === "reschedule" || nav.action === "cancel") {
          const interviewSlugMap: Record<string, string> = {
            technical: "interview_hr",
            behavioral: "interview_hr",
            cultural: "interview_hr",
            final: "interview_final",
          }
          const interviewStageId = interviewSlugMap[(nav as Record<string, unknown>).interviewType as string] || "interview_hr"
          const matchedStage = dynamicStages.find(s => s.id === interviewStageId || s.actionBehavior === "scheduling")
          if (matchedStage) {
            fromStage = matchedStage.id
            toStage = matchedStage.id
          }
        }

        const kanbanCandidate: KanbanCandidate = {
          id: (matched as unknown as Record<string, unknown>).id as string,
          name: (matched as unknown as Record<string, unknown>).name as string,
          email: (matched as unknown as Record<string, unknown>).email as string | undefined,
          phone: (matched as unknown as Record<string, unknown>).phone as string | undefined,
          avatar: (matched as unknown as Record<string, unknown>).avatar as string | undefined,
          role: ((matched as unknown as Record<string, unknown>).role || (matched as unknown as Record<string, unknown>).currentTitle) as string | undefined,
          currentTitle: (matched as unknown as Record<string, unknown>).currentTitle as string | undefined,
          currentCompany: ((matched as unknown as Record<string, unknown>).currentCompany || (matched as unknown as Record<string, unknown>).company) as string | undefined,
          location: (matched as unknown as Record<string, unknown>).location as string | undefined,
          stage: fromStage,
          sub_status: (matched as unknown as Record<string, unknown>).sub_status as string | undefined,
          stageId: fromStage,
        }

        if (prompt) {
          setTransitionInitialPrompt(prompt)
        }
        if (nav.action === "cancel" || nav.action === "reschedule") {
          setTransitionAllowStageSelection(true)
        }
        openTransition([kanbanCandidate], fromStage, toStage)
      }
    } else {
      if (prompt) {
        setLiaPromptValue(prompt)
        setShowExpandedLIA(true)
      }
      if (matched) {
        setPreviewCandidate(matched as Record<string, unknown>)
        setIsPreviewOpen(true)
      }
    }
    return true
  }, [candidatesData, dynamicStages, openTransition, setTransitionInitialPrompt, setLiaPromptValue, setShowExpandedLIA, setPreviewCandidate, setIsPreviewOpen, setTransitionAllowStageSelection])

  useEffect(() => {
    const raw = localStorage.getItem("navigateToCandidate")
    if (!raw) return

    try {
      const nav = JSON.parse(raw) as {
        candidateId?: string
        candidateName?: string
        jobId?: string
        jobTitle?: string
        currentStage?: string
        interviewType?: string
        action?: string
        openTransitionModal?: boolean
      }
      localStorage.removeItem("navigateToCandidate")

      const prompt = localStorage.getItem("liaPrompt")
      if (prompt) {
        localStorage.removeItem("liaPrompt")
      }

      pendingNavigationRef.current = { nav, prompt }
      processPendingNavigation()
    } catch (e) {
      localStorage.removeItem("navigateToCandidate")
      localStorage.removeItem("liaPrompt")
    }
  }, [jobId, processPendingNavigation])

  useEffect(() => {
    processPendingNavigation()
  }, [candidatesData, processPendingNavigation])

  // Detect pending communication action (from job unpublish with notification)
  useEffect(() => {
    const pendingAction = localStorage.getItem("pendingCommunicationAction")
    if (pendingAction) {
      try {
        const action = JSON.parse(pendingAction) as {
          jobId: string
          template?: string
          candidateIds?: string[]
          channel?: "email" | "whatsapp"
        }
        if (action.jobId && String(action.jobId) === String(jobId)) {
          localStorage.removeItem("pendingCommunicationAction")
          setTimeout(() => {
            const candidateCount = action.candidateIds?.length || 0
            const channelType = action.channel === "whatsapp" ? "whatsapp" : "email"
            setUnifiedModalCandidate(null)
            setUnifiedModalType(channelType)
            setUnifiedModalOpen(true)
            if (candidateCount > 0) {
              toast.success("Modal de comunicação aberto", { description: `${candidateCount} candidato(s) prontos para notificação via ${channelType === "whatsapp" ? "WhatsApp" : "E-mail"}.` })
            }
          }, 500)
        }
      } catch (e) {
        localStorage.removeItem("pendingCommunicationAction")
      }
    }
  }, [jobId, setUnifiedModalCandidate, setUnifiedModalType, setUnifiedModalOpen])

  return {
    pendingNavigationRef,
    processPendingNavigation,
  }
}
