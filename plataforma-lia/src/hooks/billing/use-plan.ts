"use client"

import { useQuery } from "@tanstack/react-query"

interface PlanSummary {
  plan_code: "starter" | "professional" | "enterprise" | "custom" | string
  plan_name: string
  status: "active" | "trialing" | "suspended" | "cancelled" | string
  features_enabled: string[]
  seats_contracted: number
}

export function usePlan() {
  const { data, isLoading, error } = useQuery<PlanSummary>({
    queryKey: ["billing-plan-summary"],
    queryFn: () =>
      fetch("/api/backend-proxy/billing/plan-summary").then((r) => {
        if (!r.ok) throw new Error("plan fetch failed")
        return r.json()
      }),
    staleTime: 10 * 60_000,
    retry: 1,
  })

  // enterprise e custom desbloqueiam features Enterprise-tier
  const isEnterprise =
    data?.plan_code === "enterprise" || data?.plan_code === "custom"

  return {
    plan: data ?? null,
    planCode: data?.plan_code ?? "starter",
    isEnterprise,
    isPlanLoading: isLoading,
    planError: error,
  }
}
