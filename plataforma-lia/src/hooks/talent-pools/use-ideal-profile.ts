"use client"

/**
 * useIdealProfile — hook canonical para fetch de IdealProfile por id.
 *
 * Sprint 4 v3 (2026-05-25): introduzido para o SourcingTab pré-popular
 * inputs a partir do arquétipo vinculado ao pool. Recrutador edita
 * manualmente se quiser refinar.
 *
 * Endpoint canonical:
 *   GET /api/backend-proxy/company/ideal-profiles/:profileId
 *
 * Defensive: aceita `profileId=null` (pool sem arquétipo) → retorna
 * `data=null` sem chamar fetch.
 *
 * Shape do retorno alinhado com `lia-agent-system/app/schemas/company.py`
 * (`IdealProfileResponse`). Só os campos consumidos pelo SourcingTab são
 * tipados aqui — extender quando outras telas precisarem.
 */
import useSWR from "swr"

export interface IdealProfile {
  id: string
  name: string
  description: string | null
  role_type: string | null
  seniority_level: string | null
  mandatory_skills: string[]
  preferred_skills: string[]
  technical_requirements?: Record<string, unknown>
  is_active: boolean
}

interface UseIdealProfileReturn {
  data: IdealProfile | null
  isLoading: boolean
  error: Error | null
}

const fetcher = async (url: string): Promise<IdealProfile> => {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`Failed to load ideal profile: ${res.status}`)
  }
  return res.json()
}

export function useIdealProfile(profileId: string | null): UseIdealProfileReturn {
  const { data, error, isLoading } = useSWR<IdealProfile>(
    profileId ? `/api/backend-proxy/company/ideal-profiles/${profileId}` : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    }
  )

  return {
    data: data ?? null,
    isLoading,
    error: error ?? null,
  }
}
