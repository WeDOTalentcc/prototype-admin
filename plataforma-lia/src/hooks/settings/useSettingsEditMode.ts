"use client"

/**
 * useSettingsEditMode — P2-2 Sprint B.4 read-only/edit toggle.
 *
 * Hook canonical que combina:
 *   1. RBAC permission (canEditHub) — backend authoritative
 *   2. Local toggle state (localStorage) — UX preference per user
 *
 * Default behavior:
 *   - Se role NÃO pode editar → readOnly forçado (RBAC vence)
 *   - Se role PODE editar → respeita localStorage toggle
 *   - Default toggle = "edit" (legacy behavior preservado)
 *
 * Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md Sprint B.4
 */

import { useCallback, useEffect, useState } from "react"
import { canEditHub } from "@/lib/settings/settings-rbac"
import { useAuth } from "@/contexts/auth-context"

const STORAGE_KEY = "lia-settings-edit-mode"

export interface SettingsEditMode {
  /** True = inputs habilitados, salvar visível. False = read-only. */
  isEditing: boolean
  /** True se RBAC permite. False = bloqueio total (toggle não aparece). */
  canToggle: boolean
  /** Alterna estado (no-op se canToggle=false). */
  toggleEditMode: () => void
  /** Força modo (read-only ou edit). */
  setEditMode: (editing: boolean) => void
}

export function useSettingsEditMode(hubId: string): SettingsEditMode {
  const { user } = useAuth()
  const userRole = (user && "role" in user ? user.role : null) ?? null
  const canToggle = canEditHub(hubId, userRole)

  // Inicia em "edit" por default (legacy). Read-only é opt-in via UX.
  const [isEditingState, setIsEditingState] = useState<boolean>(() => {
    if (typeof window === "undefined") return true
    const stored = window.localStorage.getItem(STORAGE_KEY)
    return stored === null ? true : stored === "true"
  })

  // RBAC override: se não pode editar, força isEditing=false (computed)
  const isEditing = canToggle ? isEditingState : false

  const toggleEditMode = useCallback(() => {
    if (!canToggle) return
    setIsEditingState((prev) => {
      const next = !prev
      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, String(next))
      }
      return next
    })
  }, [canToggle])

  const setEditMode = useCallback((editing: boolean) => {
    if (!canToggle) return
    setIsEditingState(editing)
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, String(editing))
    }
  }, [canToggle])

  return {
    isEditing,
    canToggle,
    toggleEditMode,
    setEditMode,
  }
}
