"use client"

import { useEffect, useRef } from "react"
import { usePathname } from "next/navigation"
import { useWeeklyDigest } from "@/hooks/ai/use-weekly-digest"
import { useLiaFloat, useLiaChatContext } from "@/contexts/lia-float-context"
import { useAuth } from "@/contexts/auth-context"

export function WeeklyDigestChatProvider() {
  const { user: authUser } = useAuth()
  const pathname = usePathname()
  const { open } = useLiaFloat()
  const { addChatMessage } = useLiaChatContext()

  const injectedRef = useRef(false)
  const lastUserRef = useRef(authUser?.email)

  if (lastUserRef.current !== authUser?.email) {
    lastUserRef.current = authUser?.email
    injectedRef.current = false
  }

  const weeklyDigest = useWeeklyDigest({
    enabled: true,
    triggerOnMonday: true,
    userId: authUser?.email,
  })

  useEffect(() => {
    if (!weeklyDigest.isVisible || !weeklyDigest.digest) return
    if (injectedRef.current) return

    injectedRef.current = true

    const digest = weeklyDigest.digest
    const recruiterName = authUser?.name?.split(" ")[0] || "Ana"

    const summaryParts = [
      `Resumo Semanal — ${digest.date}`,
      `Pipeline: ${digest.pipeline.activeJobs} vagas, ${digest.pipeline.screened} triados, ${digest.pipeline.interviews} entrevistas.`,
    ]
    if (digest.atRiskJobs.length > 0) {
      summaryParts.push(`${digest.atRiskJobs.length} vaga(s) em risco.`)
    }
    summaryParts.push(`Compliance: ${digest.compliance.status}.`)

    const message = {
      id: `weekly-digest-${Date.now()}`,
      sender: "lia" as const,
      content: summaryParts.join(" "),
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      metadata: {
        type: "weekly_digest",
        digest,
        recruiterName,
      },
    }

    const isOnChatPage = pathname === "/chat" || pathname?.startsWith("/chat/")

    if (!isOnChatPage) {
      window.dispatchEvent(new CustomEvent("lia:chat-mode-changed", { detail: { mode: "sidebar" } }))
      open()
    }

    addChatMessage(message)
    weeklyDigest.dismiss()
  }, [weeklyDigest.isVisible, weeklyDigest.digest, weeklyDigest.dismiss, pathname, open, addChatMessage, authUser?.name])

  return null
}
