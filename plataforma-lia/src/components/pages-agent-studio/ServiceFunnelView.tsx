"use client"

import React, { useState } from "react"
import { ChevronDown, ChevronRight, Plus } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"

// ── Types ──────────────────────────────────────────────────────────────────

export type ServiceSlug =
  | "intake"
  | "alignment"
  | "sourcing"
  | "screening"
  | "calibration"
  | "offer"
  | "nps"

export type ServiceStatus = "active" | "configured" | "attention" | "inactive"

export interface FunnelServiceData {
  slug: ServiceSlug
  status: ServiceStatus
  /** Short human-readable metric: "2 ativos", "84% acurácia" */
  metric?: string
  /** Render the expanded panel for this service */
  panel?: React.ReactNode
  /** Override the default CTA label (e.g. "Gerenciar" vs "Ativar") */
  ctaKey?: string
}

interface ServiceFunnelViewProps {
  services: FunnelServiceData[]
  defaultExpanded?: ServiceSlug | null
  onActivate?: (slug: ServiceSlug) => void
  /** Open marketplace pre-filtered by funnel stage */
  onMarketplaceForSlug?: (slug: ServiceSlug) => void
}

// ── Funnel phases ────────────────────────────────────────────────────────────
// Agrupa as 7 etapas em 4 fases do funil de recrutamento → dá estrutura visual
// em vez de uma lista plana de 7 linhas iguais.
const PHASE_GROUPS: { key: string; slugs: ServiceSlug[] }[] = [
  { key: "opening", slugs: ["intake", "alignment"] },
  { key: "attraction", slugs: ["sourcing", "screening"] },
  { key: "decision", slugs: ["calibration", "offer"] },
  { key: "post", slugs: ["nps"] },
]
const ORDERED_SLUGS: ServiceSlug[] = PHASE_GROUPS.flatMap(g => g.slugs)

// ── Status dot ─────────────────────────────────────────────────────────────
// White-label canonical (commit 7b350ed2a): cyan é exclusiva da LIA quando ELA
// age. Status de serviço do CLIENTE usa verde/laranja semânticos + neutros DS.

const STATUS_DOT: Record<ServiceStatus, string> = {
  active:     "bg-wedo-green",            // semantic success
  configured: "bg-lia-text-tertiary",     // neutral — set up, idle (no cyan)
  attention:  "bg-wedo-orange",           // semantic warning
  inactive:   "bg-lia-border-default",    // faint — not yet set up
}

const STATUS_PULSE: Record<ServiceStatus, boolean> = {
  active:     true,
  configured: false,
  attention:  true,
  inactive:   false,
}

function ServiceStatusDot({ status }: { status: ServiceStatus }) {
  return (
    <span className="relative flex items-center justify-center w-4 h-4 flex-shrink-0">
      <span className={cn("w-2 h-2 rounded-full", STATUS_DOT[status])} />
      {STATUS_PULSE[status] && (
        <span
          className={cn(
            "absolute inset-0 rounded-full opacity-40 animate-ping motion-reduce:animate-none",
            STATUS_DOT[status]
          )}
        />
      )}
    </span>
  )
}

// ── Status label (translated) ───────────────────────────────────────────────

const STATUS_LABEL_KEY: Record<ServiceStatus, string> = {
  active:     "studio.services.statusActive",
  configured: "studio.services.statusConfigured",
  attention:  "studio.services.statusAttention",
  inactive:   "studio.services.statusInactive",
}

const STATUS_TEXT_COLOR: Record<ServiceStatus, string> = {
  active:     "text-lia-text-secondary",
  configured: "text-lia-text-secondary",
  attention:  "text-wedo-orange-text",
  inactive:   "text-lia-text-tertiary",
}

// ── Single service row ─────────────────────────────────────────────────────

interface ServiceRowProps {
  data: FunnelServiceData
  stepNumber: number
  isLast: boolean
  isExpanded: boolean
  onToggle: () => void
  onActivate: () => void
  onMarketplaceForSlug?: () => void
}

