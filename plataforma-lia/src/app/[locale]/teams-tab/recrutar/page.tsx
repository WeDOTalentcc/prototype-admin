"use client"

import { PipelineOverviewPage } from "@/components/pages/pipeline-overview-page"
import { useTeamsSSOContext } from "@/contexts/teams-sso-context"
import { useTeamsTabTracker } from "@/hooks/shared/use-teams-tab-tracker"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

/**
 * Teams Tab — Recrutar
 *
 * Manifest entry: tab-recrutar → /teams-tab/recrutar.
 * Reuses PipelineOverviewPage (visão global do pipeline de recrutamento),
 * mesmo componente da rota (dashboard)/recrutar.
 * SSO + behavioral tracker auto-applied via TeamsSSOProvider in layout.
 */
export default function TeamsTabRecrutar() {
  const { teamsUserId, platformUserId } = useTeamsSSOContext()
  useTeamsTabTracker({ teamsUserId, platformUserId })

  return (
    <ErrorBoundarySection>
      <PipelineOverviewPage />
    </ErrorBoundarySection>
  )
}
