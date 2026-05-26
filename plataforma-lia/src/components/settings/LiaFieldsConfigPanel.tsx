"use client"

/**
 * LiaFieldsConfigPanel — canonical painel de instruções LIA per campo + tenant override YAML.
 *
 * Audit 2026-05-20 Sessão H / Tema D: LIA_FIELD_DEFINITIONS tem 34 keys
 * canonical mas UI só expunha LiaFieldToggle em 3 (BenefitsTab, DepartmentsTab,
 * WorkforceSection). Os outros 31 fields ficavam com defaults invisíveis ao
 * recrutador. Este painel expõe TODOS os 34 toggles agrupados por category.
 *
 * Wave 2 Agent B (2026-05-21) — T-13 Fase 2: tab nova "Tenant Override (YAML)"
 * para customizar persona/instruções da LIA per-tenant SEM deploy.
 * Backward compat 100%: tab "fields" preserva comportamento original.
 *
 * Multi-tenancy: company_id via useCompanyId() (JWT) — nunca user input.
 * Persistência toggles: PUT /api/backend-proxy/company/{companyId}/field-toggles
 *   (body: { toggles, comments }) — schema canonical FieldTogglesUpdate
 * Persistência overrides: PUT /api/backend-proxy/admin/prompts/tenant-overrides/{path}
 */

import React, { useState, useEffect, useCallback } from "react"
import { useTranslations } from "next-intl"
import { useAuth } from "@/contexts/auth-context"
import {
  Brain,
  Loader2,
  AlertCircle,
  Code,
  Save,
  Trash2,
  Plus,
  CheckCircle2,
} from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { HubLoadingState } from "./_shared"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"
import useCompanyId from "@/hooks/company/useCompanyId"
import { LiaFieldToggle } from "@/components/settings/LiaFieldToggle"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AiPersonaPanel } from "@/components/settings/AiPersonaPanel"
import { Sparkles } from "lucide-react"
import {
  LIA_FIELD_DEFINITIONS,
  type LiaFieldKey,
} from "@/hooks/company/use-company-lia-instructions"
import { LiaImpactSummary } from "@/components/settings/LiaImpactSummary"

interface LiaFieldsConfig {
  lia_field_toggles: Partial<Record<LiaFieldKey, boolean>>
  lia_instructions: Partial<Record<LiaFieldKey, string>>
}

const DEFAULT_CONFIG: LiaFieldsConfig = {
  lia_field_toggles: {},
  lia_instructions: {},
}

// T-13 — Canonical YAML paths permitidos (alinhado com backend _ALLOWED_PATH_PREFIXES).
const CANONICAL_YAML_PATHS = [
  "shared/lia_persona",
  "shared/guardrails_block",
  "shared/compliance_block",
  "shared/defensive",
  "domains/sourcing",
  "domains/cv_screening",
  "domains/orchestrator",
  "domains/recruiter_assistant",
  "domains/talent_pool",
  "domains/job_creation",
  "domains/job_management",
  "domains/pipeline",
  "domains/communication",
] as const

interface TenantOverrideEntry {
  path: string
  version: string
  last_updated_at: string
  size_bytes: number
}

interface TenantOverrideListResponse {
  company_id: string
  total: number
  overrides: TenantOverrideEntry[]
}

