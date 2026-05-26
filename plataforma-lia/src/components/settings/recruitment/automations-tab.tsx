"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { SETTINGS_QUERY_KEYS } from "@/hooks/settings/useSettingsBroadcast"
import { HubHeader, HubLoadingState, HubErrorState } from "@/components/settings/_shared"
import { Chip } from "@/components/ui/chip"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { hasModuleAccess } from "@/utils/license-manager"
import { ModuleUpsell } from "@/components/module-access/module-upsell"
import { apiFetch } from "@/lib/api/api-fetch"
import { Edit, Plus, Workflow, FileText, Zap, Download, BarChart3, Activity, MoreHorizontal, Sparkles } from "lucide-react"

interface ApiAutomation {
  id: string
  name: string
  description?: string | null
  trigger_type: string
  action_type: string
  is_active: boolean
  executions_count?: number | null
  last_executed_at?: string | null
  success_rate?: number | null
}

interface WorkflowItem {
  id: string
  name: string
  description: string
  status: "active" | "paused"
  triggerType: string
  lastRun: string | null
  executions: number
  successRate: number
}

function mapAutomation(a: ApiAutomation): WorkflowItem {
  return {
    id: String(a.id),
    name: a.name,
    description: a.description ?? "",
    status: a.is_active ? "active" : "paused",
    triggerType: a.trigger_type,
    lastRun: a.last_executed_at ?? null,
    executions: a.executions_count ?? 0,
    successRate: a.success_rate ?? 100,
  }
}

type ViewTab = "overview" | "builder" | "templates" | "logs"

