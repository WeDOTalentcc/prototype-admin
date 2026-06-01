"use client"

/**
 * HiringPoliciesHub — Regras tipadas de recrutamento (gates).
 *
 * V4 (2026-06-01): renderizado como aba "Regras" dentro do hub único
 * "Comportamento da LIA" (LiaPersonalizacaoHub). Quando `embedded`, omite o
 * HubHeader próprio (o hub-pai já tem cabeçalho) e mostra só uma toolbar slim.
 * Deixou de ser item separado "Políticas de Recrutamento" no menu.
 *
 * Conteúdo: bloco "policy" estruturado (toggle/number/select) via MinhaEmpresaCard.
 * Instruções de texto livre vivem na aba "Instruções por Campo" (V2.2).
 */

import React from "react"
import { FileText, RefreshCw } from "lucide-react"
import { useCompanySettingsCards } from "@/hooks/settings/use-company-settings-cards"
import { MinhaEmpresaCard } from "@/components/settings/MinhaEmpresaCard"
import { HubHeader, HubLoadingState, HubErrorState } from "./_shared"
import { SettingsEditModeToggle } from "@/components/settings/SettingsEditModeToggle"
import { useSettingsEditMode } from "@/hooks/settings/useSettingsEditMode"

export function HiringPoliciesHub({ embedded = false }: { embedded?: boolean } = {}) {
  // ─── TODOS OS HOOKS PRIMEIRO (rules-of-hooks, CLAUDE.md) ───
  const {
    blocks, benefits, companyId, loading, error,
    recentlyUpdated, editingField, isSavingField,
    startEditing, cancelEditing, saveField, refreshAll, watchdogError,
  } = useCompanySettingsCards()

  const [isExpanded, setIsExpanded] = React.useState(true)
  const { isEditing } = useSettingsEditMode("politicas-recrutamento")

  const policyBlock = React.useMemo(() => blocks.find((b) => b.key === "policy"), [blocks])

  React.useEffect(() => {
    if (typeof window === "undefined") return
    const handler = () => refreshAll()
    window.addEventListener("lia:settings-updated", handler)
    return () => window.removeEventListener("lia:settings-updated", handler)
  }, [refreshAll])

  // ─── EARLY RETURNS — APÓS TODOS OS HOOKS ───
  if (watchdogError) return <HubErrorState message={watchdogError} onRetry={refreshAll} />
  if (loading) return <HubLoadingState message="Carregando regras de recrutamento..." />
  if (!policyBlock) return <HubErrorState message="Bloco de políticas não encontrado. Tente recarregar." onRetry={refreshAll} />

  const toolbar = (
    <div className="flex items-center gap-3">
      <SettingsEditModeToggle hubId="politicas-recrutamento" />
      <button onClick={refreshAll} className="p-1.5 rounded-md hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none" aria-label="Recarregar dados">
        <RefreshCw className="w-4 h-4 text-lia-text-secondary" />
      </button>
    </div>
  )

  return (
    <div className="flex flex-col h-full space-y-4">
      {error && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm bg-status-error/10 text-status-error border border-status-error/30">
          <span>{error}</span>
        </div>
      )}

      {embedded ? (
        <div className="flex items-start justify-between gap-3">
          <p className="text-sm text-lia-text-secondary leading-relaxed">
            Regras tipadas que a LIA aplica no processo: triagem, aprovação, agendamento e automação.
          </p>
          {toolbar}
        </div>
      ) : (
        <div>
          <HubHeader
            title="Políticas de Recrutamento"
            description="Regras tipadas que a LIA aplica no processo: triagem, aprovação, agendamento e automação."
          >
            {toolbar}
          </HubHeader>
        </div>
      )}

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
