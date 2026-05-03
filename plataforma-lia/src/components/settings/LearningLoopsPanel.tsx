"use client"

/**
 * LearningLoopsPanel — Sprint B Phase 2
 *
 * 4 toggles for learning loops configuration.
 * Multi-tenancy: company_id from useCompanyId() (JWT), never from user input.
 * LGPD: bigfive_department_history shows disclosure modal before enabling.
 */

import React, { useState, useEffect, useCallback } from "react"
import { Brain, BookOpen, BarChart2, FileText, AlertCircle, X, Loader2 } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import useCompanyId from "@/hooks/company/useCompanyId"

interface LearningLoopsConfig {
  enabled: boolean
  bigfive_company_culture: boolean
  bigfive_department_history: boolean
  wsi_question_effectiveness: boolean
  jd_similar_suggestion: boolean
}

interface ToggleDefinition {
  key: keyof LearningLoopsConfig
  label: string
  description: string
  defaultValue: boolean
  requiresDisclosure?: boolean
  disclosureText?: string
}

const TOGGLE_DEFS: ToggleDefinition[] = [
  {
    key: "enabled",
    label: "Loops de Aprendizado",
    description: "Chave mestre — ativa ou desativa todos os loops de aprendizado automaticamente.",
    defaultValue: true,
  },
  {
    key: "bigfive_company_culture",
    label: "DNA Cultural da Empresa (Layer 3)",
    description:
      "Incorpora o perfil cultural da empresa no ranking Big Five das vagas. Baixo risco — usa apenas dados organizacionais já coletados.",
    defaultValue: true,
  },
  {
    key: "bigfive_department_history",
    label: "Histórico por Departamento (Layer 4)",
    description:
      "Ativa aprendizado específico por departamento/senioridade a partir de contratações confirmadas. Requer mínimo de 10 amostras para ativar.",
    defaultValue: false,
    requiresDisclosure: true,
    disclosureText:
      "Esta funcionalidade armazena médias agregadas de traços comportamentais derivadas de contratações confirmadas, agrupadas por departamento e nível de senioridade. Nenhum dado individual de candidato é armazenado (apenas scores médios anonimizados). Ao ativar, você confirma que os candidatos foram informados sobre o uso de análise comportamental no processo seletivo, conforme exigido pela LGPD (Art. 11). O sistema aplicará automaticamente verificação de impacto adverso — perfis que ultrapassem 10% de variação serão bloqueados até revisão manual.",
  },
  {
    key: "jd_similar_suggestion",
    label: "Sugestão de JD Similar (Phase 1)",
    description:
      "Sugere descrições de vagas similares do histórico da empresa ao criar novas vagas. Ativo quando a empresa tem 10+ vagas históricas.",
    defaultValue: true,
  },
  {
    key: "wsi_question_effectiveness",
    label: "Efetividade de Perguntas WSI (Phase 3)",
    description:
      "Aprende quais perguntas de triagem geram melhores resultados. Funcionalidade em desenvolvimento.",
    defaultValue: false,
  },
]

const DEFAULT_CONFIG: LearningLoopsConfig = {
  enabled: true,
  bigfive_company_culture: true,
  bigfive_department_history: false,
  wsi_question_effectiveness: false,
  jd_similar_suggestion: true,
}

function DisclosureModal({
  onConfirm,
  onCancel,
  text,
}: {
  onConfirm: () => void
  onCancel: () => void
  text: string
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="disclosure-title"
    >
      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl shadow-xl max-w-lg w-full mx-4 p-6 relative">
        <button
          onClick={onCancel}
          className="absolute top-4 right-4 p-1 rounded-md hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-elevated transition-colors"
          aria-label="Fechar"
        >
          <X className="w-4 h-4 text-lia-text-tertiary" />
        </button>
        <div className="flex items-start gap-3 mb-4">
          <AlertCircle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
          <h2 id="disclosure-title" className={textStyles.h3}>
            Aviso LGPD — Dados Comportamentais
          </h2>
        </div>
        <p className={`${textStyles.body} text-lia-text-secondary mb-6 leading-relaxed`}>
          {text}
        </p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg text-sm font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-elevated border border-lia-border-subtle transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-lia-btn-primary-bg text-lia-btn-primary-text hover:opacity-90 transition-opacity"
          >
            Confirmo — Ativar
          </button>
        </div>
      </div>
    </div>
  )
}

