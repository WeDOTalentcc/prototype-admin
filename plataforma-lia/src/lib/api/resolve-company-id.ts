import { NextRequest } from 'next/server'
import { cookies } from 'next/headers'
import { verifyAndDecodeSession } from '@/lib/session-crypto'

const IS_DEVELOPMENT = process.env.NODE_ENV === 'development'
const DEV_FALLBACK_COMPANY = process.env.DEV_FALLBACK_COMPANY_ID || 'dev_company'
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const TENANT_CACHE_TTL_MS = 5 * 60 * 1000
const tenantCache = new Map<string, { value: string; ts: number }>()

async function resolveTenantFromBackend(workosOrgId: string): Promise<string | null> {
  const cached = tenantCache.get(workosOrgId)
  const now = Date.now()
  if (cached && now - cached.ts < TENANT_CACHE_TTL_MS) {
    return cached.value
  }
  try {
    const url = `${BACKEND_URL}/api/v1/company/resolve-tenant?workos_organization_id=${encodeURIComponent(workosOrgId)}`
    const res = await fetch(url, { cache: 'no-store' })
    if (!res.ok) return null
    const data = (await res.json()) as { company_profile_id?: string | null }
    const cid = data?.company_profile_id || null
    if (cid) {
      tenantCache.set(workosOrgId, { value: cid, ts: now })
      return cid
    }
  } catch {
    // ignore
  }
  return null
}

export async function resolveCompanyId(request: NextRequest): Promise<string | null> {
  const fromQuery = request.nextUrl.searchParams.get('company_id')
  if (fromQuery && fromQuery.trim()) return fromQuery.trim()

  try {
    const cookieStore = await cookies()
    const session = cookieStore.get('workos_session')
    if (session) {
      const data = verifyAndDecodeSession(session.value)
      const orgId = data?.workosProfile?.organizationId
      if (orgId) {
        const resolved = await resolveTenantFromBackend(orgId)
        if (resolved) return resolved
      }
    }
  } catch {
    // ignore
  }

  if (IS_DEVELOPMENT) return DEV_FALLBACK_COMPANY
  return null
}
