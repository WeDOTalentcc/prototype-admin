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
import { HubLoadingState, ConfigurableFieldCard } from "./_shared"
import { apiFetch } from "@/lib/api/api-fetch"
import { useAllLiaFieldToggles } from "@/hooks/settings/useLiaFieldTogglesForSection"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import {
  LIA_FIELD_DEFINITIONS,
  type LiaFieldKey,
} from "@/hooks/company/use-company-lia-instructions"
import { LiaImpactSummary } from "@/components/settings/LiaImpactSummary"

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
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
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
  const lia = useAllLiaFieldToggles()

  const handleToggleChange = (fieldKey: string, isActive: boolean) =>
    lia.saveToggle(fieldKey, isActive)

  const handleInstructionSave = (fieldKey: string, instruction: string) =>
    lia.saveInstruction(fieldKey, instruction)

  // P2-7 (audit 2026-05-26): batch operations sobre os 34 toggles.
  const handleClearAllInstructions = () => {
    if (typeof window !== "undefined" && !window.confirm(
      "Limpar TODAS as instruções customizadas dos 34 campos LIA? Esta ação não pode ser desfeita. Os toggles ON/OFF permanecem como estão.",
    )) {
      return
    }
    lia.clearAllInstructions()
  }

  const handleBatchToggleAll = (targetState: boolean) => {
    const action = targetState ? "ativar" : "desativar"
    if (typeof window !== "undefined" && !window.confirm(
      `${action.charAt(0).toUpperCase() + action.slice(1)} TODOS os 34 toggles de campos LIA? Instruções customizadas permanecem inalteradas.`,
    )) {
      return
    }
    lia.toggleAll(targetState)
  }

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

  if (lia.isLoading) {
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
      <LiaImpactSummary toggles={lia.toggles} />

      {lia.error && (
        <div className="flex items-center gap-2 p-3 bg-status-error/10 border border-status-error/30 rounded-xl">
          <AlertCircle className="w-5 h-5 text-status-error shrink-0" />
          <p className="text-sm text-status-error">{lia.error}</p>
        </div>
      )}

      <Tabs defaultValue="fields" className="w-full">
        <TabsList>
          <TabsTrigger value="fields">
            <Brain className="w-4 h-4 mr-2" />
            {t("tabs.fields", { default: "Campos LIA" })}
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
          {/* P2-7 (audit 2026-05-26): batch actions bar — opera sobre todos
              os 34 toggles de uma vez. Confirmacao via window.confirm. */}
          <div
            className="flex flex-wrap items-center gap-2 p-3 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary/50"
            data-testid="lia-fields-batch-actions"
          >
            <span className="text-xs font-medium text-lia-text-secondary mr-2">
              Ações em massa:
            </span>
            <button
              type="button"
              onClick={() => handleBatchToggleAll(true)}
              className="text-xs px-2.5 py-1 rounded-md bg-lia-bg-primary hover:bg-wedo-cyan/10 border border-lia-border-default text-lia-text-primary transition-colors motion-reduce:transition-none"
              data-testid="batch-activate-all"
            >
              Ativar todos
            </button>
            <button
              type="button"
              onClick={() => handleBatchToggleAll(false)}
              className="text-xs px-2.5 py-1 rounded-md bg-lia-bg-primary hover:bg-status-warning/10 border border-lia-border-default text-lia-text-primary transition-colors motion-reduce:transition-none"
              data-testid="batch-deactivate-all"
            >
              Desativar todos
            </button>
            <button
              type="button"
              onClick={handleClearAllInstructions}
              className="text-xs px-2.5 py-1 rounded-md bg-lia-bg-primary hover:bg-status-error/10 border border-lia-border-default text-lia-text-primary transition-colors motion-reduce:transition-none"
              data-testid="batch-clear-instructions"
            >
              Limpar todas as instruções
            </button>
          </div>

          <div className="rounded-md bg-lia-bg-secondary border border-lia-border-subtle px-3 py-2 mb-2 text-xs text-lia-text-tertiary">
            <span className="font-medium text-lia-text-secondary">Ativo</span>: o campo é
            enviado como contexto para a IA.{" "}
            <span className="font-medium text-lia-text-secondary">Inativo</span>: o dado é
            ocultado e a LIA usa uma estratégia de fallback.
          </div>

          {Object.entries(fieldsByCategory).map(([category, fields]) => (
            <section key={category} className="space-y-3">
              <h4 className={textStyles.h4}>{category}</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {fields.map((field) => (
                  <ConfigurableFieldCard
                    key={field.key}
                    label={field.label}
                    hint={field.location}
                    showToggle
                    isActive={lia.toggles[field.key] ?? false}
                    onToggleChange={(active) => handleToggleChange(field.key, active)}
                    instruction={lia.comments[field.key] || ""}
                    onInstructionSave={(text) => handleInstructionSave(field.key, text)}
                    isSaving={lia.savingKeys.has(field.key)}
                    placeholder={`Instrução opcional para ${personaName} sobre este campo...`}
                  />
                ))}
              </div>
            </section>
          ))}
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
        <AlertCircle className="w-5 h-5 text-status-warning shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="text-sm font-medium text-status-warning">
            {t("tenantOverride.title", { default: "Tenant Override (YAML)" })}
          </p>
          <p className="text-xs text-status-warning">
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
          <p className="text-xs text-status-error">{listError}</p>
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
            className="flex-1 px-3 py-1.5 text-sm bg-lia-bg-primary border border-lia-border-default rounded-md text-lia-text-primary"
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
            className="w-full p-3 font-mono text-xs bg-lia-bg-primary border border-lia-border-default rounded-md text-lia-text-primary"
            placeholder="metadata:\n  version: 1.0.0-tenant\n..."
          />
        )}

        {editorError && (
          <div className="flex items-start gap-2 p-3 bg-status-error/10 border border-status-error/30 rounded-xl">
            <AlertCircle className="w-4 h-4 text-status-error shrink-0 mt-0.5" />
            <p className="text-xs text-status-error">{editorError}</p>
          </div>
        )}

        {savedAt && (
          <div className="flex items-center gap-2 p-3 bg-status-success/10 border border-status-success/30 rounded-xl">
            <CheckCircle2 className="w-4 h-4 text-status-success shrink-0" />
            <p className="text-xs text-status-success">
              {t("tenantOverride.saved", { default: "Salvo em" })}{" "}
              {new Date(savedAt).toLocaleString()}
            </p>
          </div>
        )}

        {warnings.length > 0 && (
          <ul className="space-y-1">
            {warnings.map((w, idx) => (
              <li key={idx} className="text-xs text-status-warning flex items-start gap-1">
                <AlertCircle className="w-3 h-3 shrink-0 mt-0.5" />
                {w}
              </li>
            ))}
          </ul>
        )}

        <div className="flex items-center justify-end gap-2 pt-2">
          {hasExistingOverride && (
            <Button
              type="button"
              variant="destructive"
              size="sm"
              onClick={handleDelete}
              disabled={isDeleting || isSaving || isFetchingContent}
              data-testid="delete-btn"
            >
              {isDeleting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
              {t("tenantOverride.delete", { default: "Remover override" })}
            </Button>
          )}
          <Button
            type="button"
            size="sm"
            onClick={handleSave}
            disabled={!isDirty || isSaving || isFetchingContent || isDeleting}
            data-testid="save-btn"
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
          </Button>
        </div>
      </section>
    </div>
  )
}
