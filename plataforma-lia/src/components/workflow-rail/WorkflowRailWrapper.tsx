"use client"

import React, { useCallback } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useLocale } from "next-intl"
import { useAuthStore } from "@/stores/auth-store"
import { isAuthRoute } from "@/lib/auth-routes"
import WorkflowRail from "./WorkflowRail"

/**
 * Client wrapper for WorkflowRail — connects to auth context and router.
 * Used in root layout (server component) to bridge client-side state.
 *
 * NOTE: A visibilidade do trilho agora é controlada globalmente pelo
 * `useWorkflowRailStore` (toggle no rodapé do sidebar). O wrapper só
 * provê navegação e identidade.
 */
export default function WorkflowRailWrapper() {
  const router = useRouter()
  const pathname = usePathname()
  const locale = useLocale()
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  const handleCreateJob = useCallback(() => {
    const target = `/${locale}/jobs?action=create`
    if (pathname?.includes("/jobs")) {
      router.replace(target)
    } else {
      router.push(target)
    }
  }, [router, pathname, locale])

  const handleNavigate = useCallback((path: string) => {
    const localePrefix = `/${locale}`
    const target = path.startsWith(localePrefix) ? path : `${localePrefix}${path}`
    router.push(target)
  }, [router, locale])

  if (isAuthRoute(pathname ?? "")) return null

  // Task #592 — Educational phase: in development we want the rail visible
  // even without a real session so designers/recruiters can perceive the
  // unified funnel vocabulary. Production keeps the strict auth check.
  const isDev = process.env.NODE_ENV !== "production"

  if (!isAuthenticated || !user?.id) {
    if (!isDev) return null
    return (
      <WorkflowRail
        userId="dev-demo-user"
        onNavigate={handleNavigate}
        onCreateJob={handleCreateJob}
      />
    )
  }

  return (
    <WorkflowRail
      userId={user.id}
      onNavigate={handleNavigate}
      onCreateJob={handleCreateJob}
    />
  )
}
