"use client"

import React, { useCallback } from "react"
import { useRouter, usePathname } from "next/navigation"
import { useLocale } from "next-intl"
import { useAuthStore } from "@/stores/auth-store"
import WorkflowRail from "./WorkflowRail"

/**
 * Client wrapper for WorkflowRail — connects to auth context and router.
 * Used in root layout (server component) to bridge client-side state.
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
      // Already on jobs route — replace to re-trigger search-param effect
      router.replace(target)
    } else {
      router.push(target)
    }
  }, [router, pathname, locale])

  if (!isAuthenticated || !user?.id) return null

  return (
    <WorkflowRail
      userId={user.id}
      onNavigate={(path) => router.push(path)}
      onCreateJob={handleCreateJob}
    />
  )
}
