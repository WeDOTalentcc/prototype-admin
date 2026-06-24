"use client"

import { useTranslations } from "next-intl"
import { useEffect, useMemo, useState } from "react"
import { useSearchParams } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { LIA_PENDING_AUTOMATION_STORAGE_KEY } from "./AutomationFromChatBridge"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { SETTINGS_QUERY_KEYS } from "@/hooks/settings/useSettingsBroadcast"
import { HubHeader, HubLoadingState, HubErrorState } from "@/components/settings/_shared"
import { Chip } from "@/components/ui/chip"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover"
import { hasModuleAccess } from "@/utils/license-manager"
import { ModuleUpsell } from "@/components/module-access/module-upsell"
import { apiFetch } from "@/lib/api/api-fetch"
import {
  Edit,
  Plus,
  Workflow,
  FileText,
  Zap,
  Download,
  BarChart3,
  Activity,
  MoreHorizontal,
  Sparkles,
  Play,
  Copy,
  Trash,
} from "lucide-react"
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
  useToggleAutomationActive,
  useTestAutomation,
  useDeleteAutomation,
  useTriggerTypes,
  useActionTypes,
  useOperators,
  useConditionFields,
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

// ─── Catalog mocks (Sprint A.5 → A.7) ────────────────────────────────
// Sprint A.7 (2026-05-26): triggers/actions agora vêm de useTriggerTypes()
// + useActionTypes() (backend canonical em /api/backend-proxy/automations/
// {trigger,action}-types/available). Os arrays MOCK_* abaixo permanecem
// como FALLBACK pra:
//   1) loading state (hook ainda em flight) — evita SentenceBuilder vazio
//   2) error state (backend down) — REGRA 4 fail-explicit no log + UX continua
// Sprint A.8 (2026-05-26): operators + condition_fields agora vêm de
// useOperators() + useConditionFields() (backend canonical em
// /api/backend-proxy/automations/operators/available + condition-fields/available).
// MOCK_OPERATORS / MOCK_CONDITION_FIELDS mantidos como fallback REGRA 4 (error path).

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

// ─── Backend → SentenceBuilder adapters (Sprint A.7) ─────────────────
// Backend canonical shape (lia-agent-system/app/api/v1/automations.py):
//   trigger_types: [{ value, name, description }]
//   action_types:  [{ value, name, description, config_fields: string[] }]
// SentenceBuilder espera TriggerOption/ActionOption com { value, label, params[] }.
// `params` requer schema (name/label/type[/options]) que backend não envia hoje —
// retornamos params=[] (SentenceBuilder renderiza trigger/action standalone sem
// inputs adicionais até backend expor schema completo).
//
// REGRA 4 (anti-silent-fallback): se backend vier com shape inesperado, .map
// resulta em entries com value=undefined → React filtra; logamos warn.

interface BackendTriggerType {
  value?: string
  name?: string
  description?: string
}

interface BackendActionType {
  value?: string
  name?: string
  description?: string
  config_fields?: string[]
}

interface BackendCatalogResponse<T> {
  success?: boolean
  data?: {
    trigger_types?: T[]
    action_types?: T[]
  }
}

function mapBackendTriggers(payload: unknown): TriggerOption[] {
  const root = payload as BackendCatalogResponse<BackendTriggerType> | undefined
  const arr = root?.data?.trigger_types
  if (!Array.isArray(arr) || arr.length === 0) return []
  return arr
    .filter((t): t is BackendTriggerType => !!t && typeof t.value === "string")
    .map((t) => ({
      value: t.value as string,
      label: t.name ?? (t.value as string),
      params: [],
    }))
}

function mapBackendActions(payload: unknown): ActionOption[] {
  const root = payload as BackendCatalogResponse<BackendActionType> | undefined
  const arr = root?.data?.action_types
  if (!Array.isArray(arr) || arr.length === 0) return []
  return arr
    .filter((a): a is BackendActionType => !!a && typeof a.value === "string")
    .map((a) => ({
      value: a.value as string,
      label: a.name ?? (a.value as string),
      params: [],
    }))
}



// Sprint A.8 — operators + condition fields backend canonical adapters
interface BackendOperator {
  value?: string
  name?: string
  label_pt?: string
  label_en?: string
  applicable_types?: string[]
}

interface BackendConditionField {
  value?: string
  name?: string
  label_pt?: string
  label_en?: string
  type?: string
  category?: string
}

interface BackendOperatorsResponse {
  success?: boolean
  data?: { operators?: BackendOperator[] }
}

interface BackendConditionFieldsResponse {
  success?: boolean
  data?: { condition_fields?: BackendConditionField[] }
}

function mapBackendOperators(payload: unknown): ConditionOperator[] {
  const root = payload as BackendOperatorsResponse | undefined
  const arr = root?.data?.operators
  if (!Array.isArray(arr) || arr.length === 0) return []
  return arr
    .filter((o): o is BackendOperator => !!o && typeof o.value === "string")
    .map((o) => ({
      value: o.value as string,
      label: o.label_pt ?? o.name ?? (o.value as string),
    }))
}

