// Onda 4 F6.4 (2026-05-28) — badge "agente novo aprendendo".
//
// Quando is_learning=true (ou total_executions < 5), agente está em fase de
// estabilização. Badge cyan sutil pra comunicar isso sem ser ruidoso.
//
// Reuso: AgentCard, AgentDetailsPanel, página KPIs (já tem versão inline).
"use client"

import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"

interface LearningBadgeProps {
  className?: string
  /** Quando true, oculta o emoji e mostra apenas texto (para casos densos). */
  iconOnly?: boolean
}

export function LearningBadge({ className, iconOnly }: LearningBadgeProps) {
  const t = useTranslations("agents.studio.kpis.learning")
  return (
    <span
      role="status"
      title={t("tooltip")}
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs",
        "border-lia-border-medium bg-lia-bg-tertiary text-lia-text-primary",
        className,
      )}
      data-testid="learning-badge"
    >
      <span aria-hidden="true">🩵</span>
      {!iconOnly && <span>{t("badge").replace("🩵 ", "")}</span>}
      <span className="sr-only">— {t("tooltip")}</span>
    </span>
  )
}
