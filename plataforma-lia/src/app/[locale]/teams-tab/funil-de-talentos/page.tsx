"use client"

import { CandidatesPage } from "@/components/pages/candidates-page"
import { useTeamsSSOContext } from "@/contexts/teams-sso-context"
import { useTeamsTabTracker } from "@/hooks/shared/use-teams-tab-tracker"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

/**
 * Teams Tab — Funil de Talentos
 *
 * Manifest entry: tab-funil → /teams-tab/funil-de-talentos.
 * Reuses CandidatesPage (funil consolidado de candidatos). Substitui a antiga
 * aba "Candidatos" alinhando ao novo nome canônico do menu.
 * SSO + behavioral tracker auto-applied via TeamsSSOProvider in layout.
 */
export default function TeamsTabFunilDeTalentos() {
  const { teamsUserId, platformUserId } = useTeamsSSOContext()
  useTeamsTabTracker({ teamsUserId, platformUserId })

  return (
    <ErrorBoundarySection>
      <CandidatesPage />
    </ErrorBoundarySection>
  )
}
