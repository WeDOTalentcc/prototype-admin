import type { Metadata } from "next"
import IntegracoesClient from "./IntegracoesClient"

export const metadata: Metadata = {
  title: "Integrações | LIA — WeDo Talent",
  description: "Conecte a Plataforma LIA WeDoTalent com Google Calendar, Microsoft Teams e outras ferramentas para potencializar seu processo seletivo.",
}

export default function IntegracoesPage() {
  return <IntegracoesClient />
}
