"use client"

import React, { useState } from "react"
import { useTranslations } from "next-intl"
import { ScrollText, ShieldAlert, Workflow, FileCheck2, UserCog, ShieldCheck, Activity } from "lucide-react"
import { tabStyles, textStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import { AuditLogsPanel } from "./AuditLogsPanel"
import { BiasAuditPanel } from "./BiasAuditPanel"
import { AutomationRulesPanel } from "./AutomationRulesPanel"
import { PolicyEnginePanel } from "./PolicyEnginePanel"
import { DSRInboxPanel } from "./DSRInboxPanel"
import { ConsentPanel } from "./ConsentPanel"
import { AIPerformancePanel } from "./AIPerformancePanel"

export type GovernancaSubsection =
  | "audit-logs"
  | "bias-audit"
  | "automation-rules"
  | "policy-engine"
  | "dsr"
  | "consent"
  | "ai-performance"

interface GovernancaHubProps {
  activeSubsection?: GovernancaSubsection
}

export function GovernancaHub({ activeSubsection }: GovernancaHubProps) {
  const t = useTranslations("settings.governanca")
  const [active, setActive] = useState<GovernancaSubsection>(
    activeSubsection ?? "audit-logs",
  )

  const tabs: Array<{ id: GovernancaSubsection; label: string; icon: React.ElementType }> = [
    { id: "audit-logs", label: t("tabs.auditLogs"), icon: ScrollText },
    { id: "bias-audit", label: t("tabs.biasAudit"), icon: ShieldAlert },
    { id: "automation-rules", label: t("tabs.automationRules"), icon: Workflow },
    { id: "policy-engine", label: t("tabs.policyEngine"), icon: FileCheck2 },
    { id: "dsr", label: t("tabs.dsr"), icon: UserCog },
    { id: "consent", label: t("tabs.consent"), icon: ShieldCheck },
    { id: "ai-performance", label: t("tabs.aiPerformance"), icon: Activity },
  ]

  return (
    <div className="space-y-6" data-testid="governanca-hub">
      <header className="space-y-1">
        <h1 className={textStyles.h1}>{t("title")}</h1>
        <p className={textStyles.description}>{t("description")}</p>
      </header>

      <nav
        className={cn(tabStyles.pillContainer, "flex-wrap")}
        role="tablist"
        aria-label={t("title")}
      >
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = active === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`governanca-panel-${tab.id}`}
              data-testid={`governanca-tab-${tab.id}`}
              className={isActive ? tabStyles.pillActive : tabStyles.pill}
              onClick={() => setActive(tab.id)}
            >
              <Icon className={tabStyles.pillIcon} aria-hidden="true" />
              {tab.label}
            </button>
          )
        })}
      </nav>

      <section
        id={`governanca-panel-${active}`}
        role="tabpanel"
        aria-labelledby={`governanca-tab-${active}`}
        data-testid={`governanca-panel-${active}`}
      >
        {active === "audit-logs" && <AuditLogsPanel />}
        {active === "bias-audit" && <BiasAuditPanel />}
        {active === "automation-rules" && <AutomationRulesPanel />}
        {active === "policy-engine" && <PolicyEnginePanel />}
        {active === "dsr" && <DSRInboxPanel />}
        {active === "consent" && <ConsentPanel />}
        {active === "ai-performance" && <AIPerformancePanel />}
      </section>
    </div>
  )
}

export default GovernancaHub
