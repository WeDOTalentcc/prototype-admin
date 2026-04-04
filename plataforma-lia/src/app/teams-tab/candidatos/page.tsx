"use client"

import { CandidatesPage } from "@/components/pages/candidates-page"
import { useTeamsSSOContext } from "@/contexts/teams-sso-context"
import { useTeamsTabTracker } from "@/hooks/use-teams-tab-tracker"

export default function TeamsTabCandidatos() {
  const { teamsUserId, platformUserId } = useTeamsSSOContext()
  // Automatically fires prolonged_stay after 3 min.
  // Fine-grained events (e.g. click_edit_candidate) can be wired via
  // CandidatesPage props when the component exposes the right callbacks.
  useTeamsTabTracker({ teamsUserId, platformUserId })

  return <CandidatesPage />
}