function ServiceRow({ data, stepNumber, isLast, isExpanded, onToggle, onActivate, onMarketplaceForSlug }: ServiceRowProps) {
  const t = useTranslations("agents")
  const isInactive = data.status === "inactive"
  const hasPanel = Boolean(data.panel)
  const labelKey = `studio.services.${data.slug}` as const

  const handleRowClick = () => {
    // Painel sempre expande (mesmo inativo) — revela o card com as ações reais
    // (solicitar alinhamento, enviar oferta/NPS, criar agente/twin). Só serviços
    // SEM painel (ex: screening) caem no onActivate.
    if (hasPanel) { onToggle(); return }
    if (isInactive) onActivate()
  }

  return (
    <div className={cn("group", !isLast && "border-b border-lia-border-subtle")}>
      {/* ── Main row ── */}
      <div
        role={hasPanel || isInactive ? "button" : undefined}
        tabIndex={hasPanel || isInactive ? 0 : undefined}
        onKeyDown={e => (e.key === "Enter" || e.key === " ") && handleRowClick()}
        onClick={handleRowClick}
        className={cn(
          "flex items-center gap-3 px-4 py-3 transition-colors",
          (hasPanel || isInactive) && "cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-lia-border-medium",
          isExpanded
            ? "bg-lia-bg-secondary"
            : (hasPanel || isInactive)
              ? "hover:bg-lia-bg-secondary"
              : "bg-lia-bg-elevated",
        )}
        aria-expanded={hasPanel ? isExpanded : undefined}
      >
        {/* Step number */}
        <span
          className={cn(
            "w-5 h-5 rounded-full flex items-center justify-center text-micro font-semibold flex-shrink-0 tabular-nums",
            isInactive
              ? "bg-lia-bg-tertiary text-lia-text-tertiary"
              : "bg-lia-bg-tertiary text-lia-text-primary",
          )}
        >
          {stepNumber}
        </span>

        {/* Status dot */}
        <ServiceStatusDot status={data.status} />

        {/* Service name */}
        <span
          className={cn(
            "flex-1 text-sm font-medium",
            isInactive ? "text-lia-text-tertiary" : "text-lia-text-primary"
          )}
        >
          {t(labelKey)}
        </span>

        {/* Metric */}
        {data.metric && (
          <span className="text-xs tabular-nums font-mono text-lia-text-secondary mr-2 hidden sm:block">
            {data.metric}
          </span>
        )}

        {/* Status label */}
        <span className={cn("text-xs font-medium hidden md:block", STATUS_TEXT_COLOR[data.status])}>
          {t(STATUS_LABEL_KEY[data.status])}
        </span>

        {/* CTA / chevron */}
        <div className="flex items-center gap-2 ml-2">
          {/* Contextual marketplace button for active/configured rows */}
          {!isInactive && onMarketplaceForSlug && (
            <button
              type="button"
              onClick={e => { e.stopPropagation(); onMarketplaceForSlug() }}
              className="hidden group-hover:flex items-center gap-1 text-micro font-medium text-lia-text-tertiary hover:text-lia-text-primary border border-lia-border-subtle hover:border-lia-border-medium rounded px-1.5 py-0.5 transition-colors"
              aria-label={t("studio.services.advanced")}
            >
              <Plus className="w-2.5 h-2.5" />
              {t("studio.services.advanced")}
            </button>
          )}
          {isInactive ? (
            // CTA sempre visível (não escondido em opacity-0) — discoverabilidade.
            <span className="flex items-center gap-1 text-xs font-medium text-lia-text-tertiary group-hover:text-lia-text-primary transition-colors">
              <Plus className="w-3 h-3" />
              {t(data.ctaKey ?? "studio.services.ctaActivate")}
            </span>
          ) : hasPanel ? (
            isExpanded
              ? <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />
              : <ChevronRight className="w-4 h-4 text-lia-text-tertiary opacity-0 group-hover:opacity-100 transition-opacity" />
          ) : (
            <ChevronRight className="w-4 h-4 text-lia-text-tertiary opacity-0 group-hover:opacity-100 transition-opacity" />
          )}
        </div>
      </div>

      {/* ── Expanded panel ── */}
      {hasPanel && isExpanded && (
        <div className="border-t border-lia-border-subtle bg-lia-bg-secondary">
          {data.panel}
        </div>
      )}
    </div>
  )
}

// ── Main view ──────────────────────────────────────────────────────────────

