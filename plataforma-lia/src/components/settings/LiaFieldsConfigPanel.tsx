"use client"

/**
 * LiaFieldsConfigPanel — canonical painel de instruções LIA per campo.
 *
 * Audit 2026-05-20 Sessão H / Tema D: LIA_FIELD_DEFINITIONS tem 34 keys
 * canonical mas UI só expunha LiaFieldToggle em 3 (BenefitsTab, DepartmentsTab,
 * WorkforceSection). Os outros 31 fields ficavam com defaults invisíveis ao
 * recrutador. Este painel expõe TODOS os 34 toggles agrupados por category.
 *
 * Multi-tenancy: company_id via useCompanyId() (JWT) — nunca user input.
 * Persistência: PUT /api/backend-proxy/company/culture-profile/{companyId}
 * com lia_field_toggles + lia_instructions (pattern canonical já usado em
 * useBenefitsTab e useGoalsPlanningHub).
 */

import React, { useState, useEffect, useCallback } from "react"
import { useTranslations } from "next-intl"
import { Brain, Loader2, AlertCircle } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { apiFetch } from "@/lib/api/api-fetch"
import useCompanyId from "@/hooks/company/useCompanyId"
import { LiaFieldToggle } from "@/components/settings/LiaFieldToggle"
import {
  LIA_FIELD_DEFINITIONS,
  type LiaFieldKey,
} from "@/hooks/company/use-company-lia-instructions"

interface LiaFieldsConfig {
  lia_field_toggles: Partial<Record<LiaFieldKey, boolean>>
  lia_instructions: Partial<Record<LiaFieldKey, string>>
}

const DEFAULT_CONFIG: LiaFieldsConfig = {
  lia_field_toggles: {},
  lia_instructions: {},
}

export function LiaFieldsConfigPanel() {
  const t = useTranslations("settings.liaFields")
  const { companyId, isLoading: isLoadingCompany } = useCompanyId()
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
        `/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`,
      )
      if (!res.ok) {
        if (res.status === 404 || res.status === 422) {
          setConfig(DEFAULT_CONFIG)
          return
        }
        throw new Error(`Failed to fetch config: ${res.status}`)
      }
      const data = await res.json()
      setConfig({
        lia_field_toggles: data.lia_field_toggles || {},
        lia_instructions: data.lia_instructions || {},
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
          `/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              lia_field_toggles: next.lia_field_toggles,
              lia_instructions: next.lia_instructions,
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

  // Group fields by category for visual organization
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
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="w-6 h-6 animate-spin text-lia-text-secondary" />
      </div>
    )
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

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

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
    </div>
  )
}
