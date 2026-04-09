"use client"

import React from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth-store"
import WorkflowRail from "./WorkflowRail"

/**
 * Client wrapper for WorkflowRail — connects to auth context and router.
 * Used in root layout (server component) to bridge client-side state.
 */
export default function WorkflowRailWrapper() {
  const router = useRouter()
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  if (!isAuthenticated || !user?.id) return null

  return (
    <WorkflowRail
      userId={user.id}
      onNavigate={(path) => router.push(path)}
    />
  )
}
