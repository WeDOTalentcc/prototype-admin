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
import {
  SentenceBuilder,
  type SentenceBuilderState,
  type TriggerOption,
  type ActionOption,
  type ConditionOperator,
  type ConditionFieldDef,
} from "./SentenceBuilder"
import {
  useCreateAutomation,
  useUpdateAutomation,
  type AutomationPayload,
} from "@/hooks/automations/useAutomationMutations"

interface ApiAutomation {
  id: string
  name: string
  description?: string | null
  trigger_type: string
  trigger_data?: Record<string, unknown> | null
  action_type: string
  action_data?: Record<string, unknown> | null
  conditions?: Array<{ field: string; operator: string; value: unknown }> | null
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
  triggerData: Record<string, unknown>
  actionType: string
  actionData: Record<string, unknown>
  conditions: Array<{ field: string; operator: string; value: unknown }>
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
    triggerData: a.trigger_data ?? {},
    actionType: a.action_type,
    actionData: a.action_data ?? {},
    conditions: a.conditions ?? [],
    lastRun: a.last_executed_at ?? null,
    executions: a.executions_count ?? 0,
    successRate: a.success_rate ?? 100,
  }
}

type ViewTab = "overview" | "builder" | "templates" | "logs"

// ─── Mock catalog (Sprint A.5) ───────────────────────────────────────
// TODO Sprint A.7: substituir mock por useTriggerTypes() + useActionTypes()
// hooks (já existem em useAutomationMutations.ts) quando endpoints estiverem
// canonical no backend. Hoje mantemos hardcoded pra desbloquear UX flow.

const MOCK_TRIGGERS: TriggerOption[] = [
  {
    value: "stage_changed",
    label: "chega na etapa",
    params: [
      {
        name: "stage_id",
        label: "etapa",
        type: "select",
        options: [
          { value: "screening", label: "Triagem" },
          { value: "interview", label: "Entrevista" },
          { value: "offer", label: "Oferta" },
        ],
      },
    ],
  },
  { value: "candidate_applied", label: "se candidata", params: [] },
  { value: "wsi_score_received", label: "tem score WSI atribuído", params: [] },
]

const MOCK_ACTIONS: ActionOption[] = [
  {
    value: "send_whatsapp",
    label: "envie WhatsApp",
    params: [
      {
        name: "template_id",
        label: "modelo",
        type: "select",
        options: [
          { value: "interview_invite", label: "Convite entrevista" },
          { value: "rejection", label: "Recusa" },
        ],
      },
    ],
  },
  {
    value: "move_stage",
    label: "mova para etapa",
    params: [
      {
        name: "stage_id",
        label: "etapa destino",
        type: "select",
        options: [
          { value: "interview", label: "Entrevista" },
          { value: "offer", label: "Oferta" },
          { value: "rejected", label: "Rejeitado" },
        ],
      },
    ],
  },
  {
    value: "send_email",
    label: "envie email",
    params: [{ name: "template_id", label: "modelo", type: "string" }],
  },
]

const MOCK_OPERATORS: ConditionOperator[] = [
  { value: "eq", label: "for igual a" },
  { value: "gt", label: "for maior que" },
  { value: "lt", label: "for menor que" },
  { value: "contains", label: "contém" },
]

const MOCK_CONDITION_FIELDS: ConditionFieldDef[] = [
  { value: "candidate.wsi_score", label: "score WSI", type: "number" },
  { value: "candidate.big_five.openness", label: "abertura (Big Five)", type: "number" },
  { value: "candidate.years_experience", label: "anos de experiência", type: "number" },
  { value: "candidate.expected_salary", label: "pretensão salarial", type: "number" },
]

function workflowToBuilderState(w: WorkflowItem): SentenceBuilderState {
  return {
    trigger: { type: w.triggerType, params: w.triggerData ?? {} },
    conditions: w.conditions ?? [],
    actions: [{ type: w.actionType, params: w.actionData ?? {} }],
    name: w.name,
  }
}

function builderStateToPayload(state: SentenceBuilderState): AutomationPayload {
  const firstAction = state.actions[0]
  return {
    name: state.name,
    trigger_type: state.trigger?.type ?? "",
    trigger_data: state.trigger?.params ?? {},
    action_type: firstAction?.type ?? "",
    action_data: firstAction?.params ?? {},
    conditions: state.conditions,
  }
}

export function AutomationsTab({ onSettingsChange: _onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const t = useTranslations("settings.recruitment.automationsTab")
  const [selectedView, setSelectedView] = useState<ViewTab>("overview")
  const [editingAutomation, setEditingAutomation] = useState<
    { id?: string; initial: SentenceBuilderState } | null
  >(null)
  const { companyId } = useCompanyId()

  const createMutation = useCreateAutomation()
  const updateMutation = useUpdateAutomation()

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

  const openNewAutomation = () => {
    setEditingAutomation({
      initial: { trigger: undefined, conditions: [], actions: [], name: "" },
    })
    setSelectedView("builder")
  }

  const openEditAutomation = (w: WorkflowItem) => {
    setEditingAutomation({ id: w.id, initial: workflowToBuilderState(w) })
    setSelectedView("builder")
  }

  const closeBuilder = () => {
    setEditingAutomation(null)
    setSelectedView("overview")
  }

  const handleSave = async (state: SentenceBuilderState) => {
    const payload = builderStateToPayload(state)
    if (editingAutomation?.id) {
      await updateMutation.mutateAsync({ id: editingAutomation.id, ...payload })
    } else {
      await createMutation.mutateAsync(payload)
    }
    closeBuilder()
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
        <Button size="sm" className="gap-2" onClick={openNewAutomation}>
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
                    <Button size="sm" className="gap-2" onClick={openNewAutomation}>
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
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0"
                          aria-label={t("edit")}
                          onClick={() => openEditAutomation(workflow)}
                        >
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
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-medium text-lia-text-primary">
              {editingAutomation?.id ? t("builderTitleEdit") : t("builderTitleNew")}
            </h3>
            <p className="text-xs text-lia-text-secondary mt-0.5">{t("builderDesc")}</p>
          </div>
          <SentenceBuilder
            initial={editingAutomation?.initial}
            triggers={MOCK_TRIGGERS}
            actions={MOCK_ACTIONS}
            operators={MOCK_OPERATORS}
            conditionFields={MOCK_CONDITION_FIELDS}
            onSave={handleSave}
            onCancel={closeBuilder}
          />
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
