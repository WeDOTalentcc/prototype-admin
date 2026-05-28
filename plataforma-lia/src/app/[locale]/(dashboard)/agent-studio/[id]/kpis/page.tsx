// Onda 4 F3 (2026-05-28) — KPIs dashboard de agente individual.
//
// Sub-rota /agent-studio/{id}/kpis canonical. Servidor delega tradução para
// metadata; toda renderização é client-side via <AgentKpisClient>.

import { getTranslations } from "next-intl/server"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import AgentKpisClient from "./AgentKpisClient"

export async function generateMetadata() {
  const t = await getTranslations("agents.studio.kpis")
  return {
    title: t("title"),
  }
}

interface PageProps {
  params: Promise<{ id: string; locale: string }>
}

export default async function AgentKpisPage({ params }: PageProps) {
  const { id } = await params
  return (
    <ErrorBoundarySection>
      <AgentKpisClient agentId={id} />
    </ErrorBoundarySection>
  )
}