// Backend type vocabulary: "number" | "string" | "boolean" | "list".
// SentenceBuilder ConditionFieldDef.type accepts "string" | "number" | "select".
// Map boolean/list → string (closest renderer); upgrade SentenceBuilder vocab later.
function mapBackendConditionFields(payload: unknown): ConditionFieldDef[] {
  const root = payload as BackendConditionFieldsResponse | undefined
  const arr = root?.data?.condition_fields
  if (!Array.isArray(arr) || arr.length === 0) return []
  return arr
    .filter((f): f is BackendConditionField => !!f && typeof f.value === "string")
    .map((f) => {
      const rawType = f.type ?? "string"
      const uiType: "string" | "number" | "select" =
        rawType === "number" ? "number" : "string"
      return {
        value: f.value as string,
        label: f.label_pt ?? f.name ?? (f.value as string),
        type: uiType,
      }
    })
}

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
  const searchParams = useSearchParams()

  // Sprint D.3: hidrata builder a partir de payload vindo do chat LIA
  // (AutomationFromChatBridge persistiu em sessionStorage antes de navegar).
  // Mount-only — evita race com sessionStorage em rerenders subsequentes.
  useEffect(() => {
    if (typeof window === "undefined") return
    try {
      const stored = window.sessionStorage.getItem(
        LIA_PENDING_AUTOMATION_STORAGE_KEY,
      )
      if (!stored) return
      const parsed = JSON.parse(stored) as {
        trigger?: { type: string; params?: Record<string, unknown> }
        conditions?: Array<{ field: string; operator: string; value: unknown }>
        actions?: Array<{ type: string; params?: Record<string, unknown> }>
        name?: string
      }
      // Normaliza params (SentenceBuilderState requer params obrigatório)
      const normalizedTrigger = parsed.trigger
        ? { type: parsed.trigger.type, params: parsed.trigger.params ?? {} }
        : undefined
      const normalizedActions = (parsed.actions ?? []).map((a) => ({
        type: a.type,
        params: a.params ?? {},
      }))
      setEditingAutomation({
        initial: {
          trigger: normalizedTrigger,
          conditions: parsed.conditions ?? [],
          actions: normalizedActions,
          name: parsed.name ?? "",
        },
      })
      setSelectedView("builder")
      window.sessionStorage.removeItem(LIA_PENDING_AUTOMATION_STORAGE_KEY)
    } catch (err) {
      // REGRA 4: log + skip (Builder fica em modo overview, UX não broken)
      console.warn(
        "[AutomationsTab] failed to hydrate from sessionStorage:",
        err,
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Sprint D.3: deep-link ?view=builder abre Builder em modo "novo"
  // mesmo sem sessionStorage payload (caso o bridge não tenha disparado,
  // ex: link compartilhado, voltar do navegador).
  useEffect(() => {
    const view = searchParams?.get("view")
    if (view === "builder" && !editingAutomation) {
      setEditingAutomation({
        initial: { trigger: undefined, conditions: [], actions: [], name: "" },
      })
      setSelectedView("builder")
    }
  }, [searchParams, editingAutomation])

  const createMutation = useCreateAutomation()
  const updateMutation = useUpdateAutomation()
  const toggleMutation = useToggleAutomationActive()
  const testMutation = useTestAutomation()
  const deleteMutation = useDeleteAutomation()

  // Sprint A.7: trigger/action catalog from backend canonical.
  // Fallback to MOCK_* on loading (avoid empty SentenceBuilder) or error
  // (REGRA 4: log warn but keep UX functional).
  const triggerTypesQuery = useTriggerTypes()
  const actionTypesQuery = useActionTypes()
  const operatorsQuery = useOperators()
  const conditionFieldsQuery = useConditionFields()

  const triggers = useMemo<TriggerOption[]>(() => {
    if (triggerTypesQuery.error) {
      console.warn(
        "[AutomationsTab] useTriggerTypes error, using mock fallback:",
        triggerTypesQuery.error,
      )
      return MOCK_TRIGGERS
    }
    const mapped = mapBackendTriggers(triggerTypesQuery.data)
    return mapped.length > 0 ? mapped : MOCK_TRIGGERS
  }, [triggerTypesQuery.data, triggerTypesQuery.error])

  const actions = useMemo<ActionOption[]>(() => {
    if (actionTypesQuery.error) {
      console.warn(
        "[AutomationsTab] useActionTypes error, using mock fallback:",
        actionTypesQuery.error,
      )
      return MOCK_ACTIONS
    }
    const mapped = mapBackendActions(actionTypesQuery.data)
    return mapped.length > 0 ? mapped : MOCK_ACTIONS
  }, [actionTypesQuery.data, actionTypesQuery.error])

  // Sprint A.8: operators + condition fields canonical from backend, with mock fallback.
  const operators = useMemo<ConditionOperator[]>(() => {
    if (operatorsQuery.error) {
      console.warn(
        "[AutomationsTab] useOperators error, using mock fallback:",
        operatorsQuery.error,
      )
      return MOCK_OPERATORS
    }
    const mapped = mapBackendOperators(operatorsQuery.data)
    return mapped.length > 0 ? mapped : MOCK_OPERATORS
  }, [operatorsQuery.data, operatorsQuery.error])

  const conditionFields = useMemo<ConditionFieldDef[]>(() => {
    if (conditionFieldsQuery.error) {
      console.warn(
        "[AutomationsTab] useConditionFields error, using mock fallback:",
        conditionFieldsQuery.error,
      )
      return MOCK_CONDITION_FIELDS
    }
    const mapped = mapBackendConditionFields(conditionFieldsQuery.data)
    return mapped.length > 0 ? mapped : MOCK_CONDITION_FIELDS
  }, [conditionFieldsQuery.data, conditionFieldsQuery.error])

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

  // ─── Sprint D.1+D.4: workflow item actions ────────────────────────
  const handleToggleActive = (workflow: WorkflowItem) => {
    toggleMutation.mutate({
      id: workflow.id,
      isActive: workflow.status !== "active",
    })
  }

  const handleTest = async (workflow: WorkflowItem) => {
    try {
      const result = (await testMutation.mutateAsync({
        id: workflow.id,
        dryRunPayload: {},
      })) as { success?: boolean; result_summary?: string } | null
      const ok = result?.success !== false
      // Voice Quiet Operator
      window.alert(
        ok
          ? t("testOk", { name: workflow.name })
          : t("testFailed", { name: workflow.name }),
      )
    } catch (_err) {
      window.alert(t("testFailed", { name: workflow.name }))
    }
  }

  const handleDuplicate = (workflow: WorkflowItem) => {
    createMutation.mutate({
      name: t("duplicateSuffix", { name: workflow.name }),
      trigger_type: workflow.triggerType,
      trigger_data: workflow.triggerData,
      action_type: workflow.actionType,
      action_data: workflow.actionData,
      conditions: workflow.conditions,
    })
  }

  const handleDelete = (workflow: WorkflowItem) => {
    // MVP: window.confirm (shadcn AlertDialog em polish futuro)
    if (!window.confirm(t("deleteConfirm", { name: workflow.name }))) return
    deleteMutation.mutate(workflow.id)
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
    ...(avgSuccess !== null ? [t("summarySuccess", { pct: String(avgSuccess) })] : []),
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
                            workflow.status === "active" ? "text-wedo-cyan-text" : "text-lia-text-tertiary"
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
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleToggleActive(workflow)
                          }}
                          disabled={toggleMutation.isPending}
                          className="cursor-pointer rounded-md focus:outline-none focus:ring-2 focus:ring-wedo-cyan/40 disabled:opacity-60 disabled:cursor-not-allowed"
                          aria-label={
                            workflow.status === "active"
                              ? t("pauseAutomation")
                              : t("activateAutomation")
                          }
                          data-testid={`workflow-toggle-${workflow.id}`}
                        >
                          <Chip
                            variant={workflow.status === "active" ? "success" : "neutral"}
                            muted={workflow.status !== "active"}
                          >
                            {workflow.status === "active" ? t("statusActive") : t("statusPaused")}
                          </Chip>
                        </button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0"
                          aria-label={t("edit")}
                          onClick={() => openEditAutomation(workflow)}
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </Button>
                        <Popover>
                          <PopoverTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0"
                              aria-label={t("moreActions")}
                              data-testid={`workflow-more-${workflow.id}`}
                            >
                              <MoreHorizontal className="w-3.5 h-3.5" />
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-48 p-1" align="end">
                            <button
                              type="button"
                              onClick={() => handleTest(workflow)}
                              disabled={testMutation.isPending}
                              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-lia-text-primary hover:bg-lia-bg-tertiary disabled:opacity-60 disabled:cursor-not-allowed"
                              data-testid={`workflow-action-test-${workflow.id}`}
                            >
                              <Play className="w-3.5 h-3.5" />
                              {t("actionTest")}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDuplicate(workflow)}
                              disabled={createMutation.isPending}
                              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-lia-text-primary hover:bg-lia-bg-tertiary disabled:opacity-60 disabled:cursor-not-allowed"
                              data-testid={`workflow-action-duplicate-${workflow.id}`}
                            >
                              <Copy className="w-3.5 h-3.5" />
                              {t("actionDuplicate")}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDelete(workflow)}
                              disabled={deleteMutation.isPending}
                              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-status-error hover:bg-status-error/10 disabled:opacity-60 disabled:cursor-not-allowed"
                              data-testid={`workflow-action-delete-${workflow.id}`}
                            >
                              <Trash className="w-3.5 h-3.5" />
                              {t("actionDelete")}
                            </button>
                          </PopoverContent>
                        </Popover>
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
            triggers={triggers}
            actions={actions}
            operators={operators}
            conditionFields={conditionFields}
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
