"use client"

import { useTranslations } from "next-intl"
import { Shield, BarChart3, FileSearch, Sliders, Activity } from "lucide-react"
import Link from "next/link"

/**
 * Landing page do `/wedo-admin/` — área provisória interna.
 *
 * Cards habilitados:
 * - fairness (PR 2 2026-05-25)
 *
 * Cards pendentes (PR 3):
 * - auditLogs, aiTransparency, policyEngine, automationRules
 *
 * Plan: ~/.claude/plans/jolly-roaming-moler.md (seção "PLANO DE EXECUÇÃO")
 */

interface SectionLink {
  id: string
  href: string
  iconKey: "fairness" | "audit" | "ai" | "policy" | "automation"
  available: boolean
}

const SECTIONS: SectionLink[] = [
  { id: "fairness", href: "/wedo-admin/fairness", iconKey: "fairness", available: true },
  { id: "auditLogs", href: "/wedo-admin/governanca/audit-logs", iconKey: "audit", available: false },
  { id: "aiTransparency", href: "/wedo-admin/governanca/ai-transparency", iconKey: "ai", available: false },
  { id: "policyEngine", href: "/wedo-admin/governanca/policy-engine", iconKey: "policy", available: false },
  { id: "automationRules", href: "/wedo-admin/governanca/automation-rules", iconKey: "automation", available: false },
]

const ICONS = {
  fairness: Shield,
  audit: FileSearch,
  ai: BarChart3,
  policy: Sliders,
  automation: Activity,
} as const

export default function WedoAdminLanding() {
  const t = useTranslations("wedo_admin.landing")

  return (
    <main className="min-h-screen bg-lia-bg-primary p-8">
      <div className="max-w-5xl mx-auto">
        <header className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-8 h-8 text-amber-500" />
            <h1 className="text-2xl font-semibold text-lia-text-primary">
              {t("title")}
            </h1>
          </div>
          <p className="text-lia-text-secondary text-sm max-w-2xl">
            {t("subtitle")}
          </p>
          <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-600 text-xs font-medium">
            <Shield className="w-3.5 h-3.5" />
            {t("provisional_badge")}
          </div>
        </header>

        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {SECTIONS.map((section) => {
            const Icon = ICONS[section.iconKey]
            const cardClass = section.available
              ? "border-lia-border-secondary hover:border-lia-accent-primary cursor-pointer"
              : "border-lia-border-secondary opacity-60 cursor-not-allowed"

            const Inner = (
              <div className={`p-6 rounded-xl border ${cardClass} transition-colors bg-lia-bg-secondary`}>
                <div className="flex items-center gap-3 mb-3">
                  <Icon className="w-5 h-5 text-lia-text-secondary" />
                  <h2 className="font-medium text-lia-text-primary">
                    {t(`sections.${section.id}.title`)}
                  </h2>
                </div>
                <p className="text-sm text-lia-text-secondary">
                  {t(`sections.${section.id}.description`)}
                </p>
                {!section.available && (
                  <p className="text-xs text-lia-text-tertiary mt-3 italic">
                    {t("coming_soon")}
                  </p>
                )}
              </div>
            )

            return section.available ? (
              <Link key={section.id} href={section.href}>
                {Inner}
              </Link>
            ) : (
              <div key={section.id}>{Inner}</div>
            )
          })}
        </section>
      </div>
    </main>
  )
}
