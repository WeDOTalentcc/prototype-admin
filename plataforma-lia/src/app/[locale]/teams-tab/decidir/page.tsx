"use client"

import { TasksPage } from "@/components/pages/tasks-page"
import { useTeamsSSOContext } from "@/contexts/teams-sso-context"
import { useTeamsTabTracker } from "@/hooks/shared/use-teams-tab-tracker"
import { ErrorBoundarySection } from "@/components/ui/error-boundary-section"

/**
 * Teams Tab — Decidir
 *
 * Manifest entry: tab-decidir → /teams-tab/decidir.
 * Reuses TasksPage (painel diário: tarefas, alertas, vagas a acompanhar).
 * SSO + behavioral tracker auto-applied via TeamsSSOProvider in layout.
 */
export default function TeamsTabDecidir() {
  const { teamsUserId, platformUserId } = useTeamsSSOContext()
  useTeamsTabTracker({ teamsUserId, platformUserId })

  return (
    <ErrorBoundarySection>
      <TasksPage />
    </ErrorBoundarySection>
  )
}