function ToggleRow({
  def,
  value,
  masterEnabled,
  onToggle,
  isLoading,
}: {
  def: ToggleDefinition
  value: boolean
  masterEnabled: boolean
  onToggle: (key: keyof LearningLoopsConfig, newValue: boolean) => void
  isLoading: boolean
}) {
  const isDisabled = isLoading || (def.key !== "enabled" && !masterEnabled)
  const IconMap: Record<string, React.ComponentType<{ className?: string }>> = {
    enabled: Brain,
    bigfive_company_culture: Brain,
    bigfive_department_history: BarChart2,
    jd_similar_suggestion: FileText,
    wsi_question_effectiveness: BookOpen,
  }
  const Icon = IconMap[def.key] ?? Brain

  return (
    <div
      className={`flex items-start justify-between gap-4 py-3 px-3 rounded-lg transition-colors ${
        isDisabled ? "opacity-50" : "hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse/40"
      }`}
    >
      <div className="flex items-start gap-3 min-w-0">
        <Icon className="w-4 h-4 text-lia-text-secondary flex-shrink-0 mt-0.5" />
        <div className="min-w-0">
          <p className={`${textStyles.label} text-lia-text-primary`}>{def.label}</p>
          <p className={`${textStyles.description} text-lia-text-tertiary mt-0.5 leading-relaxed`}>
            {def.description}
          </p>
        </div>
      </div>
      <button
        role="switch"
        aria-checked={value}
        aria-label={def.label}
        disabled={isDisabled}
        onClick={() => onToggle(def.key, !value)}
        className={`relative flex-shrink-0 inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200 motion-reduce:transition-none focus:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg ${
          value ? "bg-lia-btn-primary-bg" : "bg-lia-border-default"
        } ${isDisabled ? "cursor-not-allowed" : "cursor-pointer"}`}
      >
        <span
          className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm transition-transform duration-200 motion-reduce:transition-none ${
            value ? "translate-x-4" : "translate-x-0.5"
          }`}
        />
      </button>
    </div>
  )
}

export function LearningLoopsPanel() {
  const { companyId } = useCompanyId()
  const [config, setConfig] = useState<LearningLoopsConfig>(DEFAULT_CONFIG)
  const [isLoading, setIsLoading] = useState(false)
  const [isFetching, setIsFetching] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pendingToggle, setPendingToggle] = useState<{
    key: keyof LearningLoopsConfig
    value: boolean
    disclosureText: string
  } | null>(null)

  useEffect(() => {
    if (!companyId) return
    setIsFetching(true)
    fetch(`/api/backend-proxy/companies/${companyId}/learning-loops-config`)
      .then((r) => r.json())
      .then((data) => {
        if (data?.config) setConfig({ ...DEFAULT_CONFIG, ...data.config })
      })
      .catch(() => setError("Falha ao carregar configurações"))
      .finally(() => setIsFetching(false))
  }, [companyId])

  const applyToggle = useCallback(
    async (key: keyof LearningLoopsConfig, value: boolean) => {
      if (!companyId) return
      setIsLoading(true)
      setError(null)
      setConfig((prev) => ({ ...prev, [key]: value }))
      try {
        const resp = await fetch(
          `/api/backend-proxy/companies/${companyId}/learning-loops-config`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ [key]: value }),
          }
        )
        if (!resp.ok) {
          setConfig((prev) => ({ ...prev, [key]: !value }))
          setError("Falha ao salvar. Tente novamente.")
        } else {
          const data = await resp.json()
          if (data?.config) setConfig({ ...DEFAULT_CONFIG, ...data.config })
        }
      } catch {
        setConfig((prev) => ({ ...prev, [key]: !value }))
        setError("Erro de conexão. Tente novamente.")
      } finally {
        setIsLoading(false)
      }
    },
    [companyId]
  )

  const handleToggle = useCallback(
    (key: keyof LearningLoopsConfig, newValue: boolean) => {
      const def = TOGGLE_DEFS.find((d) => d.key === key)
      if (def?.requiresDisclosure && newValue && def.disclosureText) {
        setPendingToggle({ key, value: newValue, disclosureText: def.disclosureText })
        return
      }
      applyToggle(key, newValue)
    },
    [applyToggle]
  )

  const handleDisclosureConfirm = useCallback(() => {
    if (pendingToggle) {
      applyToggle(pendingToggle.key, pendingToggle.value)
      setPendingToggle(null)
    }
  }, [pendingToggle, applyToggle])

  if (isFetching) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-5 h-5 animate-spin text-lia-text-tertiary" />
      </div>
    )
  }

  return (
    <>
      {pendingToggle && (
        <DisclosureModal
          text={pendingToggle.disclosureText}
          onConfirm={handleDisclosureConfirm}
          onCancel={() => setPendingToggle(null)}
        />
      )}
      <div className="space-y-1">
        <div className="mb-3">
          <p className={`${textStyles.h3} text-lia-text-primary`}>Loops de Aprendizado</p>
          <p className={`${textStyles.description} text-lia-text-secondary mt-1`}>
            Configure quais mecanismos de aprendizado automático a LIA usa para melhorar sugestões ao longo do tempo.
          </p>
        </div>
        {error && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-status-error/10 border border-status-error/20 mb-2">
            <AlertCircle className="w-4 h-4 text-status-error flex-shrink-0" />
            <p className={`${textStyles.description} text-status-error`}>{error}</p>
          </div>
        )}
        <div className={`divide-y divide-lia-border-subtle ${isLoading ? "pointer-events-none" : ""}`}>
          {TOGGLE_DEFS.map((def) => (
            <ToggleRow
              key={def.key}
              def={def}
              value={config[def.key]}
              masterEnabled={config.enabled}
              onToggle={handleToggle}
              isLoading={isLoading}
            />
          ))}
        </div>
      </div>
    </>
  )
}

export default LearningLoopsPanel
