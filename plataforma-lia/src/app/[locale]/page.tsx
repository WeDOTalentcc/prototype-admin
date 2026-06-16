import type { Metadata } from "next"
import { DashboardApp } from "@/components/dashboard-app"
import { OnboardingController } from "@/components/onboarding/onboarding-controller"

export const metadata: Metadata = {
  title: "Dashboard | WeDoTalent",
  description: "Plataforma de recrutamento inteligente com IA — gerencie vagas, candidatos e pipelines de seleção em um só lugar.",
}

export default function Page() {
  return (
    <OnboardingController>
      <DashboardApp />
    </OnboardingController>
  )
}