export function ServiceFunnelView({
  services,
  defaultExpanded = null,
  onActivate,
  onMarketplaceForSlug,
}: ServiceFunnelViewProps) {
  const t = useTranslations("agents")
  const [expanded, setExpanded] = useState<ServiceSlug | null>(
    // auto-expand first non-inactive service that has a panel
    defaultExpanded ??
    (services.find(s => s.status !== "inactive" && s.panel)?.slug ?? null)
  )

  const handleToggle = (slug: ServiceSlug) => {
    setExpanded(prev => (prev === slug ? null : slug))
  }

  const bySlug = new Map(services.map(s => [s.slug, s]))
  // Last existing slug overall — used to suppress the trailing row border.
  const lastSlug = [...ORDERED_SLUGS].reverse().find(s => bySlug.has(s))

  return (
    <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-elevated overflow-hidden">
      {/* Section header */}
      <div className="px-4 py-2.5 border-b border-lia-border-subtle bg-lia-bg-secondary">
        <span className="text-micro font-semibold uppercase tracking-widest text-lia-text-tertiary">
          {t("studio.services.funnelHeader")}
        </span>
      </div>

      {/* Phase groups */}
      {PHASE_GROUPS.map(group => {
        const groupServices = group.slugs
          .map(slug => bySlug.get(slug))
          .filter((s): s is FunnelServiceData => Boolean(s))
        if (groupServices.length === 0) return null
        return (
          <div key={group.key}>
            <div className="px-4 pt-3 pb-1 bg-lia-bg-elevated">
              <span className="text-micro font-semibold uppercase tracking-wider text-lia-text-tertiary">
                {t(`studio.services.phase.${group.key}`)}
              </span>
            </div>
            {groupServices.map(svc => (
              <ServiceRow
                key={svc.slug}
                data={svc}
                stepNumber={ORDERED_SLUGS.indexOf(svc.slug) + 1}
                isLast={svc.slug === lastSlug}
                isExpanded={expanded === svc.slug}
                onToggle={() => handleToggle(svc.slug)}
                onActivate={() => onActivate?.(svc.slug)}
                onMarketplaceForSlug={onMarketplaceForSlug ? () => onMarketplaceForSlug(svc.slug) : undefined}
              />
            ))}
          </div>
        )
      })}
    </div>
  )
}

// ── Onboarding overlay (first-visit, inline, no modal) ─────────────────────

interface StudioOnboardingProps {
  openJobCount: number
  onActivateSourcing: () => void
  onDismiss: () => void
}

export function StudioOnboarding({ openJobCount, onActivateSourcing, onDismiss }: StudioOnboardingProps) {
  const t = useTranslations("agents")
  const [step, setStep] = useState(1)

  return (
    <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-secondary px-4 py-3 mb-4">
      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-2">
        {[1, 2, 3].map(n => (
          <div key={n} className={cn(
            "h-1 rounded-full transition-all",
            n <= step ? "bg-lia-text-primary w-8" : "bg-lia-border-default w-4"
          )} />
        ))}
        <span className="text-micro text-lia-text-tertiary ml-1">
          {step}/3
        </span>
      </div>

      {step === 1 && (
        <div>
          <p className="text-sm font-medium text-lia-text-primary mb-1">
            {t("studio.onboarding.step1Title")}
          </p>
          <p className="text-xs text-lia-text-tertiary mb-3">
            {t("studio.onboarding.step1Desc", { count: openJobCount })}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setStep(2)}
              className="text-xs font-medium px-3 py-1.5 rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover transition-colors"
            >
              {t("studio.onboarding.continue")}
            </button>
            <button onClick={onDismiss} className="text-xs text-lia-text-tertiary hover:text-lia-text-secondary transition-colors px-2">
              {t("studio.onboarding.skip")}
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div>
          <p className="text-sm font-medium text-lia-text-primary mb-1">
            {t("studio.onboarding.step2Title")}
          </p>
          <p className="text-xs text-lia-text-tertiary mb-3">
            {t("studio.onboarding.step2Desc")}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => { onActivateSourcing(); setStep(3) }}
              className="text-xs font-medium px-3 py-1.5 rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover transition-colors"
            >
              {t("studio.onboarding.activateSourcing")}
            </button>
            <button onClick={() => setStep(3)} className="text-xs text-lia-text-tertiary hover:text-lia-text-secondary transition-colors px-2">
              {t("studio.onboarding.notNow")}
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div>
          <p className="text-sm font-medium text-lia-text-primary mb-1">
            {t("studio.onboarding.step3Title")}
          </p>
          <p className="text-xs text-lia-text-tertiary mb-3">
            {t("studio.onboarding.step3Desc")}
          </p>
          <button
            onClick={onDismiss}
            className="text-xs font-medium px-3 py-1.5 rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover transition-colors"
          >
            {t("studio.onboarding.done")}
          </button>
        </div>
      )}
    </div>
  )
}
