import type { Metadata } from "next"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"
import { CandidatesPage } from "@/components/pages/candidates-page"

export const metadata: Metadata = {
  title: "Funil de Talentos | WeDoTalent",
  description: "Visualize o funil consolidado de candidatos das suas vagas e bancos de talentos.",
}

// Funil de Talentos as a real App Router page so /pt/funil-de-talentos opens
// the canvas on direct access and survives F5. The (dashboard) layout wraps
// us in DashboardApp; when initialPage === currentPage === "Funil de Talentos"
// (computed by DashboardLayoutClient via `labelFromPath`), DashboardApp renders
// `children` — i.e. this CandidatesPage — instead of the renderCurrentPage()
// switch. The `"Funil de Talentos" → "/funil-de-talentos"` entry in
// `src/lib/navigation/routes.ts` (PAGE_PATHS) keeps the URL in sync when the
// sidebar item is clicked from another canvas.
export default function FunilDeTalentosRoute() {
  return (
    <ErrorBoundarySection>
      <CandidatesPage />
    </ErrorBoundarySection>
  )
}
