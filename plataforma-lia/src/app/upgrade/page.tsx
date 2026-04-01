import type { Metadata } from "next"
import UpgradeClient from "./UpgradeClient"

export const metadata: Metadata = {
  title: "Upgrade de Plano | LIA — WeDo Talent",
  description: "Faça upgrade do seu plano LIA WeDoTalent e desbloqueie funcionalidades avançadas de recrutamento com inteligência artificial.",
}

export default function UpgradePage() {
  return <UpgradeClient />
}
