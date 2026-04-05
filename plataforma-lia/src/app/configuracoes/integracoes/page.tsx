import type { Metadata } from "next"
import IntegracoesClient from "./IntegracoesClient"

export const metadata: Metadata = {
  title: "Integrações | LIA — WeDo Talent",
  description: "Hub de Integrações — conecte LLMs, ATS, calendários, comunicação, CRMs e APIs à Plataforma LIA WeDoTalent.",
}

export default function IntegracoesPage() {
  return <IntegracoesClient />
}
