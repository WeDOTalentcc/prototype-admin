"use client"

import dynamic from "next/dynamic"

const UnifiedChatConditional = dynamic(
  () => import("@/components/unified-chat").then((m) => ({ default: m.UnifiedChatConditional })),
  { ssr: false }
)

const WeeklyDigestChatProvider = dynamic(
  () =>
    import("@/components/notifications/weekly-digest-chat-provider").then((m) => ({
      default: m.WeeklyDigestChatProvider,
    })),
  { ssr: false }
)

const WorkflowRailWrapper = dynamic(
  () => import("@/components/workflow-rail/WorkflowRailWrapper"),
  { ssr: false }
)

export default function DeferredLayoutClients() {
  return (
    <>
      <WorkflowRailWrapper />
      <UnifiedChatConditional />
      <WeeklyDigestChatProvider />
    </>
  )
}
