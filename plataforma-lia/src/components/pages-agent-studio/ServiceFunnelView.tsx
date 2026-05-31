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
  onCustomAgents?: () => void
  onMarketplace?: () => void
  /** Open marketplace pre-filtered by funnel stage */
  onMarketplaceForSlug?: (slug: ServiceSlug) => void
}

// ── Status dot ─────────────────────────────────────────────────────────────

const STATUS_DOT: Record<ServiceStatus, string> = {
  active:     "bg-[#5DA47A]",              // forest-green
  configured: "bg-[#60BED1]",              // lia-cyan
  attention:  "bg-[#D19960]",              // amber-warning
  inactive:   "bg-[#D1D5DB]",              // pebble — not yet set up
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
            "absolute inset-0 rounded-full opacity-40 animate-ping",
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
  active:     "text-[#5DA47A]",
  configured: "text-[#4B5563]",          // slate
  attention:  "text-[#D19960]",
  inactive:   "text-[#9CA3AF]",          // fog
}

// ── Single service row ─────────────────────────────────────────────────────

interface ServiceRowProps {
  data: FunnelServiceData
  index: number
  isLast: boolean
  isExpanded: boolean
  onToggle: () => void
  onActivate: () => void
  onMarketplaceForSlug?: () => void
}

function ServiceRow({ data, index, isLast, isExpanded, onToggle, onActivate, onMarketplaceForSlug }: ServiceRowProps) {
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
    <div className={cn("group", !isLast && "border-b border-[#E5E7EB]")}>
      {/* ── Main row ── */}
      <div
        role={hasPanel || isInactive ? "button" : undefined}
        tabIndex={hasPanel || isInactive ? 0 : undefined}
        onKeyDown={e => (e.key === "Enter" || e.key === " ") && handleRowClick()}
        onClick={handleRowClick}
        className={cn(
          "flex items-center gap-3 px-4 py-3 transition-colors",
          (hasPanel || isInactive) && "cursor-pointer",
          isExpanded
            ? "bg-[#F9FAFB]"
            : (hasPanel || isInactive)
              ? "hover:bg-[#F9FAFB]"
              : "bg-white",
        )}
        aria-expanded={hasPanel ? isExpanded : undefined}
      >
        {/* Step number */}
        <span
          className={cn(
            "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-semibold flex-shrink-0 tabular-nums",
            isInactive
              ? "bg-[#F3F4F6] text-[#9CA3AF]"
              : "bg-[#EBF8FB] text-[#60BED1]",
          )}
        >
          {index + 1}
        </span>

        {/* Status dot */}
        <ServiceStatusDot status={data.status} />

        {/* Service name */}
        <span
          className={cn(
            "flex-1 text-sm font-medium",
            isInactive ? "text-[#6B7280]" : "text-[#030712]"
          )}
        >
          {t(labelKey)}
        </span>

        {/* Metric */}
        {data.metric && (
          <span className="text-xs tabular-nums font-mono text-[#4B5563] mr-2 hidden sm:block">
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
              className="hidden group-hover:flex items-center gap-1 text-[10px] font-medium text-[#9CA3AF] hover:text-[#60BED1] border border-[#E5E7EB] hover:border-[#60BED1]/40 rounded px-1.5 py-0.5 transition-colors"
              aria-label={t("studio.services.advanced")}
            >
              <Plus className="w-2.5 h-2.5" />
              {t("studio.services.advanced")}
            </button>
          )}
          {isInactive ? (
            <span className="flex items-center gap-1 text-xs font-medium text-[#60BED1] opacity-0 group-hover:opacity-100 transition-opacity">
              <Plus className="w-3 h-3" />
              {t("studio.services.ctaActivate")}
            </span>
          ) : hasPanel ? (
            isExpanded
              ? <ChevronDown className="w-4 h-4 text-[#9CA3AF]" />
              : <ChevronRight className="w-4 h-4 text-[#9CA3AF] opacity-0 group-hover:opacity-100 transition-opacity" />
          ) : (
            <ChevronRight className="w-4 h-4 text-[#9CA3AF] opacity-0 group-hover:opacity-100 transition-opacity" />
          )}
        </div>
      </div>

      {/* ── Expanded panel ── */}
      {hasPanel && isExpanded && (
        <div className="border-t border-[#E5E7EB] bg-[#F9FAFB]">
          {data.panel}
        </div>
      )}
    </div>
  )
}

// ── Advanced tools footer ──────────────────────────────────────────────────

interface AdvancedToolsFooterProps {
  onCustomAgents: () => void
  onMarketplace: () => void
}

