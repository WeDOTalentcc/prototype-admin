"use client"

import { useQuery } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { CreditCard, Wallet, Building2 } from "lucide-react"
import { HubLoadingState, HubErrorState } from "@/components/settings/_shared"
import { SETTINGS_QUERY_KEYS } from "@/hooks/settings/useSettingsBroadcast"

export function CobrancaTab() {
  const t = useTranslations("settings.billing")

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.billingPaymentMethods(),
    queryFn: async () => {
      const res = await fetch("/api/backend-proxy/billing/payment-methods")
      if (res.status === 404) return { payment_methods: [] }
      if (!res.ok) throw new Error(t("errors.loadPaymentMethods"))
      return res.json()
    },
    staleTime: 120_000,
  })

  if (isLoading) return <HubLoadingState />
  if (error) return <HubErrorState onRetry={refetch} />

  const methods = Array.isArray(data?.payment_methods)
    ? data.payment_methods
    : Array.isArray(data)
      ? data
      : []

  return (
    <div className="space-y-4">
      {/* Meio de pagamento */}
      <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Wallet className="h-4 w-4 text-lia-text-muted" aria-hidden="true" />
          <p className="text-sm font-medium text-lia-text-primary">{t("paymentMethod")}</p>
        </div>

        {methods.length === 0 ? (
          <p className="text-xs text-lia-text-tertiary">{t("noPaymentMethod")}</p>
        ) : (
          <div className="space-y-2">
            {methods.map((m: any, i: number) => (
              <div
                key={m.id || i}
                className="flex items-center gap-3 text-sm text-lia-text-secondary"
              >
                <CreditCard className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
                <span>
                  {m.brand || m.type || t("card")}{" "}
                  {m.last4 ? `•••• ${m.last4}` : ""}{" "}
                  {m.exp_month && m.exp_year
                    ? `(${String(m.exp_month).padStart(2, "0")}/${m.exp_year})`
                    : ""}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Dados fiscais — stub (B5, wiring admin deferred) */}
      <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 text-lia-text-muted" aria-hidden="true" />
          <p className="text-sm font-medium text-lia-text-primary">{t("fiscalData")}</p>
        </div>
        <p className="text-xs text-lia-text-tertiary">{t("fiscalDataComing")}</p>
      </div>
    </div>
  )
}
