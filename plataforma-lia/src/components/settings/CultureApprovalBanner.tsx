"use client"

import { useTranslations } from "next-intl"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { ShieldQuestion, Check, X } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import {
  SETTINGS_QUERY_KEYS,
  dispatchSettingsUpdate,
} from "@/hooks/settings/useSettingsBroadcast"

/**
 * Fase 5.1 — Context Center HITL approval gate (2026-06-04).
 *
 * Auto-generated culture profiles (source='auto', scrape+LLM) are WITHHELD from
 * agent prompts until a human approves them (LGPD/bias — ghost-context gate).
 * This banner surfaces the pending state on Minha Empresa and lets the recruiter
 * approve/reject. Renders nothing unless an auto profile is pending — manual /
 * onboarding profiles bypass the gate and never show here.
 *
 * Reuses the canonical `cultureProfile` query key so the fetch dedupes with
 * useCompanySettingsCards' culture query (no extra round-trip).
 */
async function fetchCultureApproval(
  companyId: string,
): Promise<{ source?: string; is_approved?: boolean } | null> {
  const res = await fetch(
    `/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`,
  )
  if (!res.ok) return null
  return res.json()
}

export function CultureApprovalBanner({ companyId }: { companyId: string | null }) {
  const t = useTranslations("settings.minhaEmpresa.cultureApproval")
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: companyId
      ? SETTINGS_QUERY_KEYS.cultureProfile(companyId)
      : ["culture-profile", "none"],
    queryFn: () => fetchCultureApproval(companyId as string),
    enabled: !!companyId,
    staleTime: 30_000,
  })

  const mutation = useMutation({
    mutationFn: async (decision: "approve" | "reject") => {
      const res = await fetch(
        `/api/backend-proxy/company/culture-profile/${encodeURIComponent(
          companyId as string,
        )}/${decision}`,
        { method: "PATCH" },
      )
      if (!res.ok) throw new Error(`${decision} failed: ${res.status}`)
      return res.json()
    },
    onSuccess: (_res, decision) => {
      if (companyId) {
        queryClient.invalidateQueries({
          queryKey: SETTINGS_QUERY_KEYS.cultureProfile(companyId),
        })
      }
      queryClient.invalidateQueries({
        queryKey: SETTINGS_QUERY_KEYS.settingsProgress(),
      })
      // source: "ui" prevents this hook's own broadcast listener from reacting.
      dispatchSettingsUpdate({
        actionId: "approve_culture_profile",
        section: "culture",
        source: "ui",
        ts: Date.now(),
      })
      toast.success(decision === "approve" ? t("approvedToast") : t("rejectedToast"))
    },
    onError: () => toast.error(t("errorToast")),
  })

  // Only auto-generated, not-yet-approved profiles need the gate UI.
  const isPending = data?.source === "auto" && data?.is_approved === false
  if (!companyId || !isPending) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col gap-2 rounded-md border border-status-warning/30 bg-status-warning/10 p-3 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="flex items-start gap-2">
        <ShieldQuestion className="mt-0.5 h-4 w-4 flex-shrink-0 text-status-warning" />
        <div>
          <p className="text-[13px] font-medium text-lia-text-primary">{t("title")}</p>
          <p className="text-[12px] text-lia-text-secondary">{t("description")}</p>
        </div>
      </div>
      <div className="flex flex-shrink-0 gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={mutation.isPending}
          onClick={() => mutation.mutate("reject")}
        >
          <X className="mr-1 h-3.5 w-3.5" />
          {t("reject")}
        </Button>
        <Button
          type="button"
          size="sm"
          disabled={mutation.isPending}
          onClick={() => mutation.mutate("approve")}
        >
          <Check className="mr-1 h-3.5 w-3.5" />
          {t("approve")}
        </Button>
      </div>
    </div>
  )
}
