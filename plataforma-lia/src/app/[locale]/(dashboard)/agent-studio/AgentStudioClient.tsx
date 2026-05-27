"use client"

import React, { useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import AgentStudioPage from "@/components/pages-agent-studio/AgentStudioPage"
import CalibrationCardModal from "@/components/pages-agent-studio/CalibrationCardModal"
import { useLiaChatContext } from "@/contexts/lia-float-context"
import { navigateToJobDetail } from "@/lib/navigation/job-navigation"

/**
 * AgentStudioClient — wraps AgentStudioPage and notifies the global UnifiedChat
 * provider that the user is in the Agent Studio context.
 *
 * Without this, getPageContext() fallback would treat /agent-studio as
 * "general", and short messages like "oi" would route to recruiter_assistant
 * (default) and end up in the Tier 8 clarification fallback — which the
 * UnifiedChat does not render today, producing a silent chat.
 *
 * On unmount we revert to "general" so the next page starts clean.
 *
 * Wave A P0 #8 (2026-05-27): wires onStartCalibration / onNavigateToPool /
 * onNavigateToJob — sem isso os botões "Recalibrar" e "Ver" do sourcing-card
 * eram no-op. Pattern espelha dashboard-app.tsx (caso "Estúdio de Agentes").
 */
export default function AgentStudioClient() {
  const router = useRouter()
  const { switchChatContext } = useLiaChatContext()
  // `switchChatContext` from the provider changes reference on every parent
  // render (its useCallback depends on `connection`, which is re-created each
  // render). Pin it behind a ref so this effect runs once on mount and once
  // on unmount, without retriggering on every render.
  const switchRef = useRef(switchChatContext)
  switchRef.current = switchChatContext

  // Wave A P0 #8: CalibrationCardModal mounted via local state (mirrors
  // dashboard-app.tsx canonical pattern). AgentStudioPage emits agentId
  // through onStartCalibration; we open the modal here.
  const [calibratingAgentId, setCalibratingAgentId] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    switchRef.current("agent_studio", { conversationId: null })
    return () => {
      switchRef.current("general", { conversationId: null })
    }
  }, [])

  return (
    <div className="h-full">
      <AgentStudioPage
        key={refreshKey}
        onStartCalibration={(agentId) => setCalibratingAgentId(agentId)}
        onNavigateToJob={(jobId) => {
          // Canonical: rota é /[locale]/jobs/[id]. Use navigateToJobDetail
          // (single navigation source — sensor enforça em
          // src/lib/navigation/__tests__/job-navigation.test.ts).
          navigateToJobDetail(router, jobId)
        }}
        onNavigateToPool={(poolId) => {
          // Canonical: rota é /[locale]/bancos-de-talentos/[id] (vide
          // BancosClient.tsx). Locale é prefixado pelo middleware next-intl,
          // mas seguimos o pattern explícito do BancosClient.
          router.push(`/bancos-de-talentos/${encodeURIComponent(poolId)}`)
        }}
      />
      {calibratingAgentId && (
        <CalibrationCardModal
          agentId={calibratingAgentId}
          isOpen={!!calibratingAgentId}
          onClose={() => setCalibratingAgentId(null)}
          onCalibrationComplete={() => {
            setCalibratingAgentId(null)
            setRefreshKey((k) => k + 1)
          }}
        />
      )}
    </div>
  )
}
