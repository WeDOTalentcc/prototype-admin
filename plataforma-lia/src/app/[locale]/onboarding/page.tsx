"use client"

/**
 * /[locale]/onboarding/page.tsx
 *
 * Onda 4-N1 (2026-05-24): rota canonical pro conversational onboarding flow.
 *
 * Histórico: Task #712 (commit d1ed07e4d0, 2026-04-20) introduziu
 * `window.location.href = "/onboarding"` em onboarding-controller.tsx
 * mas a rota nunca foi criada. OnboardingChatPage (commit bbe4db71b, 2026-04-10
 * "complete conversational onboarding system") existe mas nunca foi instanciada.
 *
 * Resultado: usuário novo que clica "Start Setup Wizard" via Setup Intro Modal
 * caía em 404 por 35 dias. Esta page fecha o gap canonical.
 */

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { useJWTAuth } from "@/contexts/auth-context"
import { OnboardingChatPage } from "@/components/onboarding/OnboardingChatPage"
import dynamic from "next/dynamic"

const ChatPageFullscreen = dynamic(
  () => import("@/components/unified-chat/ChatPageFullscreen").then(m => ({ default: m.ChatPageFullscreen })),
  { ssr: false }
)

export default function OnboardingRoute() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading } = useJWTAuth()
  const [sessionId] = useState<string>(() => {
    if (typeof window === "undefined") return ""
    return crypto.randomUUID()
  })

  // Redirect to login if not authenticated (after initial load)
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login")
    }
  }, [isLoading, isAuthenticated, router])

  // user.id is the canonical UUID identifier; OnboardingChatPage typed userId as number
  // historically (legacy Rails int), but only uses it as a path param in backend-proxy fetch.
  // Cast pragmatically; backend handles both.
  const userId = useMemo(() => {
    if (!user) return null
    return user.id as unknown as number
  }, [user])

  if (isLoading || !user || !userId) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-lia-bg-primary">
        <div className="text-lia-text-secondary text-sm">Carregando...</div>
      </div>
    )
  }

  return (
    <OnboardingChatPage
      sessionId={sessionId}
      userId={userId}
    >
      <ChatPageFullscreen />
    </OnboardingChatPage>
  )
}
