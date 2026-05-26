"use client"

/**
 * SettingsEditModeToggle — P2-2 Sprint B.4 UI.
 *
 * Toggle visual para alternar entre read-only e edit mode no settings panel.
 * Consome useSettingsEditMode hook (RBAC-aware).
 *
 * Não renderiza nada se RBAC não permite editar (canToggle=false) —
 * read-only forçado sem opção visível.
 *
 * Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md Sprint B.4
 */

import { Eye, Edit3 } from "lucide-react"
import { useSettingsEditMode } from "@/hooks/settings/useSettingsEditMode"

interface Props {
  hubId: string
  className?: string
}

export function SettingsEditModeToggle({ hubId, className = "" }: Props) {
  const { isEditing, canToggle, toggleEditMode } = useSettingsEditMode(hubId)

  if (!canToggle) return null

  return (
    <button
      type="button"
      onClick={toggleEditMode}
      data-testid="settings-edit-mode-toggle"
      aria-pressed={isEditing}
      aria-label={isEditing ? "Mudar para modo visualização" : "Mudar para modo edição"}
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md
        text-xs font-medium border transition-colors motion-reduce:transition-none
        ${isEditing
          ? "bg-wedo-cyan/10 text-wedo-cyan border-wedo-cyan/30"
          : "bg-lia-bg-secondary text-lia-text-secondary border-lia-border-default hover:bg-lia-bg-primary"
        }
        ${className}
      `}
    >
      {isEditing ? (
        <>
          <Edit3 className="w-3 h-3" aria-hidden="true" />
          Modo edição
        </>
      ) : (
        <>
          <Eye className="w-3 h-3" aria-hidden="true" />
          Modo visualização
        </>
      )}
    </button>
  )
}
