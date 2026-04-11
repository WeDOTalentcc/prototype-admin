"use client"

/**
 * TeamsSSOContext
 *
 * Wraps Teams Tab pages with silent SSO initialization.
 * Provides teamsUserId and platformUserId to child components via context.
 */

import { createContext, useContext, ReactNode } from "react"
import { useTeamsSSO } from "@/hooks/company/use-teams-sso"

interface TeamsSSOContextType {
  isTeams: boolean
  isAuthenticated: boolean
  isLoading: boolean
  teamsUserId: string | null
  platformUserId: string | null
  error: string | null
}

const TeamsSSOContext = createContext<TeamsSSOContextType>({
  isTeams: false,
  isAuthenticated: false,
  isLoading: false,
  teamsUserId: null,
  platformUserId: null,
  error: null,
})

export function TeamsSSOProvider({ children }: { children: ReactNode }) {
  const sso = useTeamsSSO()

  return (
    <TeamsSSOContext.Provider value={sso}>
      {children}
    </TeamsSSOContext.Provider>
  )
}

export function useTeamsSSOContext() {
  return useContext(TeamsSSOContext)
}
