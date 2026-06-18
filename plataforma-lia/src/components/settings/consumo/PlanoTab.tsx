"use client"

import { useQuery } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { Crown, Tag } from "lucide-react"
import { HubLoadingState, HubErrorState } from "@/components/settings/_shared"
import { Chip } from "@/components/ui/chip"
import { SETTINGS_QUERY_KEYS } from "@/hooks/settings/useSettingsBroadcast"

function PlanStatusChip({ status }: { status: string }) {
  const t = useTranslations("settings.billing")
  const variants: Record<string, "success" | "warning" | "error" | "neutral"> = {
    active: "success",
    trialing: "warning",
    suspended: "error",
    canceled: "error",
    past_due: "error",
  }
  return (
    <Chip variant={variants[status] || "neutral"}>
      {t(`status.${status}` as any) || status}
    </Chip>
  )
}

export function PlanoTab() {
  const t = useTranslations("settings.billing")

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.billing(),
    queryFn: async () => {
      const res = await fetch("/api/backend-proxy/billing/plan-summary")
      if (!res.ok) throw new Error(t("errors.loadPlan"))
      return res.json()
    },
    staleTime: 60_000,
  })

  if (isLoading) return <HubLoadingState />
  if (error) return <HubErrorState onRetry={refetch} />
  if (!data) return null

  const features: string[] = data.features_enabled || []
  const desconto = data.desconto as { pct: number; validade: string | null } | undefined

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-5 space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="rounded-lg bg-lia-bg-tertiary p-2 mt-0.5 flex-shrink-0">
              <Crown className="h-4 w-4 text-lia-text-muted" aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-medium text-lia-text-primary">
                {t("currentPlan")} {data.plan_name || data.plan_code}
              </p>
              <p className="text-xs text-lia-text-tertiary mt-0.5">
                {data.seats_contracted} {t("seats")}
              </p>
            </div>
          </div>
          <PlanStatusChip status={data.status} />
        </div>

        {data.status === "trialing" && (
          <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2">
            <p className="text-xs text-amber-800">{t("trialNotice")}</p>
          </div>
        )}

        {/* Desconto ALFA — condicional, zero impacto para não-ALFA */}
        {desconto && desconto.pct > 0 && (
          <div className="flex items-center gap-2 rounded-lg bg-teal-50 border border-teal-200 px-3 py-2">
            <Tag className="h-3.5 w-3.5 text-teal-700 flex-shrink-0" aria-hidden="true" />
            <div>
              <p className="text-xs font-medium text-teal-800">
                {t("descontoLabel").replace("{pct}", String(desconto.pct))}
              </p>
              {desconto.validade && (
                <p className="text-[10px] text-teal-600 mt-0.5">
                  {t("descontoValidade")}{" "}
                  {new Date(desconto.validade).toLocaleDateString("pt-BR")}
                </p>
              )}
            </div>
          </div>
        )}

        {features.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {features.map((f: string) => (
              <Chip key={f} variant="neutral" muted className="text-[10px]">
                {f.replace(/_/g, " ")}
              </Chip>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
