import type { Metadata } from "next"
import { AiCreditsPage } from "@/components/pages/ai-credits-page"

export const metadata: Metadata = {
  title: "Créditos de IA | LIA — WeDo Talent",
  description: "Gerencie e monitore o consumo de créditos de inteligência artificial da sua conta LIA WeDoTalent.",
}

export default function AiCreditsSettingsPage() {
  return <AiCreditsPage />
}