export function LiaFieldsConfigPanel() {
  const t = useTranslations("settings.liaFields")
  const { companyId, isLoading: isLoadingCompany } = useCompanyId()
  // E1 (audit 2026-05-21): only WeDOTalent staff (role wedotalent_admin) can
  // see / edit the raw YAML tenant override tab. Customer-end users — even
  // their org-level admin — must not have access. This is defense-in-depth:
  // the backend already enforces the role via require_wedotalent_admin (C2),
  // but hiding the tab eliminates the UX confusion ("toggle here breaks
  // everything") and the curiosity-driven escalations.
  const { user } = useAuth()
  // E1 enforcement: User.role enum (auth-service.ts) was extended in C24 to
  // include "wedotalent_admin" canonical (backend role from C1). Type-safe
  // comparison replaces the legacy string cast workaround.
  const canSeeRawYaml = user?.role === "wedotalent_admin"
  const [config, setConfig] = useState<LiaFieldsConfig>(DEFAULT_CONFIG)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [savingFields, setSavingFields] = useState<Set<string>>(new Set())

  const fetchConfig = useCallback(async () => {
    if (!companyId) return
    setIsLoading(true)
    setError(null)
    try {
      const res = await apiFetch(
        `/api/backend-proxy/company/${encodeURIComponent(companyId)}/field-toggles`,
      )
      if (!res.ok) {
        if (res.status === 404 || res.status === 422) {
          setConfig(DEFAULT_CONFIG)
          return
        }
        throw new Error(`Failed to fetch config: ${res.status}`)
      }
      const data = await res.json()
      // Backend canonical: data.toggles (Record<string,bool>) + data.comments (Record<string,str|null>)
      // Filter null comments — schema FieldToggleResponse permite comment=null
      const instructions: Record<string, string> = {}
      for (const [k, v] of Object.entries(data.comments || {})) {
        if (typeof v === "string" && v.trim()) instructions[k] = v
      }
      setConfig({
        lia_field_toggles: data.toggles || {},
        lia_instructions: instructions,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar configurações LIA")
      setConfig(DEFAULT_CONFIG)
    } finally {
      setIsLoading(false)
    }
  }, [companyId])

  useEffect(() => {
    if (!isLoadingCompany && companyId) {
      fetchConfig()
    } else if (!isLoadingCompany && !companyId) {
      setConfig(DEFAULT_CONFIG)
      setIsLoading(false)
    }
  }, [fetchConfig, isLoadingCompany, companyId])

  const persistConfig = useCallback(
    async (next: LiaFieldsConfig, fieldKey: string) => {
      if (!companyId) return
      setSavingFields((prev) => new Set(prev).add(fieldKey))
      try {
        const res = await apiFetch(
          `/api/backend-proxy/company/${encodeURIComponent(companyId)}/field-toggles`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              toggles: next.lia_field_toggles,
              comments: next.lia_instructions,
            }),
          },
        )
        if (!res.ok) throw new Error(`Save failed: ${res.status}`)
        setConfig(next)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao salvar configuração LIA")
      } finally {
        setSavingFields((prev) => {
          const n = new Set(prev)
          n.delete(fieldKey)
          return n
        })
      }
    },
    [companyId],
  )

  const handleToggleChange = useCallback(
    (fieldKey: string, isActive: boolean) => {
      const next: LiaFieldsConfig = {
        ...config,
        lia_field_toggles: { ...config.lia_field_toggles, [fieldKey]: isActive },
      }
      persistConfig(next, fieldKey)
    },
    [config, persistConfig],
  )

  const handleInstructionSave = useCallback(
    (fieldKey: string, instruction: string) => {
      const next: LiaFieldsConfig = {
        ...config,
        lia_instructions: { ...config.lia_instructions, [fieldKey]: instruction },
      }
      persistConfig(next, fieldKey)
    },
    [config, persistConfig],
  )

  const fieldsByCategory = React.useMemo(() => {
    const groups: Record<string, Array<{ key: LiaFieldKey; label: string; location: string }>> = {}
    for (const [key, def] of Object.entries(LIA_FIELD_DEFINITIONS) as Array<
      [LiaFieldKey, { label: string; category: string; location: string }]
    >) {
      if (!groups[def.category]) groups[def.category] = []
      groups[def.category].push({ key, label: def.label, location: def.location })
    }
    return groups
  }, [])

  if (isLoadingCompany || isLoading) {
    return <HubLoadingState />
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3 p-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
        <Brain className="w-5 h-5 text-lia-btn-primary-bg shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h3 className={textStyles.h3}>{t("title", { default: "Instruções LIA por Campo" })}</h3>
          <p className="text-sm text-lia-text-secondary dark:text-lia-text-secondary">
            {t("description", {
              default:
                "Configure como a LIA deve interpretar cada campo da empresa. Toggles definem se a IA pode sugerir/preencher; instruções customizam comportamento.",
            })}
          </p>
          <p className="text-xs text-lia-text-secondary dark:text-lia-text-secondary">
            <strong>{Object.keys(LIA_FIELD_DEFINITIONS).length}</strong>{" "}
            {t("fieldsTotal", { default: "campos canonical disponíveis" })}.
          </p>
        </div>
      </div>

      {/* P1-9 (audit 2026-05-26): visualiza diferencial competitivo invisível —
          quantos campos canonical a LIA consome + exemplos por campo. */}
      <LiaImpactSummary toggles={config.lia_field_toggles} />

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      <Tabs defaultValue="fields" className="w-full">
        <TabsList>
          <TabsTrigger value="fields">
            <Brain className="w-4 h-4 mr-2" />
            {t("tabs.fields", { default: "Campos LIA" })}
          </TabsTrigger>
          {/* E2.4 (audit 2026-05-21): tab "Personalidade da IA" — input
              estruturado de nome + tom. Substitui o YAML cru pra clientes
              finais; persona base permanece imutável no backend. */}
          <TabsTrigger value="ai-persona" data-testid="tab-ai-persona">
            <Sparkles className="w-4 h-4 mr-2" />
            {t("tabs.aiPersona", { default: "Personalidade da IA" })}
          </TabsTrigger>
          {/*
            E1 gate: only render the raw-YAML tab for WeDOTalent staff.
            Backend equivalent gate at app/api/v1/admin_prompts.py uses
            require_wedotalent_admin — the UI mirrors that posture so the
            tab is never visible to customer-end roles (admin/recruiter/viewer).
            When the future admin2.wedotalent.cc UI is built, this entire
            block migrates there; for now WeDOTalent staff editing in-app
            is the bridge until that ships.
          */}
          {canSeeRawYaml && (
            <TabsTrigger value="tenant-override" data-testid="tab-tenant-override">
              <Code className="w-4 h-4 mr-2" />
              {t("tabs.tenantOverride", { default: "Tenant Override (YAML)" })}
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="fields" className="space-y-6 mt-4">
          {Object.entries(fieldsByCategory).map(([category, fields]) => (
            <section key={category} className="space-y-3">
              <h4 className={textStyles.h4}>{category}</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {fields.map((field) => (
                  <div
                    key={field.key}
                    className="flex items-center justify-between p-3 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-subtle rounded-xl"
                  >
                    <div className="flex-1 min-w-0 mr-3">
                      <p className="text-sm font-medium text-lia-text-primary truncate">{field.label}</p>
                      <p className="text-xs text-lia-text-secondary truncate" title={field.location}>
                        {field.location}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {savingFields.has(field.key) && (
                        <Loader2 className="w-3 h-3 animate-spin text-lia-text-secondary" />
                      )}
                      <LiaFieldToggle
                        fieldKey={field.key}
                        isActive={config.lia_field_toggles[field.key] ?? false}
                        currentInstruction={config.lia_instructions[field.key] || ""}
                        onToggleChange={handleToggleChange}
                        onInstructionSave={handleInstructionSave}
                        compact
                      />
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </TabsContent>

        <TabsContent value="ai-persona" className="mt-4">
          <AiPersonaPanel />
        </TabsContent>

        {/* E1: content rendered only for WeDOTalent staff (same gate as the trigger). */}
        {canSeeRawYaml && (
          <TabsContent value="tenant-override" className="mt-4">
            <TenantOverrideYamlEditor />
          </TabsContent>
        )}
      </Tabs>
    </div>
  )
}


// ---------------------------------------------------------------------------
// T-13 — Tenant Override YAML editor (sub-component)
// ---------------------------------------------------------------------------

function TenantOverrideYamlEditor() {
  const t = useTranslations("settings.liaFields")
  const [overrides, setOverrides] = useState<TenantOverrideEntry[]>([])
  const [isLoadingList, setIsLoadingList] = useState(true)
  const [listError, setListError] = useState<string | null>(null)

  const [selectedPath, setSelectedPath] = useState<string>(CANONICAL_YAML_PATHS[0])
  const [yamlContent, setYamlContent] = useState<string>("")
  const [originalContent, setOriginalContent] = useState<string>("")
  const [isFetchingContent, setIsFetchingContent] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [editorError, setEditorError] = useState<string | null>(null)
  const [savedAt, setSavedAt] = useState<string | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])

  const fetchOverrides = useCallback(async () => {
    setIsLoadingList(true)
    setListError(null)
    try {
      const res = await apiFetch("/api/backend-proxy/admin/prompts/tenant-overrides")
      if (!res.ok) {
        throw new Error(`Failed to fetch overrides list: ${res.status}`)
      }
      const data: TenantOverrideListResponse = await res.json()
      setOverrides(data.overrides || [])
    } catch (err) {
      setListError(err instanceof Error ? err.message : "Erro ao carregar overrides")
      setOverrides([])
    } finally {
      setIsLoadingList(false)
    }
  }, [])

  useEffect(() => {
    fetchOverrides()
  }, [fetchOverrides])

  const fetchPathContent = useCallback(async (path: string) => {
    setIsFetchingContent(true)
    setEditorError(null)
    setSavedAt(null)
    setWarnings([])
    try {
      const res = await apiFetch(
        `/api/backend-proxy/admin/prompts/tenant-overrides/${path}`,
      )
      if (res.status === 404) {
        // No override yet — start with empty template
        const template = `metadata:\n  version: "1.0.0-tenant-${Date.now()}"\n  description: "Override custom"\n\nsystem_prompt: |\n  # Conteúdo customizado aqui\n`
        setYamlContent(template)
        setOriginalContent("")
        return
      }
      if (!res.ok) {
        throw new Error(`Failed to fetch content: ${res.status}`)
      }
      const data = await res.json()
      setYamlContent(data.content || "")
      setOriginalContent(data.content || "")
    } catch (err) {
      setEditorError(err instanceof Error ? err.message : "Erro ao carregar override")
    } finally {
      setIsFetchingContent(false)
    }
  }, [])

  useEffect(() => {
    if (selectedPath) {
      fetchPathContent(selectedPath)
    }
  }, [selectedPath, fetchPathContent])

  const handleSave = useCallback(async () => {
    setIsSaving(true)
    setEditorError(null)
    setSavedAt(null)
    setWarnings([])
    try {
      const res = await apiFetch(
        `/api/backend-proxy/admin/prompts/tenant-overrides/${selectedPath}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: yamlContent }),
        },
      )
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || data.error || `Save failed: ${res.status}`)
      }
      setOriginalContent(yamlContent)
      setSavedAt(data.last_updated_at || new Date().toISOString())
      setWarnings(data.validation_warnings || [])
      notifyChatOfSettingsUpdate({
        actionId: "save_lia_field_override",
        section: "lia_fields",
        field: selectedPath,
      })
      await fetchOverrides()
    } catch (err) {
      setEditorError(err instanceof Error ? err.message : "Erro ao salvar override")
    } finally {
      setIsSaving(false)
    }
  }, [selectedPath, yamlContent, fetchOverrides])

  const handleDelete = useCallback(async () => {
    if (!window.confirm(
      t("tenantOverride.confirmDelete", {
        default: "Remover override e voltar ao padrão canonical?",
      }),
    )) return
    setIsDeleting(true)
    setEditorError(null)
    try {
      const res = await apiFetch(
        `/api/backend-proxy/admin/prompts/tenant-overrides/${selectedPath}`,
        { method: "DELETE" },
      )
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || `Delete failed: ${res.status}`)
      }
      setYamlContent("")
      setOriginalContent("")
      setSavedAt(null)
      await fetchOverrides()
    } catch (err) {
      setEditorError(err instanceof Error ? err.message : "Erro ao remover override")
    } finally {
      setIsDeleting(false)
    }
  }, [selectedPath, t, fetchOverrides])

  const isDirty = yamlContent !== originalContent
  const hasExistingOverride = overrides.some((o) => o.path === selectedPath)

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3 p-4 bg-status-warning-bg rounded-xl border border-status-warning-border">
        <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="text-sm font-medium text-amber-900 dark:text-amber-200">
            {t("tenantOverride.title", { default: "Tenant Override (YAML)" })}
          </p>
          <p className="text-xs text-amber-800 dark:text-amber-300">
            {t("tenantOverride.disclaimer", {
              default:
                "Modificações em tenant overrides são per-empresa e hot-reload em até 30 segundos. Backup automático mantido. Reverter via Delete.",
            })}
          </p>
        </div>
      </div>

      {/* Active overrides list */}
      <section className="space-y-2">
        <h4 className={textStyles.h4}>
          {t("tenantOverride.activeOverrides", { default: "Overrides ativos" })}
        </h4>
        {isLoadingList ? (
          <Loader2 className="w-4 h-4 animate-spin text-lia-text-secondary" />
        ) : listError ? (
          <p className="text-xs text-red-600">{listError}</p>
        ) : overrides.length === 0 ? (
          <p className="text-xs text-lia-text-secondary italic">
            {t("tenantOverride.empty", {
              default: "Nenhum override ativo — todos os prompts usam canonical.",
            })}
          </p>
        ) : (
          <ul className="space-y-1">
            {overrides.map((o) => (
              <li
                key={o.path}
                className="flex items-center justify-between text-xs p-2 rounded-lg bg-lia-bg-primary border border-lia-border-subtle"
              >
                <span className="font-mono">{o.path}</span>
                <span className="text-lia-text-secondary">
                  v{o.version} - {new Date(o.last_updated_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Editor */}
      <section className="space-y-3">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-lia-text-primary">
            {t("tenantOverride.pathLabel", { default: "Path canonical:" })}
          </label>
          <select
            value={selectedPath}
            onChange={(e) => setSelectedPath(e.target.value)}
            disabled={isFetchingContent || isSaving || isDeleting}
            data-testid="select-yaml-path"
            className="flex-1 px-3 py-1.5 text-sm bg-lia-bg-primary border border-lia-border-default rounded-lg text-lia-text-primary"
          >
            {CANONICAL_YAML_PATHS.map((p) => (
              <option key={p} value={p}>
                {p}{overrides.some((o) => o.path === p) ? " - customizado" : ""}
              </option>
            ))}
          </select>
        </div>

        {isFetchingContent ? (
          <div className="flex items-center gap-2 p-4">
            <Loader2 className="w-4 h-4 animate-spin text-lia-text-secondary" />
            <span className="text-sm text-lia-text-secondary">
              {t("tenantOverride.loading", { default: "Carregando..." })}
            </span>
          </div>
        ) : (
          <textarea
            value={yamlContent}
            onChange={(e) => {
              setYamlContent(e.target.value)
              setSavedAt(null)
            }}
            data-testid="yaml-editor"
            spellCheck={false}
            rows={18}
            className="w-full p-3 font-mono text-xs bg-lia-bg-primary border border-lia-border-default rounded-xl text-lia-text-primary"
            placeholder="metadata:\n  version: 1.0.0-tenant\n..."
          />
        )}

        {editorError && (
          <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <p className="text-xs text-red-700 dark:text-red-300">{editorError}</p>
          </div>
        )}

        {savedAt && (
          <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
            <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0" />
            <p className="text-xs text-green-700 dark:text-green-300">
              {t("tenantOverride.saved", { default: "Salvo em" })}{" "}
              {new Date(savedAt).toLocaleString()}
            </p>
          </div>
        )}

        {warnings.length > 0 && (
          <ul className="space-y-1">
            {warnings.map((w, idx) => (
              <li key={idx} className="text-xs text-amber-700 dark:text-amber-300 flex items-start gap-1">
                <AlertCircle className="w-3 h-3 shrink-0 mt-0.5" />
                {w}
              </li>
            ))}
          </ul>
        )}

        <div className="flex items-center justify-end gap-2 pt-2">
          {hasExistingOverride && (
            <button
              type="button"
              onClick={handleDelete}
              disabled={isDeleting || isSaving || isFetchingContent}
              data-testid="delete-btn"
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border border-red-200 text-red-700 hover:bg-red-50 disabled:opacity-50"
            >
              {isDeleting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
              {t("tenantOverride.delete", { default: "Remover override" })}
            </button>
          )}
          <button
            type="button"
            onClick={handleSave}
            disabled={!isDirty || isSaving || isFetchingContent || isDeleting}
            data-testid="save-btn"
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs rounded-lg bg-lia-btn-primary-bg text-white hover:opacity-90 disabled:opacity-50"
          >
            {isSaving ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : hasExistingOverride ? (
              <Save className="w-3 h-3" />
            ) : (
              <Plus className="w-3 h-3" />
            )}
            {hasExistingOverride
              ? t("tenantOverride.save", { default: "Salvar override" })
              : t("tenantOverride.create", { default: "Criar override" })}
          </button>
        </div>
      </section>
    </div>
  )
}
