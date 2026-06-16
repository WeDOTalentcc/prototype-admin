import { getTranslations } from "next-intl/server"
import MarketplaceClient from "./MarketplaceClient"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export async function generateMetadata() {
  const t = await getTranslations("agents.metadata")
  return {
    title: t("marketplaceTitle") || "Marketplace de Agentes",
    description: t("marketplaceDescription") || "Explore agentes prontos do marketplace WeDOTalent",
  }
}

export default function MarketplacePage() {
  return (
    <ErrorBoundarySection>
      <MarketplaceClient />
    </ErrorBoundarySection>
  )
}
