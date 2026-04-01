import type { Metadata } from "next"
import dynamic from "next/dynamic"

// AiCreditsPage usa recharts - lazy loaded para reduzir bundle inicial
const AiCreditsPage = dynamic(
  () => import("@/components/pages/ai-credits-page").then((m) => ({ default: m.AiCreditsPage })),
  { ssr: false }
)

export const metadata: Metadata = {
  title: "Créditos de IA | LIA — WeDo Talent",
  description: "Gerencie e monitore o consumo de créditos de inteligência artificial da sua conta LIA WeDoTalent.",
}

export default function AiCreditsSettingsPage() {
  return <AiCreditsPage />
}
