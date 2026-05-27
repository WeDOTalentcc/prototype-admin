/**
 * use-company-settings-cards.ts — thin wrapper (Sprint 2.2 refactor, 2026-05-26)
 *
 * Antes: 807 LOC monolith (fetch + transform + UI state + mutations + broadcast).
 * Agora: ~180 LOC coordinator que compõe:
 *   - React Query queries para fetch paralelo de dados
 *   - useCompanyBlocks (pure transform)
 *   - useFieldSave (React Query mutations)
 *   - useSettingsBroadcast (event listener)
 *
 * API pública INALTERADA — consumidores (MinhaEmpresaHub, MinhaEmpresaCard)
 * não precisam de qualquer mudança.
 */

"use client"

import { useState, useEffect, useCallback, useRef, useMemo } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useLiaChatContext } from "@/contexts/lia-float-context"
import { useLoadingWatchdog } from "@/hooks/shared/use-loading-watchdog"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import type { CompanyData } from "@/hooks/settings/department-types"
import {
  useCompanyBlocks,
  mergeToCompanyData,
  snapshotFieldValues,
  type CardBlock,
  type BenefitItem,
  type HiringPolicyData,
} from "@/hooks/settings/useCompanyBlocks"
import { useFieldSave, type SaveFieldArgs } from "@/hooks/settings/useFieldSave"
import { useSettingsBroadcast, SETTINGS_QUERY_KEYS } from "@/hooks/settings/useSettingsBroadcast"

// ─── Re-export types for backward compat ────────────────────────────────────
export type { BlockProgress, CardBlock, CardField, BenefitItem, HiringPolicyData } from "@/hooks/settings/useCompanyBlocks"

// ─── Fetch functions ─────────────────────────────────────────────────────────

async function fetchCompanyProfile(): Promise<Record<string, unknown> | null> {
  const res = await fetch("/api/backend-proxy/company/profile")
  if (res.ok) return res.json()
  if (res.status === 404) {
    try {
      const body = await res.json()
      if (body?.detail?.code === "COMPANY_PROFILE_NOT_FOUND" && typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("lia:onboarding-required", {
            detail: {
              hintRoute: body.detail.hint_route ?? "/configuracoes/minha-empresa",
              message: body.detail.message,
            },
          }),
        )
      }
    } catch { /* non-JSON 404 */ }
    return null
  }
  console.error("[useCompanySettingsCards] fetchCompanyProfile HTTP", res.status)
  return null
}

async function fetchCultureProfile(companyId: string): Promise<Record<string, unknown> | null> {
  const res = await fetch(`/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`)
  if (res.ok) return res.json()
  if (res.status !== 404) {
    console.error("[useCompanySettingsCards] fetchCultureProfile HTTP", res.status)
  }
  return null
}

async function fetchBenefits(companyId: string): Promise<BenefitItem[]> {
  const res = await fetch(`/api/backend-proxy/company/benefits/?company_id=${encodeURIComponent(companyId)}`)
  if (res.ok) {
    const data = await res.json()
    return Array.isArray(data) ? data : (data.items || [])
  }
  console.error("[useCompanySettingsCards] fetchBenefits HTTP", res.status)
  return []
}

async function fetchHiringPolicy(): Promise<HiringPolicyData | null> {
  const res = await fetch("/api/backend-proxy/hiring-policy")
  if (res.ok) return res.json()
  if (res.status !== 404) {
    console.error("[useCompanySettingsCards] fetchHiringPolicy HTTP", res.status)
  }
  return null
}

