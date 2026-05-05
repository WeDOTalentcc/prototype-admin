import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { CandidatesPage } from "@/components/pages/candidates-page"

export const metadata: Metadata = {
  title: "Funil de Talentos | LIA — WeDo Talent",
  description: "Visualize o funil consolidado de candidatos das suas vagas e bancos de talentos.",
}

// Funil de Talentos as a real App Router page so /pt/funil-de-talentos opens
// the canvas on direct access and survives F5. The (dashboard) layout wraps
// us in DashboardApp; when initialPage === currentPage === "Funil de Talentos"
// (computed by DashboardLayoutClient::ROUTE_TO_PAGE), DashboardApp renders
// `children` — i.e. this CandidatesPage — instead of the renderCurrentPage()
// switch. PAGE_ROUTES["Funil de Talentos"] = "/funil-de-talentos" keeps the
// URL in sync when the sidebar item is clicked from another canvas.
export default function FunilDeTalentosRoute() {
  return (
    <ErrorBoundarySection>
      <CandidatesPage />
    </ErrorBoundarySection>
  )
}
