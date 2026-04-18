import type { Metadata } from "next"
import { getTranslations } from "next-intl/server"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { PipelineOverviewPage } from "@/components/pages/pipeline-overview-page"

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("pipelineOverview")
  return {
    title: `${t("title")} | LIA — WeDo Talent`,
    description: t("metaDescription"),
  }
}

export default function VisaoDoFunilPage() {
  return (
    <ErrorBoundarySection>
      <PipelineOverviewPage />
    </ErrorBoundarySection>
  )
}