function AdvancedToolsFooter({ onCustomAgents, onMarketplace }: AdvancedToolsFooterProps) {
  const t = useTranslations("agents")
  return (
    <div className="flex items-center gap-4 px-4 py-3 border-t border-[#E5E7EB] bg-[#F9FAFB]">
      <span className="text-[10px] font-semibold uppercase tracking-widest text-[#9CA3AF] mr-1">
        {t("studio.services.advanced")}
      </span>
      <button
        onClick={onCustomAgents}
        className="text-xs text-[#4B5563] hover:text-[#030712] transition-colors font-medium"
      >
        {t("studio.tabs.customAgents")}
      </button>
      <span className="text-[#D1D5DB]">·</span>
      <button
        onClick={onMarketplace}
        className="text-xs text-[#4B5563] hover:text-[#030712] transition-colors font-medium"
      >
        {t("studio.tabs.marketplace")}
      </button>
    </div>
  )
}

// ── Main view ──────────────────────────────────────────────────────────────

export function ServiceFunnelView({
  services,
  defaultExpanded = null,
  onActivate,
  onCustomAgents,
  onMarketplace,
  onMarketplaceForSlug,
}: ServiceFunnelViewProps) {
  const [expanded, setExpanded] = useState<ServiceSlug | null>(
    // auto-expand first non-inactive service that has a panel
    defaultExpanded ??
    (services.find(s => s.status !== "inactive" && s.panel)?.slug ?? null)
  )

  const handleToggle = (slug: ServiceSlug) => {
    setExpanded(prev => (prev === slug ? null : slug))
  }

  // Split into funnel services vs advanced (custom, marketplace are passed separately)
  const funnelServices = services.filter(
    s => !["custom", "marketplace"].includes(s.slug)
  )

  return (
    <div className="rounded-xl border border-[#E5E7EB] bg-white overflow-hidden">
      {/* Section header */}
      <div className="px-4 py-2.5 border-b border-[#E5E7EB] bg-[#F9FAFB]">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-[#9CA3AF]">
          Serviços do Funil
        </span>
      </div>

      {/* Service rows */}
      {funnelServices.map((svc, i) => (
        <ServiceRow
          key={svc.slug}
          data={svc}
          index={i}
          isLast={i === funnelServices.length - 1 && !onCustomAgents && !onMarketplace}
          isExpanded={expanded === svc.slug}
          onToggle={() => handleToggle(svc.slug)}
          onActivate={() => onActivate?.(svc.slug)}
          onMarketplaceForSlug={onMarketplaceForSlug ? () => onMarketplaceForSlug(svc.slug) : undefined}
        />
      ))}

      {/* Advanced tools footer — only rendered when callbacks are provided */}
      {(onCustomAgents || onMarketplace) && (
        <AdvancedToolsFooter
          onCustomAgents={onCustomAgents ?? (() => {})}
          onMarketplace={onMarketplace ?? (() => {})}
        />
      )}
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
    <div className="rounded-xl border border-[#60BED1]/30 bg-[#EBF8FB]/40 p-5 mb-4">
      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-3">
        {[1, 2, 3].map(n => (
          <div key={n} className={cn(
            "h-1 rounded-full transition-all",
            n <= step ? "bg-[#60BED1] w-8" : "bg-[#D1D5DB] w-4"
          )} />
        ))}
        <span className="text-[10px] text-[#9CA3AF] ml-1">
          {step}/3
        </span>
      </div>

      {step === 1 && (
        <div>
          <p className="text-sm font-medium text-[#030712] mb-1">
            {t("studio.onboarding.step1Title")}
          </p>
          <p className="text-xs text-[#6B7280] mb-3">
            {t("studio.onboarding.step1Desc", { count: openJobCount })}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setStep(2)}
              className="text-xs font-medium px-3 py-1.5 rounded-md bg-[#030712] text-white hover:bg-[#1F2937] transition-colors"
            >
              {t("studio.onboarding.continue")}
            </button>
            <button onClick={onDismiss} className="text-xs text-[#9CA3AF] hover:text-[#6B7280] transition-colors px-2">
              {t("studio.onboarding.skip")}
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div>
          <p className="text-sm font-medium text-[#030712] mb-1">
            {t("studio.onboarding.step2Title")}
          </p>
          <p className="text-xs text-[#6B7280] mb-3">
            {t("studio.onboarding.step2Desc")}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => { onActivateSourcing(); setStep(3) }}
              className="text-xs font-medium px-3 py-1.5 rounded-md bg-[#030712] text-white hover:bg-[#1F2937] transition-colors"
            >
              {t("studio.onboarding.activateSourcing")}
            </button>
            <button onClick={() => setStep(3)} className="text-xs text-[#9CA3AF] hover:text-[#6B7280] transition-colors px-2">
              {t("studio.onboarding.notNow")}
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div>
          <p className="text-sm font-medium text-[#030712] mb-1">
            {t("studio.onboarding.step3Title")}
          </p>
          <p className="text-xs text-[#6B7280] mb-3">
            {t("studio.onboarding.step3Desc")}
          </p>
          <button
            onClick={onDismiss}
            className="text-xs font-medium px-3 py-1.5 rounded-md bg-[#030712] text-white hover:bg-[#1F2937] transition-colors"
          >
            {t("studio.onboarding.done")}
          </button>
        </div>
      )}
    </div>
  )
}
