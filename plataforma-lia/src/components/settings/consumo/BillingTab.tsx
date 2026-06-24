"use client"

import { useQuery } from "@tanstack/react-query"
import { useTranslations } from "next-intl"
import {
  CreditCard,
  FileText,
  Gauge,
  Shield,
  Wallet,
  Crown,
  Zap,
  Bot,
  Search,
  Database,
} from "lucide-react"
import { HubLoadingState, HubErrorState } from "@/components/settings/_shared"
import { Chip } from "@/components/ui/chip"
import { Progress } from "@/components/ui/progress"
import { SETTINGS_QUERY_KEYS } from "@/hooks/settings/useSettingsBroadcast"

// ---------------------------------------------------------------------------
// Query hooks
// ---------------------------------------------------------------------------

function useBillingSubscription(errorMsg: string) {
  return useQuery({
    queryKey: SETTINGS_QUERY_KEYS.billing(),
    queryFn: async () => {
      const res = await fetch("/api/backend-proxy/billing/plan-summary")
      if (!res.ok) throw new Error(errorMsg)
      return res.json()
    },
    staleTime: 60_000,
  })
}

function useBillingUsage(errorMsg: string) {
  return useQuery({
    queryKey: SETTINGS_QUERY_KEYS.billingUsage(),
    queryFn: async () => {
      const res = await fetch("/api/backend-proxy/billing/usage-summary")
      if (!res.ok) throw new Error(errorMsg)
      return res.json()
    },
    staleTime: 30_000,
  })
}

function useBillingInvoices(errorMsg: string) {
  return useQuery({
    queryKey: SETTINGS_QUERY_KEYS.billingInvoices(),
    queryFn: async () => {
      const res = await fetch("/api/backend-proxy/billing/invoices?limit=6")
      if (!res.ok) throw new Error(errorMsg)
      return res.json()
    },
    staleTime: 120_000,
  })
}

