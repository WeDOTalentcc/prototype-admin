import { getTranslations } from "next-intl/server"
import AgentStudioClient from "./AgentStudioClient"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export async function generateMetadata() {
  const t = await getTranslations("agents.metadata")
  return {
    title: t("title"),
    description: t("description"),
  }
}

export default function AgentStudioPage() {
  return (
    <ErrorBoundarySection>
      <AgentStudioClient />
    </ErrorBoundarySection>
  )
}
