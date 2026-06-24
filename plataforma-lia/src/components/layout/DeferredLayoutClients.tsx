"use client"

import dynamic from "next/dynamic"
import { LIAGlobalModals } from "@/components/lia-global-modals/LIAGlobalModals"

const UnifiedChatConditional = dynamic(
  () => import("@/components/unified-chat").then((m) => ({ default: m.UnifiedChatConditional })),
  { ssr: false }
)


const GlobalSelectionChat = dynamic(
  () => import("@/components/shared/GlobalSelectionChat").then((m) => ({ default: m.GlobalSelectionChat })),
  { ssr: false }
)

const WeeklyDigestChatProvider = dynamic(
  () =>
    import("@/components/notifications/weekly-digest-chat-provider").then((m) => ({
      default: m.WeeklyDigestChatProvider,
    })),
  { ssr: false }
)

export default function DeferredLayoutClients() {
  return (
    <>
      <UnifiedChatConditional />
      <WeeklyDigestChatProvider />
      <LIAGlobalModals />
      <GlobalSelectionChat />
    </>
  )
}
