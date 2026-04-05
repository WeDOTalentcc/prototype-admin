"use client"

import { useState, useEffect, useCallback, useRef } from "react"

export interface TenantInfo {
  companyId: string
  clientAccountId: string | null
  companyProfileId: string | null
  companyName: string | null
  planId: string | null
  status: string | null
}

interface UseCompanyIdResult {
  companyId: string | null
  tenantInfo: TenantInfo | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

let cachedTenantInfo: TenantInfo | null = null
let cachePromise: Promise<TenantInfo | null> | null = null
let cacheTimestamp = 0
const CACHE_TTL_MS = 5 * 60 * 1000

async function fetchTenantInfo(): Promise<TenantInfo | null> {
  const now = Date.now()
  if (cachedTenantInfo && now - cacheTimestamp < CACHE_TTL_MS) {
    return cachedTenantInfo
  }

  if (cachePromise) {
    return cachePromise
  }

  cachePromise = (async () => {
    try {
      let organizationId: string | null = null

      const sessionRes = await fetch("/api/auth/workos/session", {
        credentials: "include",
      })
      if (sessionRes.ok) {
        const sessionData = await sessionRes.json()
        if (sessionData.authenticated && sessionData.user) {
          organizationId = sessionData.user.organizationId
        }
      }

      const resolveParams = organizationId
        ? `workos_organization_id=${encodeURIComponent(organizationId)}`
        : ''

      const resolveRes = await fetch(
        `/api/backend-proxy/company/resolve-tenant${resolveParams ? `?${resolveParams}` : ''}`
      )

      if (resolveRes.ok) {
        const data = await resolveRes.json()
        if (data.company_profile_id) {
          cachedTenantInfo = {
            companyId: data.company_profile_id,
            clientAccountId: data.client_account_id || null,
            companyProfileId: data.company_profile_id,
            companyName: data.company_name || null,
            planId: data.plan_id || null,
            status: data.status || null,
          }
          cacheTimestamp = Date.now()
          return cachedTenantInfo
        }
      }

      const jwtSessionRes = await fetch("/api/auth/session", {
        credentials: "include",
      })
      if (jwtSessionRes.ok) {
        const jwtData = await jwtSessionRes.json()
        if (jwtData.user?.company_id) {
          cachedTenantInfo = {
            companyId: jwtData.user.company_id,
            clientAccountId: null,
            companyProfileId: jwtData.user.company_id,
            companyName: jwtData.user.company || null,
            planId: null,
            status: null,
          }
          cacheTimestamp = Date.now()
          return cachedTenantInfo
        }
      }

      return null
    } catch {
      return null
    } finally {
      cachePromise = null
    }
  })()

  return cachePromise
}

export function invalidateCompanyIdCache() {
  cachedTenantInfo = null
  cacheTimestamp = 0
  cachePromise = null
}

export function useCompanyId(): UseCompanyIdResult {
  const [tenantInfo, setTenantInfo] = useState<TenantInfo | null>(cachedTenantInfo)
  const [isLoading, setIsLoading] = useState(!cachedTenantInfo)
  const [error, setError] = useState<string | null>(null)
  const mountedRef = useRef(true)

  const refetch = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    invalidateCompanyIdCache()

    try {
      const info = await fetchTenantInfo()
      if (mountedRef.current) {
        setTenantInfo(info)
        if (!info) {
          setError("Could not resolve company ID from session")
        }
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : "Failed to resolve company ID")
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false)
      }
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true

    const load = async () => {
      try {
        const info = await fetchTenantInfo()
        if (mountedRef.current) {
          setTenantInfo(info)
          if (!info) {
            setError("Could not resolve company ID from session")
          }
          setIsLoading(false)
        }
      } catch (err) {
        if (mountedRef.current) {
          setError(err instanceof Error ? err.message : "Failed to resolve company ID")
          setIsLoading(false)
        }
      }
    }

    load()

    return () => {
      mountedRef.current = false
    }
  }, [])

  return {
    companyId: tenantInfo?.companyId ?? null,
    tenantInfo,
    isLoading,
    error,
    refetch,
  }
}

export default useCompanyId
