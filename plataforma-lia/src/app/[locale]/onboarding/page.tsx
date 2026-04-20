"use client"

import React, { useEffect, useState } from "react"
import { OnboardingChatPage } from "@/components/onboarding/OnboardingChatPage"
import { UnifiedChat } from "@/components/unified-chat/UnifiedChat"

export default function OnboardingRoutePage() {
  const [userId, setUserId] = useState<number | null>(null)
  const [sessionId, setSessionId] = useState<string>("")

  useEffect(() => {
    if (typeof window === "undefined") return
    const params = new URLSearchParams(window.location.search)
    setSessionId(params.get("session") || `onb-${Date.now()}`)

    fetch("/api/backend-proxy/users/me", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((u) => {
        const id = u?.id ?? u?.user_id
        if (typeof id === "number") setUserId(id)
        else if (typeof id === "string" && /^\d+$/.test(id)) setUserId(Number(id))
        else setUserId(0)
      })
      .catch(() => setUserId(0))
  }, [])

  if (userId === null) {
    return (
      <div className="fixed inset-0 z-40 bg-lia-bg-primary flex items-center justify-center">
        <div className="text-center">
          <div className="w-6 h-6 mx-auto mb-3 border-2 border-wedo-cyan border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-lia-text-secondary">Carregando seu onboarding...</p>
        </div>
      </div>
    )
  }

  return (
    <OnboardingChatPage sessionId={sessionId} userId={userId}>
      <UnifiedChat renderMode="inline" />
    </OnboardingChatPage>
  )
}
