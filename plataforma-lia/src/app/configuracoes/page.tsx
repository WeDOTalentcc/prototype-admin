import type { Metadata } from "next"
import { DashboardApp } from "@/components/dashboard-app"

export const metadata: Metadata = {
  title: "Configurações | LIA — WeDo Talent",
  description: "Configure sua conta, preferências da plataforma, integrações e configurações da empresa no LIA WeDoTalent.",
}

export default function ConfiguracoesPage() {
  return <DashboardApp initialPage="Configurações" />
}
