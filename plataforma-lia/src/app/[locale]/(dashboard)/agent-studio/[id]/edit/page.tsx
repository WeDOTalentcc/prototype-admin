import { getTranslations } from "next-intl/server"
import EditAgentClient from "./EditAgentClient"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export async function generateMetadata() {
  const t = await getTranslations("agents.customAgents")
  return {
    title: t("editBtn"),
  }
}

interface PageProps {
  params: Promise<{ id: string; locale: string }>
}

export default async function EditAgentPage({ params }: PageProps) {
  const { id } = await params
  return (
    <ErrorBoundarySection>
      <EditAgentClient agentId={id} />
    </ErrorBoundarySection>
  )
}
