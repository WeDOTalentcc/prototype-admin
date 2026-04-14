import type { Metadata } from "next"
import { getTranslations } from "next-intl/server"
import { DashboardApp } from "@/components/dashboard-app"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('pipeline')
  return {
    title: `${t('funnelTitle')} | LIA — WeDo Talent`,
    description: t('funnelMetaDescription'),
  }
}

export default function FunilPage() {
  return (
    <ErrorBoundarySection>
      <DashboardApp />
    </ErrorBoundarySection>
  )
}
