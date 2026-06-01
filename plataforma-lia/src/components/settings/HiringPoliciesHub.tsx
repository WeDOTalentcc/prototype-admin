"use client"

/**
 * HiringPoliciesHub — Políticas de Recrutamento (superfície ESTRUTURADA canônica)
 *
 * P1 dedup (2026-06-01): substitui a versão narrativa (18 Textareas livres) por
 * controles TIPADOS, reusando o bloco "policy" de useCompanySettingsCards +
 * MinhaEmpresaCard. Motivo: os consumidores backend são gates tipados (bool/int)
 * e a UI narrativa gravava strings que o boundary P0.a agora rejeita (422).
 * Decisão "estruturado vence" (plano aprovado 2026-06-01).
 *
 * - Mesma fonte de dados (CompanyHiringPolicy) e mesmos editores inline de
 *   Minha Empresa — agora num único lugar canônico (grupo PROCESSO do menu).
 * - O bloco "policy" foi REMOVIDO de MinhaEmpresaHub para eliminar a duplicação.
 * - Os 14 campos narrativos-puros (screening_criteria, no_show_policy, D&I,
 *   data_retention, etc.) ficam deferidos ao P3, onde viram instruções da LIA
 *   (LiaFieldToggle.comment) — fora de slots de gate. Dado preservado no banco;
 *   a versão narrativa permanece no histórico git para reuso no P3.
 */

import React from "react"
import { FileText, RefreshCw } from "lucide-react"
import { useCompanySettingsCards } from "@/hooks/settings/use-company-settings-cards"
import { MinhaEmpresaCard } from "@/components/settings/MinhaEmpresaCard"
import { HubHeader, HubLoadingState, HubErrorState } from "./_shared"
import { SettingsEditModeToggle } from "@/components/settings/SettingsEditModeToggle"
import { useSettingsEditMode } from "@/hooks/settings/useSettingsEditMode"

export function HiringPoliciesHub() {
  // ─── TODOS OS HOOKS PRIMEIRO (rules-of-hooks, CLAUDE.md) ───
  const {
    blocks,
    benefits,
    companyId,
    loading,
    error,
    recentlyUpdated,
    editingField,
    isSavingField,
    startEditing,
    cancelEditing,
    saveField,
    refreshAll,
    watchdogError,
  } = useCompanySettingsCards()

  const [isExpanded, setIsExpanded] = React.useState(true)

  // RBAC edit-mode (P2): read-only por role; default editável para admin/recruiter.
  const { isEditing } = useSettingsEditMode("politicas-recrutamento")

  const policyBlock = React.useMemo(
    () => blocks.find((b) => b.key === "policy"),
    [blocks],
  )

  // Card no chat dispara `lia:settings-updated` ao salvar — re-fetch.
  React.useEffect(() => {
    if (typeof window === "undefined") return
    const handler = () => refreshAll()
    window.addEventListener("lia:settings-updated", handler)
    return () => window.removeEventListener("lia:settings-updated", handler)
  }, [refreshAll])

  // ─── EARLY RETURNS — APÓS TODOS OS HOOKS ───
  if (watchdogError) {
    return <HubErrorState message={watchdogError} onRetry={refreshAll} />
  }
  if (loading) {
    return <HubLoadingState message="Carregando políticas de recrutamento..." />
  }
  if (!policyBlock) {
    return (
      <HubErrorState
        message="Bloco de políticas não encontrado. Tente recarregar."
        onRetry={refreshAll}
      />
    )
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      {error && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm bg-status-error/10 text-status-error border border-status-error/30">
          <span>{error}</span>
        </div>
      )}

      <div>
        <HubHeader
          title="Políticas de Recrutamento"
          description="Regras de triagem, aprovação, agendamento e automação que a LIA aplica no processo seletivo."
        >
          <div className="flex items-center gap-3">
            <SettingsEditModeToggle hubId="politicas-recrutamento" />
            <button
              onClick={refreshAll}
              className="p-1.5 rounded-md hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
              aria-label="Recarregar dados"
            >
              <RefreshCw className="w-4 h-4 text-lia-text-secondary" />
            </button>
          </div>
        </HubHeader>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <MinhaEmpresaCard
          block={policyBlock}
          IconComp={FileText}
          isExpanded={isExpanded}
          recentlyUpdated={recentlyUpdated}
          editingField={editingField}
          isSavingField={isSavingField}
          benefits={benefits}
          companyId={companyId}
          isReadOnly={!isEditing}
          onBenefitsChanged={refreshAll}
          onLogoUploaded={refreshAll}
          onToggle={() => setIsExpanded((v) => !v)}
          onStartEditing={startEditing}
          onCancelEditing={cancelEditing}
          onSaveField={saveField}
        />
      </div>
    </div>
  )
}
