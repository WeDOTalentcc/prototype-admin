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
import { HubLoadingState } from "./_shared"
import useCompanyId from "@/hooks/company/useCompanyId"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

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

const MASTER_DEF: ToggleDefinition = {
  key: "enabled",
  label: "Loops de Aprendizado",
  description:
    "Chave mestre — ativa ou desativa todos os loops de aprendizado automaticamente.",
  defaultValue: true,
}

const SUB_TOGGLE_DEFS: ToggleDefinition[] = [
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

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  enabled: Brain,
  bigfive_company_culture: Brain,
  bigfive_department_history: BarChart2,
  jd_similar_suggestion: FileText,
  wsi_question_effectiveness: BookOpen,
}

function ToggleSwitch({
  value,
  label,
  isDisabled,
  onClick,
}: {
  value: boolean
  label: string
  isDisabled: boolean
  onClick: () => void
}) {
  return (
    <button
      role="switch"
      aria-checked={value}
      aria-label={label}
      disabled={isDisabled}
      onClick={onClick}
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
  )
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

function ToggleCard({
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
  const isDisabled = isLoading || !masterEnabled
  const Icon = ICON_MAP[def.key] ?? Brain

  return (
    <div
      className={`flex items-start justify-between gap-4 p-4 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-subtle rounded-xl transition-colors ${
        isDisabled ? "opacity-50" : ""
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
      <ToggleSwitch
        value={value}
        label={def.label}
        isDisabled={isDisabled}
        onClick={() => onToggle(def.key, !value)}
      />
    </div>
  )
}

export function LearningLoopsPanel() {
  const { companyId } = useCompanyId()
  const [config, setConfig] = useState<LearningLoopsConfig>(DEFAULT_CONFIG)
  const [isLoading, setIsLoading] = useState(false)
  const [isFetching, setIsFetching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // Boy-Scout (audit 2026-05-24 P2-F): sinaliza explicitamente quando o
  // proxy retornou defaults porque o backend não respondeu. Antes o panel
  // caía silenciosamente em DEFAULT_CONFIG — recrutador editava toggles
  // achando que estava salvando, mas o backend nunca devolveu o estado real.
  // REGRA 4 CLAUDE.md (anti-silent-fallback): falhar visível.
  const [backendUnavailable, setBackendUnavailable] = useState(false)
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
        // Proxy retorna 200 OK com source='default' + message='backend
        // unavailable' quando o FastAPI está fora — preserva UX ao mesmo
        // tempo que o panel sinaliza ao usuário que não há config salva.
        const isBackendDown =
          data?.source === "default" && data?.message === "backend unavailable"
        setBackendUnavailable(isBackendDown)
        if (data?.config) setConfig({ ...DEFAULT_CONFIG, ...data.config })
      })
      .catch(() => {
        setError("Falha ao carregar configurações")
        setBackendUnavailable(true)
      })
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
          notifyChatOfSettingsUpdate({
            actionId: "configure_learning_loop",
            section: "learning_loops",
            field: String(key),
            value: value,
          })
          // Boy-Scout P2-F: PATCH bem-sucedido implica backend de volta.
          setBackendUnavailable(false)
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
      const def =
        MASTER_DEF.key === key ? MASTER_DEF : SUB_TOGGLE_DEFS.find((d) => d.key === key)
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
    return <HubLoadingState />
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
      <div className="space-y-6">
        {/* Header banner — canonical pattern (LiaFieldsConfigPanel.tsx:212) com master toggle integrado */}
        <div className="flex items-start justify-between gap-4 p-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
          <div className="flex items-start gap-3 min-w-0">
            <Brain className="w-5 h-5 text-lia-btn-primary-bg shrink-0 mt-0.5" />
            <div className="space-y-1 min-w-0">
              <h3 className={textStyles.h3}>{MASTER_DEF.label}</h3>
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-secondary">
                Configure quais mecanismos de aprendizado automático a LIA usa para melhorar sugestões ao longo do tempo.
              </p>
              <p className="text-xs text-lia-text-secondary dark:text-lia-text-secondary">
                {MASTER_DEF.description}
              </p>
            </div>
          </div>
          <ToggleSwitch
            value={config.enabled}
            label={MASTER_DEF.label}
            isDisabled={isLoading}
            onClick={() => handleToggle(MASTER_DEF.key, !config.enabled)}
          />
        </div>

        {backendUnavailable && (
          <div
            className="flex items-start gap-2 p-3 bg-status-warning-bg border border-status-warning-border rounded-xl"
            role="status"
            aria-live="polite"
            data-testid="learning-loops-backend-unavailable"
          >
            <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <p className="text-sm text-status-warning">
              Não foi possível carregar configurações salvas. Exibindo defaults da plataforma — recarregue em alguns instantes.
            </p>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}

        <div className={`space-y-2 ${isLoading ? "pointer-events-none" : ""}`}>
          {SUB_TOGGLE_DEFS.map((def) => (
            <ToggleCard
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
