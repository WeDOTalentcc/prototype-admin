"use client"

import { useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { Chip } from "@/components/ui/chip"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { hasModuleAccess } from "@/utils/license-manager"
import { ModuleUpsell } from "@/components/module-access/module-upsell"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import {
  Edit, Plus, Workflow, FileText, Zap, Target,
  Download, BarChart3, Activity, MoreHorizontal, AlertCircle,
} from "lucide-react"
import { apiFetch } from "@/lib/api/api-fetch"

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

export function AutomationsTab({ onSettingsChange: _onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const t = useTranslations("settings.recruitment.automationsTab")
  const [selectedView, setSelectedView] = useState<"overview" | "builder" | "templates" | "logs">("overview")
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { companyId } = useCompanyId()

  useEffect(() => {
    if (!companyId) return
    setIsLoading(true)
    setError(null)
    apiFetch(`/api/backend-proxy/automations?company_id=${encodeURIComponent(companyId)}`)
      .then((res) => res.json())
      .then((json) => {
        if (json?.success && Array.isArray(json?.data?.automations)) {
          setWorkflows(json.data.automations.map(mapAutomation))
        } else {
          setWorkflows([])
        }
      })
      .catch((err) => {
        console.error("[AutomationsTab] Could not load automations:", err)
        setError(t("loadError"))
      })
      .finally(() => setIsLoading(false))
  }, [companyId, t])

  const labelForTrigger = (triggerType: string): string => {
    const key = `trigger_${triggerType}`
    try {
      const label = t(key as never)
      if (label && label !== key) return label
    } catch {
      // missing key — fall through
    }
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

  const renderOverview = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-16">
          <div className="w-6 h-6 rounded-full border-2 border-lia-text-secondary border-t-transparent animate-spin" />
          <span className="ml-3 text-sm text-lia-text-primary">{t("loading")}</span>
        </div>
      )
    }

    if (error) {
      return (
        <Card>
          <CardContent className="flex items-center gap-3 p-6 text-status-error">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span className="text-sm">{error}</span>
          </CardContent>
        </Card>
      )
    }

    const activeCount = workflows.filter((w) => w.status === "active").length

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-lia-text-primary">{t("activeWorkflows")}</p>
                  <p className="text-2xl font-semibold text-status-success">{activeCount}</p>
                  <p className="text-xs text-lia-text-primary">{t("ofTotalSimple", { total: workflows.length })}</p>
                </div>
                <div className="w-10 h-10 bg-status-success/15 rounded-md flex items-center justify-center">
                  <Workflow className="w-5 h-5 text-status-success" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-lia-text-primary">{t("executionsToday")}</p>
                  <p className="text-2xl font-semibold text-lia-text-primary">
                    {workflows.reduce((sum, w) => sum + w.executions, 0)}
                  </p>
                  <p className="text-xs text-lia-text-primary">{t("totalAccumulated")}</p>
                </div>
                <div className="w-10 h-10 bg-wedo-cyan/15 rounded-md flex items-center justify-center">
                  <Zap className="w-5 h-5 text-lia-text-secondary" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-lia-text-primary">{t("successRate")}</p>
                  <p className="text-2xl font-semibold text-wedo-orange">
                    {workflows.length > 0
                      ? `${Math.round(workflows.reduce((s, w) => s + w.successRate, 0) / workflows.length)}%`
                      : "—"}
                  </p>
                  <p className="text-xs text-lia-text-primary">{t("averageOfAutomations")}</p>
                </div>
                <div className="w-10 h-10 bg-wedo-orange/15 rounded-md flex items-center justify-center">
                  <Target className="w-5 h-5 text-wedo-orange" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-lia-text-primary">{t("automationsLabel")}</p>
                  <p className="text-2xl font-semibold text-wedo-purple">{workflows.length}</p>
                  <p className="text-xs text-lia-text-primary">{t("configured")}</p>
                </div>
                <div className="w-10 h-10 bg-wedo-purple/15 rounded-md flex items-center justify-center">
                  <FileText className="w-5 h-5 text-wedo-purple" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{t("configuredWorkflows")}</span>
              <Button className="gap-2">
                <Plus className="w-4 h-4" />
                {t("newWorkflow")}
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {workflows.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Workflow className="w-10 h-10 text-lia-text-primary mb-3" />
                <p className="text-sm font-medium text-lia-text-primary mb-1">
                  {t("emptyTitle")}
                </p>
                <p className="text-xs text-lia-text-primary mb-4">
                  {t("emptyDesc")}
                </p>
                <Button size="sm" className="gap-2">
                  <Plus className="w-4 h-4" />
                  {t("createFirst")}
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {workflows.map((workflow) => (
                  <div
                    key={workflow.id}
                    className="flex items-center justify-between p-4 border border-lia-border-subtle rounded-xl hover:transition-shadow"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={`w-10 h-10 rounded-md flex items-center justify-center ${
                          workflow.status === "active" ? "bg-status-success/15" : "bg-lia-bg-tertiary"
                        }`}
                      >
                        <Workflow
                          className={`w-5 h-5 ${
                            workflow.status === "active" ? "text-status-success" : "text-lia-text-primary"
                          }`}
                        />
                      </div>
                      <div>
                        <h4 className="font-medium text-lia-text-primary">{workflow.name}</h4>
                        {workflow.description && (
                          <p className="text-sm text-lia-text-primary">{workflow.description}</p>
                        )}
                        <div className="flex items-center gap-3 mt-1 text-xs text-lia-text-primary">
                          <span>{t("trigger", { value: labelForTrigger(workflow.triggerType) })}</span>
                          <span>•</span>
                          <span>{t("executions", { count: workflow.executions })}</span>
                          <span>•</span>
                          <span className="text-status-success">{t("successPct", { pct: workflow.successRate })}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Chip variant="neutral" muted={workflow.status !== "active"}>
                        {workflow.status === "active" ? t("statusActive") : t("statusPaused")}
                      </Chip>
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4 mr-2" />
                        {t("edit")}
                      </Button>
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("quickActions")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button variant="outline" className="h-auto p-4 justify-start gap-3">
                <Plus className="w-5 h-5 text-lia-text-secondary" />
                <div className="text-left">
                  <div className="font-medium">{t("createWorkflow")}</div>
                  <div className="text-sm text-lia-text-primary">{t("createWorkflowDesc")}</div>
                </div>
              </Button>

              <Button variant="outline" className="h-auto p-4 justify-start gap-3">
                <Download className="w-5 h-5 text-status-success" />
                <div className="text-left">
                  <div className="font-medium">{t("importTemplate")}</div>
                  <div className="text-sm text-lia-text-primary">{t("importTemplateDesc")}</div>
                </div>
              </Button>

              <Button variant="outline" className="h-auto p-4 justify-start gap-3">
                <BarChart3 className="w-5 h-5 text-wedo-purple" />
                <div className="text-left">
                  <div className="font-medium">{t("viewAnalytics")}</div>
                  <div className="text-sm text-lia-text-primary">{t("viewAnalyticsDesc")}</div>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderBuilder = () => (
    <div className="text-center py-12">
      <Workflow className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
      <h3 className="text-lg font-medium text-lia-text-primary mb-2">{t("builderTitle")}</h3>
      <p className="text-lia-text-primary">{t("builderDesc")}</p>
    </div>
  )

  const renderTemplates = () => (
    <div className="text-center py-12">
      <FileText className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
      <h3 className="text-lg font-medium text-lia-text-primary mb-2">{t("templateLibrary")}</h3>
      <p className="text-lia-text-primary">{t("templateLibraryDesc")}</p>
    </div>
  )

  const renderLogs = () => (
    <div className="text-center py-12">
      <Activity className="w-12 h-12 text-lia-text-primary mx-auto mb-4" />
      <h3 className="text-lg font-medium text-lia-text-primary mb-2">{t("executionLogs")}</h3>
      <p className="text-lia-text-primary">{t("executionLogsDesc")}</p>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-lia-text-primary flex items-center gap-2">
            <Workflow className="w-5 h-5 text-lia-text-secondary" />
            {t("pageTitle")}
          </h2>
          <p className="text-sm text-lia-text-primary">
            {t("pageSubtitle")}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-2">
            <Download className="w-4 h-4" />
            {t("export")}
          </Button>
          <Button size="sm" className="gap-2">
            <Plus className="w-4 h-4" />
            {t("newWorkflow")}
          </Button>
        </div>
      </div>

      <div className="flex space-x-1 bg-lia-bg-tertiary p-1 rounded-xl w-fit">
        {[
          { id: "overview", label: t("tabOverview"), icon: BarChart3 },
          { id: "builder", label: t("tabBuilder"), icon: Workflow },
          { id: "templates", label: t("tabTemplates"), icon: FileText },
          { id: "logs", label: t("tabLogs"), icon: Activity },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedView(tab.id as Parameters<typeof setSelectedView>[0])}
            className={`flex items-center gap-2 px-3 py-3 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none ${
              selectedView === tab.id
                ? "bg-lia-bg-primary text-lia-text-primary"
                : "text-lia-text-primary hover:text-lia-text-primary"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {selectedView === "overview" && renderOverview()}
      {selectedView === "builder" && renderBuilder()}
      {selectedView === "templates" && renderTemplates()}
      {selectedView === "logs" && renderLogs()}
    </div>
  )
}
