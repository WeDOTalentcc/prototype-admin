"use client"

import { CandidatesPage } from "@/components/pages/candidates-page"
import { useTeamsSSOContext } from "@/contexts/teams-sso-context"
import { useTeamsTabTracker } from "@/hooks/shared/use-teams-tab-tracker"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

export default function TeamsTabCandidatos() {
  const { teamsUserId, platformUserId } = useTeamsSSOContext()
  useTeamsTabTracker({ teamsUserId, platformUserId })

  return (
    <ErrorBoundarySection>
      <CandidatesPage />
    </ErrorBoundarySection>
  )
}
