"use client"

import { useCallback } from "react"
import { JobsPage } from "@/components/pages/jobs-page"
import { useTeamsSSOContext } from "@/contexts/teams-sso-context"
import { useTeamsTabTracker } from "@/hooks/shared/use-teams-tab-tracker"

export default function TeamsTabVagas() {
  const { teamsUserId, platformUserId } = useTeamsSSOContext()
  const { trackEvent } = useTeamsTabTracker({ teamsUserId, platformUserId })

  // Intercept navigation events triggered inside JobsPage.
  // When the user tries to reach routes that require the full platform, fire a
  // proactive Teams message with a deep link instead of navigating in the iframe.
  const handleNavigate = useCallback(
    (page: string) => {
      if (page === "new-job" || page === "create-job" || page?.includes("new")) {
        trackEvent("click_create_job")
        return // do not navigate — the proactive card will guide them
      }
      if (page?.includes("pipeline") || page?.includes("configuracoes")) {
        trackEvent("click_edit_pipeline")
        return
      }
      if (page?.includes("settings") || page?.includes("edit")) {
        trackEvent("click_job_settings")
        return
      }
      // Allow other navigations silently
    },
    [trackEvent],
  )

  return <JobsPage onNavigate={handleNavigate} />
}