function useBillingPaymentMethods(errorMsg: string) {
  return useQuery({
    queryKey: SETTINGS_QUERY_KEYS.billingPaymentMethods(),
    queryFn: async () => {
      const res = await fetch("/api/backend-proxy/billing/payment-methods")
      if (!res.ok) throw new Error(errorMsg)
      return res.json()
    },
    staleTime: 120_000,
  })
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatusBadge({ status, t }: { status: string | undefined; t: (key: string) => string }) {
  const variants: Record<string, "success" | "warning" | "danger" | "neutral"> = {
    active: "success",
    trialing: "warning",
    suspended: "danger",
    canceled: "danger",
    past_due: "danger",
  }
  if (!status) return <Chip variant="neutral">—</Chip>
  const label = t(`status.${status}`) || status
  const variant = variants[status] || "neutral"
  return <Chip variant={variant}>{label}</Chip>
}

function UsageBar({
  label,
  icon: Icon,
  used,
  cap,
  unit,
  alertThreshold = 0.8,
  capReachedText,
  capWarningTemplate,
}: {
  label: string
  icon: React.ElementType
  used: number
  cap: number
  unit: string
  alertThreshold?: number
  capReachedText: string
  capWarningTemplate: string
}) {
  const isUnlimited = cap === -1
  const pct = isUnlimited ? 0 : cap > 0 ? Math.min((used / cap) * 100, 100) : 0
  const isWarning = !isUnlimited && cap > 0 && used / cap >= alertThreshold

  function formatNumber(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
    return n.toLocaleString("pt-BR")
  }

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-1.5 text-lia-text-secondary">
          <Icon className="h-3.5 w-3.5" aria-hidden="true" />
          {label}
        </span>
        <span className="text-lia-text-primary font-medium">
          {formatNumber(used)} / {isUnlimited ? "∞" : formatNumber(cap)} {unit}
        </span>
      </div>
      {!isUnlimited && (
        <Progress
          value={pct}
          className={`h-2 ${isWarning ? "[&>div]:bg-amber-500" : ""}`}
        />
      )}
      {isWarning && (
        <p className="text-xs text-amber-600">
          {pct >= 100
            ? capReachedText
            : capWarningTemplate.replace("{pct}", pct.toFixed(0))}
        </p>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Section A — Current Plan
// ---------------------------------------------------------------------------

function CurrentPlanSection({ data, t }: { data: any; t: (key: string) => string }) {
  if (!data) return null
  const features: string[] = data.features_enabled || []

  return (
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
        <StatusBadge status={data.status} t={t} />
      </div>

      {data.status === "trialing" && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2">
          <p className="text-xs text-amber-800">
            {t("trialNotice")}
          </p>
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
  )
}

// ---------------------------------------------------------------------------
// Section B — Usage
// ---------------------------------------------------------------------------

function UsageSection({ subscription, usage, t }: { subscription: any; usage: any; t: (key: string) => string }) {
  if (!subscription || !usage) return null

  const llm = subscription.llm || {}
  const pearch = subscription.pearch || {}
  const apify = subscription.apify || {}
  const quotas = subscription.agent_quotas || {}

  const capReached = t("capReached")
  const capWarning = t("capWarning")

  return (
    <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Gauge className="h-4 w-4 text-lia-text-muted" aria-hidden="true" />
        <p className="text-sm font-medium text-lia-text-primary">{t("usage")}</p>
      </div>

      <div className="space-y-3">
        <UsageBar
          label={t("embeddingTokens")}
          icon={Database}
          used={usage.embedding_tokens_used || 0}
          cap={llm.embedding_monthly_cap || 0}
          unit={t("tokens")}
          capReachedText={capReached}
          capWarningTemplate={capWarning}
        />

        {llm.byok_active ? (
          <div className="flex items-center gap-2 text-sm text-lia-text-secondary">
            <Zap className="h-3.5 w-3.5" aria-hidden="true" />
            <span>
              {t("byokActive")}
              {llm.byok_provider ? ` (${llm.byok_provider})` : ""}
            </span>
          </div>
        ) : (
          <UsageBar
            label={t("llmGeneralTokens")}
            icon={Zap}
            used={usage.llm_general_tokens_used || 0}
            cap={llm.general_monthly_cap || 0}
            unit={t("tokens")}
            capReachedText={capReached}
            capWarningTemplate={capWarning}
          />
        )}

        <UsageBar
          label={t("pearchCredits")}
          icon={Search}
          used={usage.pearch_credits_used || 0}
          cap={pearch.monthly_included_credits || 0}
          unit={t("credits")}
          capReachedText={capReached}
          capWarningTemplate={capWarning}
        />

        <UsageBar
          label={t("apifyCredits")}
          icon={Database}
          used={usage.apify_credits_used || 0}
          cap={apify.monthly_included_credits || 0}
          unit={t("credits")}
          capReachedText={capReached}
          capWarningTemplate={capWarning}
        />

        <UsageBar
          label={t("agentExecutions")}
          icon={Bot}
          used={usage.agent_executions_used || 0}
          cap={0}
          unit={t("executions")}
          capReachedText={capReached}
          capWarningTemplate={capWarning}
        />
      </div>

      <div className="pt-2 border-t border-lia-border-subtle">
        <p className="text-xs text-lia-text-tertiary">
          {t("agentsSummary")
            .replace("{custom}", String(quotas.custom_agents ?? 0))
            .replace("{sourcing}", String(quotas.sourcing_agents ?? 0))
            .replace("{twins}", String(quotas.digital_twins ?? 0))
            .replace("{campaigns}", String(quotas.campaigns ?? 0))}
        </p>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Section D — Invoices
// ---------------------------------------------------------------------------

function InvoicesSection({ data, t }: { data: any; t: (key: string) => string }) {
  const invoices = Array.isArray(data?.invoices) ? data.invoices : Array.isArray(data) ? data : []
  if (invoices.length === 0) {
    return (
      <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-5">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-lia-text-muted" aria-hidden="true" />
          <p className="text-sm font-medium text-lia-text-primary">{t("invoices")}</p>
        </div>
        <p className="text-xs text-lia-text-tertiary mt-2">
          {t("noInvoices")}
        </p>
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
            {invoices.slice(0, 6).map((inv: any, i: number) => (
              <tr key={inv.id || i} className="border-b border-lia-border-subtle last:border-0">
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
                  <InvoiceStatusChip status={inv.status} t={t} />
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

function InvoiceStatusChip({ status, t }: { status: string; t: (key: string) => string }) {
  const variants: Record<string, "success" | "warning" | "danger" | "neutral"> = {
    paid: "success",
    pending: "warning",
    overdue: "danger",
    failed: "danger",
  }
  const label = t(`invoiceStatuses.${status}`) || status || "-"
  const variant = variants[status] || "neutral"
  return <Chip variant={variant} muted className="text-[10px]">{label}</Chip>
}

// ---------------------------------------------------------------------------
// Section E — Payment Method
// ---------------------------------------------------------------------------

function PaymentMethodSection({ data, t }: { data: any; t: (key: string) => string }) {
  const methods = Array.isArray(data?.payment_methods)
    ? data.payment_methods
    : Array.isArray(data)
      ? data
      : []

  return (
    <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-5 space-y-3">
      <div className="flex items-center gap-2">
        <Wallet className="h-4 w-4 text-lia-text-muted" aria-hidden="true" />
        <p className="text-sm font-medium text-lia-text-primary">{t("paymentMethod")}</p>
      </div>

      {methods.length === 0 ? (
        <p className="text-xs text-lia-text-tertiary">
          {t("noPaymentMethod")}
        </p>
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
  )
}

// ---------------------------------------------------------------------------
// Main BillingTab
// ---------------------------------------------------------------------------

export function BillingTab() {
  const t = useTranslations("settings.billing")

  const subscription = useBillingSubscription(t("errors.loadPlan"))
  const usage = useBillingUsage(t("errors.loadUsage"))
  const invoices = useBillingInvoices(t("errors.loadInvoices"))
  const paymentMethods = useBillingPaymentMethods(t("errors.loadPaymentMethods"))

  const isLoading =
    subscription.isLoading || usage.isLoading || invoices.isLoading || paymentMethods.isLoading
  const error = subscription.error || usage.error

  if (isLoading) return <HubLoadingState />
  if (error) {
    return (
      <HubErrorState
        onRetry={() => {
          subscription.refetch()
          usage.refetch()
          invoices.refetch()
          paymentMethods.refetch()
        }}
      />
    )
  }

  return (
    <div className="space-y-4">
      <CurrentPlanSection data={subscription.data} t={t} />
      <UsageSection subscription={subscription.data} usage={usage.data} t={t} />
      <InvoicesSection data={invoices.data} t={t} />
      <PaymentMethodSection data={paymentMethods.data} t={t} />
    </div>
  )
}
