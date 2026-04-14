import type { Metadata } from "next"
import { getTranslations } from "next-intl/server"
import FunilDeTalentosClient from "./FunilDeTalentosClient"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('pipeline')
  return {
    title: `${t('title')} | LIA — WeDo Talent`,
    description: t('metaDescription'),
  }
}

export default function FunilDeTalentosPage() {
  return (
    <ErrorBoundarySection>
      <FunilDeTalentosClient />
    </ErrorBoundarySection>
  )
}
