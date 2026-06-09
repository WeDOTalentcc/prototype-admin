"use client"

import { useState, useEffect, useCallback } from 'react'

export interface CompanyUser {
  id: string
  name: string
  email: string
  role: string
  isActive: boolean
}

interface UseCompanyRecruitersResult {
  recruiters: CompanyUser[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

/**
 * Hook canonical para listar recrutadores da empresa (papel recruiter/recrutador).
 *
 * Fonte: GET /api/backend-proxy/company/users (mesmo endpoint que useCompanyManagers).
 * Filtra por papéis que indicam recrutamento: recruiter, recrutador, talent, rh, hr.
 * Retorna shape mínimo: id + name para uso em filtros da lista de vagas.
 */
export function useCompanyRecruiters(): UseCompanyRecruitersResult {
  const [recruiters, setRecruiters] = useState<CompanyUser[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchRecruiters = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/backend-proxy/company/users')
      if (!res.ok) {
        if (res.status === 404) {
          setRecruiters([])
          return
        }
        throw new Error(`Failed to fetch users: ${res.status}`)
      }
      const data = await res.json()
      const users: Record<string, unknown>[] = Array.isArray(data) ? data : data?.items ?? []

      const recruiterRoles = ['recruiter', 'recrutador', 'talent', 'rh', 'hr', 'people', 'acquisition']

      const filtered: CompanyUser[] = users
        .filter((u) => {
          const active = u.is_active !== false
          const role = String(u.role ?? '').toLowerCase()
          const isRecruiterRole = recruiterRoles.some((r) => role.includes(r))
          return active && isRecruiterRole
        })
        .map((u) => ({
          id: String(u.id ?? ''),
          name: String(u.name ?? u.full_name ?? u.email ?? ''),
          email: String(u.email ?? ''),
          role: String(u.role ?? ''),
          isActive: u.is_active !== false,
        }))
        .filter((u) => u.id && u.name)

      setRecruiters(filtered)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setRecruiters([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchRecruiters()
  }, [fetchRecruiters])

  return { recruiters, isLoading, error, refetch: fetchRecruiters }
}
