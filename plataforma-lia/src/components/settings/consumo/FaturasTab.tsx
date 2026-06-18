"use client"

import { useQuery } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import { FileText } from "lucide-react"
import { HubLoadingState, HubErrorState } from "@/components/settings/_shared"
import { Chip } from "@/components/ui/chip"
import { SETTINGS_QUERY_KEYS } from "@/hooks/settings/useSettingsBroadcast"

function InvoiceStatusChip({ status, t }: { status: string; t: (key: string) => string }) {
  const variants: Record<string, "success" | "warning" | "error" | "neutral"> = {
    paid: "success",
    pending: "warning",
    overdue: "error",
    failed: "error",
  }
  const label = t(`invoiceStatuses.${status}`) || status || "-"
  const variant = variants[status] || "neutral"
  return (
    <Chip variant={variant} muted className="text-[10px]">
      {label}
    </Chip>
  )
}

export function FaturasTab() {
  const t = useTranslations("settings.billing")

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.billingInvoices(),
    queryFn: async () => {
      const res = await fetch("/api/backend-proxy/billing/invoices?limit=6")
      if (res.status === 404) return { invoices: [] }
      if (!res.ok) throw new Error(t("errors.loadInvoices"))
      return res.json()
    },
    staleTime: 120_000,
  })

  if (isLoading) return <HubLoadingState />
  if (error) return <HubErrorState onRetry={refetch} />

  const invoices = Array.isArray(data?.invoices) ? data.invoices : Array.isArray(data) ? data : []

  if (invoices.length === 0) {
    return (
      <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-5">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-lia-text-muted" aria-hidden="true" />
          <p className="text-sm font-medium text-lia-text-primary">{t("invoices")}</p>
        </div>
        <p className="text-xs text-lia-text-tertiary mt-2">{t("noInvoices")}</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-5 space-y-3">
      <div className="flex items-center gap-2">
        <FileText className="h-4 w-4 text-lia-text-muted" aria-hidden="true" />
        <p className="text-sm font-medium text-lia-text-primary">{t("invoices")}</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-lia-text-tertiary border-b border-lia-border-subtle">
              <th className="pb-2 pr-4 font-medium">{t("invoiceDate")}</th>
              <th className="pb-2 pr-4 font-medium">{t("invoiceAmount")}</th>
              <th className="pb-2 pr-4 font-medium">{t("invoiceStatus")}</th>
              <th className="pb-2 font-medium">{t("invoicePdf")}</th>
            </tr>
          </thead>
          <tbody>
            {invoices.slice(0, 12).map((inv: any, i: number) => (
              <tr
                key={inv.id || i}
                className="border-b border-lia-border-subtle last:border-0"
              >
                <td className="py-2 pr-4 text-lia-text-secondary">
                  {inv.due_date
                    ? new Date(inv.due_date).toLocaleDateString("pt-BR")
                    : "-"}
                </td>
                <td className="py-2 pr-4 text-lia-text-primary font-medium">
                  {inv.total_cents != null
                    ? `R$ ${(inv.total_cents / 100).toFixed(2)}`
                    : inv.total || "-"}
                </td>
                <td className="py-2 pr-4">
                  <InvoiceStatusChip status={inv.status} t={t as any} />
                </td>
                <td className="py-2">
                  {inv.pdf_url ? (
                    <a
                      href={inv.pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-lia-accent-primary hover:underline"
                    >
                      {t("download")}
                    </a>
                  ) : (
                    "-"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
