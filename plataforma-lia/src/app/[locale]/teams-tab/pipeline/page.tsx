"use client"

import { PipelineOverviewPage } from "@/components/pages/pipeline-overview-page"
import { useTeamsSSOContext } from "@/contexts/teams-sso-context"
import { useTeamsTabTracker } from "@/hooks/shared/use-teams-tab-tracker"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

/**
 * Teams Tab — Pipeline Overview
 *
 * Manifest entry: tab-pipeline → /teams-tab/pipeline (W5.1).
 * Reuses PipelineOverviewPage from the main platform.
 * SSO + behavioral tracker auto-applied via TeamsSSOProvider in layout.
 */
export default function TeamsTabPipeline() {
  const { teamsUserId, platformUserId } = useTeamsSSOContext()
  useTeamsTabTracker({ teamsUserId, platformUserId })

  return (
    <ErrorBoundarySection>
      <PipelineOverviewPage />
    </ErrorBoundarySection>
  )
}
