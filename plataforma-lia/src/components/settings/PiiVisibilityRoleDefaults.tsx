"use client"

import { useState, useEffect } from "react"
import { useTranslations } from "next-intl"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api/api-fetch"
import { PiiFieldVisibilityMatrix } from "./PiiFieldVisibilityMatrix"
import { HubLoadingState, HubErrorState } from "./_shared"
import type { PiiFieldVisibility, PiiVisibilityDefaults } from "./user-management-types"

const ROLES = ["admin", "manager", "recruiter", "viewer"] as const
type TenantRole = (typeof ROLES)[number]

export function PiiVisibilityRoleDefaults() {
  const t = useTranslations("settings.users")
  const queryClient = useQueryClient()

  // ── Server data (React Query) ──────────────────────────────────────────
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["pii-visibility-defaults"],
    queryFn: () =>
      apiFetch("/api/backend-proxy/pii-visibility-defaults")
        .then((r) => r.json())
        .then((body: { defaults: PiiVisibilityDefaults }) => body),
  })

  // ── Draft state (UI state, NOT server data — synced via useEffect) ─────
  const [draft, setDraft] = useState<PiiVisibilityDefaults>({})
  const [saveSuccess, setSaveSuccess] = useState(false)

  useEffect(() => {
    if (data?.defaults) {
      setDraft(data.defaults)
    }
  }, [data])

  // ── Mutation ───────────────────────────────────────────────────────────
  const mutation = useMutation({
    mutationFn: () =>
      apiFetch("/api/backend-proxy/pii-visibility-defaults", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ defaults: draft }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pii-visibility-defaults"] })
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    },
  })

  const roleLabelMap: Record<TenantRole, string> = {
    admin: t("roleAdmin"),
    manager: t("roleManager"),
    recruiter: t("roleRecruiter"),
    viewer: t("roleViewer"),
  }

  // ── Loading / error ────────────────────────────────────────────────────
  if (isLoading) return <HubLoadingState />
  if (error) return <HubErrorState onRetry={refetch} />

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium text-lia-text-primary">
          {t("piiVisibility.roleDefaultsTitle")}
        </h3>
        <p className="text-xs text-lia-text-secondary mt-0.5">
          {t("piiVisibility.roleDefaultsSubtitle")}
        </p>
      </div>

      <div className="space-y-6">
        {ROLES.map((role) => (
          <div key={role} className="space-y-2">
            <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide">
              {roleLabelMap[role]}
            </h4>
            <PiiFieldVisibilityMatrix
              value={(draft[role] ?? {}) as PiiFieldVisibility}
              onChange={(next: PiiFieldVisibility) =>
                setDraft((prev) => ({ ...prev, [role]: next }))
              }
              disabled={mutation.isPending}
            />
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3 pt-2">
        <button
          type="button"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="px-3 py-1.5 text-xs font-medium rounded-md bg-lia-btn-primary-bg text-white hover:bg-lia-btn-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {mutation.isPending
            ? t("piiVisibility.saving")
            : t("saveChanges")}
        </button>
        {saveSuccess && (
          <span className="text-xs text-status-success" aria-live="polite">
            {t("piiVisibility.saveSuccess")}
          </span>
        )}
        {mutation.isError && (
          <span className="text-xs text-status-error" aria-live="polite">
            {t("piiVisibility.saveError")}
          </span>
        )}
      </div>
    </div>
  )
}
