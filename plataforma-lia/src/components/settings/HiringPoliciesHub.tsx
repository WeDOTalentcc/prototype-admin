"use client"

/**
 * HiringPoliciesHub — Políticas de Recrutamento (SÓ gates tipados).
 *
 * P1 dedup: superfície estruturada canônica (bloco "policy" via MinhaEmpresaCard).
 * V2.2 (2026-06-01): a seção "Instruções para a LIA" (texto livre) saiu daqui e
 * foi para LIA & Personalização → Instruções por Campo → grupo "Processo"
 * (PolicyInstructionsGroup). Aqui ficam apenas as REGRAS tipadas (gates).
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
  if (loading) return <HubLoadingState message="Carregando políticas de recrutamento..." />
  if (!policyBlock) return <HubErrorState message="Bloco de políticas não encontrado. Tente recarregar." onRetry={refreshAll} />

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
          description="Regras tipadas que a LIA aplica no processo: triagem, aprovação, agendamento e automação. (Instruções de texto livre ficam em LIA & Personalização → Instruções por Campo.)"
        >
          <div className="flex items-center gap-3">
            <SettingsEditModeToggle hubId="politicas-recrutamento" />
            <button onClick={refreshAll} className="p-1.5 rounded-md hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none" aria-label="Recarregar dados">
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