export function AutomationsTab({ onSettingsChange: _onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const t = useTranslations("settings.recruitment.automationsTab")
  const [selectedView, setSelectedView] = useState<ViewTab>("overview")
  const { companyId } = useCompanyId()

  const {
    data: workflows = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.automations(companyId ?? ""),
    queryFn: async () => {
      // company_id NUNCA via query — backend extrai do JWT (REGRA 2 CLAUDE.md user-global)
      const res = await apiFetch(`/api/backend-proxy/automations`)
      const json = await res.json()
      if (json?.success && Array.isArray(json?.data?.automations)) {
        return json.data.automations.map(mapAutomation) as WorkflowItem[]
      }
      return [] as WorkflowItem[]
    },
    enabled: !!companyId,
    staleTime: 30_000,
  })

  const labelForTrigger = (triggerType: string): string => {
    const key = `trigger_${triggerType}` as Parameters<typeof t>[0]
    try {
      const label = t(key)
      if (label && label !== key) return label
    } catch { /* missing key */ }
    return triggerType
  }

  if (!hasModuleAccess("workflow_automation")) {
    return (
      <ModuleUpsell
        moduleId="workflow_automation"
        title={t("upsellTitle")}
        description={t("upsellDesc")}
      />
    )
  }

  if (isLoading) return <HubLoadingState />
  if (error) return <HubErrorState message={t("loadError")} onRetry={refetch} />

  const activeCount = workflows.filter((w) => w.status === "active").length
  const totalExecs = workflows.reduce((sum, w) => sum + w.executions, 0)
  const avgSuccess = workflows.length > 0
    ? Math.round(workflows.reduce((s, w) => s + w.successRate, 0) / workflows.length)
    : null

  const summaryParts = [
    t("summaryActive", { active: activeCount, total: workflows.length }),
    t("summaryExecs", { count: totalExecs }),
    ...(avgSuccess !== null ? [t("summarySuccess", { pct: avgSuccess })] : []),
  ]

  const TAB_ITEMS: { id: ViewTab; label: string; icon: React.ElementType }[] = [
    { id: "overview", label: t("tabOverview"), icon: BarChart3 },
    { id: "builder", label: t("tabBuilder"), icon: Workflow },
    { id: "templates", label: t("tabTemplates"), icon: FileText },
    { id: "logs", label: t("tabLogs"), icon: Activity },
  ]

  return (
    <div className="space-y-5">
      <HubHeader
        title={t("pageTitle")}
        description={t("pageSubtitle")}
      >
        <Button variant="outline" size="sm" className="gap-2">
          <Download className="w-4 h-4" />
          {t("export")}
        </Button>
        <Button size="sm" className="gap-2">
          <Plus className="w-4 h-4" />
          {t("newWorkflow")}
        </Button>
      </HubHeader>

      <div className="flex space-x-1 bg-lia-bg-tertiary p-1 rounded-xl w-fit">
        {TAB_ITEMS.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setSelectedView(tab.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors motion-reduce:transition-none ${
                selectedView === tab.id
                  ? "bg-lia-bg-primary text-lia-text-primary shadow-sm"
                  : "text-lia-text-secondary hover:text-lia-text-primary"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {selectedView === "overview" && (
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-0">
              <div className="flex items-center justify-between">
                <CardTitle>{t("configuredWorkflows")}</CardTitle>
                {workflows.length > 0 && (
                  <p className="text-xs text-lia-text-secondary">
                    {summaryParts.join("  ·  ")}
                  </p>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              {workflows.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-center">
                  <Sparkles className="w-9 h-9 text-wedo-cyan mb-3" />
                  <p className="text-sm font-medium text-lia-text-primary mb-1">{t("emptyTitle")}</p>
                  <p className="text-xs text-lia-text-secondary mb-4 max-w-md italic">{t("emptyExample")}</p>
                  <div className="flex items-center gap-2">
                    <Button size="sm" className="gap-2">
                      <Sparkles className="w-4 h-4" />
                      {t("createWithLia")}
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setSelectedView("templates")}>
                      {t("seeExamples")}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="divide-y divide-lia-border-subtle">
                  {workflows.map((workflow) => (
                    <div key={workflow.id} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className={`w-8 h-8 rounded-md flex items-center justify-center shrink-0 ${
                          workflow.status === "active" ? "bg-wedo-cyan/10" : "bg-lia-bg-tertiary"
                        }`}>
                          <Sparkles className={`w-4 h-4 ${
                            workflow.status === "active" ? "text-wedo-cyan" : "text-lia-text-tertiary"
                          }`} />
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-lia-text-primary truncate">{workflow.name}</p>
                          <p className="text-xs text-lia-text-secondary mt-0.5">
                            {t("trigger", { value: labelForTrigger(workflow.triggerType) })}
                            {workflow.executions > 0 && (
                              <span className="ml-2">· {t("executions", { count: workflow.executions })}</span>
                            )}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0 ml-4">
                        <Chip variant={workflow.status === "active" ? "success" : "neutral"} muted={workflow.status !== "active"}>
                          {workflow.status === "active" ? t("statusActive") : t("statusPaused")}
                        </Chip>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <Edit className="w-3.5 h-3.5" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <MoreHorizontal className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

        </div>
      )}

      {selectedView === "builder" && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Workflow className="w-10 h-10 text-lia-text-tertiary mb-3" />
          <p className="text-sm font-medium text-lia-text-primary mb-1">{t("builderTitle")}</p>
          <p className="text-xs text-lia-text-secondary max-w-xs">{t("builderDesc")}</p>
        </div>
      )}

      {selectedView === "templates" && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <FileText className="w-10 h-10 text-lia-text-tertiary mb-3" />
          <p className="text-sm font-medium text-lia-text-primary mb-1">{t("templateLibrary")}</p>
          <p className="text-xs text-lia-text-secondary max-w-xs">{t("templateLibraryDesc")}</p>
        </div>
      )}

      {selectedView === "logs" && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Activity className="w-10 h-10 text-lia-text-tertiary mb-3" />
          <p className="text-sm font-medium text-lia-text-primary mb-1">{t("executionLogs")}</p>
          <p className="text-xs text-lia-text-secondary max-w-xs">{t("executionLogsDesc")}</p>
        </div>
      )}
    </div>
  )
}
