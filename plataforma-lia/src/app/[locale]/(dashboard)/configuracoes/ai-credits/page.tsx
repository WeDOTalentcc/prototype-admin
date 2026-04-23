"use client"

import dynamic from "next/dynamic"

const AiCreditsPage = dynamic(
  () => import("@/components/pages/ai-credits-page").then((m) => ({ default: m.AiCreditsPage })),
  { ssr: false }
)

export default function AiCreditsSettingsPage() {
  return <AiCreditsPage />
}