async function fetchSettingsProgress(): Promise<number> {
  const res = await fetch("/api/backend-proxy/settings/progress/")
  if (res.ok) {
    const data = await res.json()
    return data.overall ?? 0
  }
  console.error("[useCompanySettingsCards] fetchSettingsProgress HTTP", res.status)
  return 0
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export function useCompanySettingsCards() {
  const { tenantInfo } = useCompanyId()
  const { switchChatContext } = useLiaChatContext()
  const queryClient = useQueryClient()

  // ── React Query data layer (parallel fetches) ──
  const profileQuery = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.companyProfile(),
    queryFn: fetchCompanyProfile,
    staleTime: 30_000,
  })

  const rawProfile = profileQuery.data ?? null
  const companyId: string | null = (rawProfile?.id as string) ?? (tenantInfo?.clientAccountId ?? null)
  const apiCompanyId = companyId ?? ""

  const cultureQuery = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.cultureProfile(apiCompanyId),
    queryFn: () => fetchCultureProfile(apiCompanyId),
    enabled: !!apiCompanyId,
    staleTime: 30_000,
  })

  const benefitsQuery = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.benefits(apiCompanyId),
    queryFn: () => fetchBenefits(apiCompanyId),
    enabled: !!apiCompanyId,
    staleTime: 30_000,
  })

  const hiringPolicyQuery = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.hiringPolicy(),
    queryFn: fetchHiringPolicy,
    staleTime: 30_000,
  })

  const progressQuery = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.settingsProgress(),
    queryFn: fetchSettingsProgress,
    staleTime: 15_000,
  })

  // ── Derived state ──
  const loading = profileQuery.isLoading || cultureQuery.isLoading || benefitsQuery.isLoading || hiringPolicyQuery.isLoading
  const error = (profileQuery.error || cultureQuery.error || benefitsQuery.error || hiringPolicyQuery.error)?.message ?? null
  const overallProgress = progressQuery.data ?? 0
  const rawCulture = cultureQuery.data ?? null
  const benefits: BenefitItem[] = benefitsQuery.data ?? []
  const hiringPolicy: HiringPolicyData | null = hiringPolicyQuery.data ?? null

  // ── Merge profile + culture into CompanyData (pure fn in useCompanyBlocks) ──
  const companyData = mergeToCompanyData(rawProfile, rawCulture)

  // ── Pure block transform ──
  const blocks: CardBlock[] = useCompanyBlocks(companyData, benefits, hiringPolicy)

  // ── Recently-updated visual indicator ──
  const [recentlyUpdated, setRecentlyUpdated] = useState<Set<string>>(new Set())
  const prevFieldSnapshotRef = useRef<Map<string, string>>(new Map())
  // Ref for companyData: avoids capturing the entire object in useCallback deps
  const companyDataRef = useRef<typeof companyData>(companyData)
  companyDataRef.current = companyData
  useEffect(() => {
    if (blocks.length === 0) return
    const currentSnapshot = snapshotFieldValues(blocks)
    const prevSnapshot = prevFieldSnapshotRef.current
    if (prevSnapshot.size > 0) {
      const changedKeys = new Set<string>()
      for (const [key, val] of currentSnapshot) {
        if (prevSnapshot.get(key) !== val) changedKeys.add(key)
      }
      if (changedKeys.size > 0) {
        setRecentlyUpdated(changedKeys)
        setTimeout(() => setRecentlyUpdated(new Set()), 2500)
      }
    }
    prevFieldSnapshotRef.current = currentSnapshot
  }, [blocks])

  // ── Chat context ──
  useEffect(() => {
    switchChatContext("settings_config", { continuePrevious: true })
    return () => { switchChatContext("general", { continuePrevious: true }) }
  }, [switchChatContext])

  // ── External settings event listener (replaces lastSelfDispatchRef hack) ──
  useSettingsBroadcast()

  // ── Loading watchdog ──
  const [watchdogError, setWatchdogError] = useState<string | null>(null)
  useLoadingWatchdog(loading, () => setWatchdogError("Tempo limite de carregamento excedido"), 8_000)

  // ── UI state ──
  const [expandedBlocks, setExpandedBlocks] = useState<Set<string>>(new Set(["basic"]))
  const [editingField, setEditingField] = useState<{ block: string; field: string } | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const toggleBlock = useCallback((blockKey: string) => {
    setExpandedBlocks(prev => {
      const next = new Set(prev)
      if (next.has(blockKey)) { next.delete(blockKey) } else { next.add(blockKey) }
      return next
    })
  }, [])

  const startEditing = useCallback((block: string, field: string) => {
    setEditingField({ block, field })
  }, [])

  const cancelEditing = useCallback(() => setEditingField(null), [])

  // ── Mutations ──
  const { saveField: saveMutation, isSavingField } = useFieldSave()

  const saveField = useCallback(
    async (block: string, field: string, value: unknown) => {
      if (!companyId) return
      const args: SaveFieldArgs = { block, field, value, companyId, companyData: companyDataRef.current }
      await saveMutation(args)
      setSuccessMessage("Campo atualizado com sucesso!")
      setTimeout(() => setSuccessMessage(null), 3000)
      setEditingField(null)
    },
    [companyId, saveMutation],
  )

  const refreshAll = useCallback(() => {
    setWatchdogError(null)
    queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.companyProfile() })
    queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.hiringPolicy() })
    queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.settingsProgress() })
    queryClient.invalidateQueries({ queryKey: ["culture-profile"] })
    queryClient.invalidateQueries({ queryKey: ["company-benefits"] })
  }, [queryClient])

  return {
    blocks,
    loading,
    error: error ?? watchdogError,
    watchdogError,
    successMessage,
    overallProgress,
    expandedBlocks,
    recentlyUpdated,
    editingField,
    isSavingField,
    benefits,
    companyId,
    toggleBlock,
    startEditing,
    cancelEditing,
    saveField,
    refreshAll,
  }
}
