import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

// R-020 P0-A: replaced next-auth (not installed) with canonical getAuthHeaders
const FASTAPI_BASE = process.env.FASTAPI_URL || process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const params = new URLSearchParams()
  searchParams.forEach((v, k) => params.set(k, v))

  const authHeaders = getAuthHeaders(req)
  const upstream = `${FASTAPI_BASE}/api/v1/rh/lgpd-requests?${params}`

  try {
    const res = await fetch(upstream, {
      headers: { ...authHeaders },
      cache: 'no-store',
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch {
    return NextResponse.json({ error: 'Upstream error' }, { status: 502 })
  }
}

export async function PATCH(req: NextRequest) {
  const body = await req.json().catch(() => ({}))
  const authHeaders = getAuthHeaders(req)

  const pathParts = req.nextUrl.pathname.split('/')
  const requestId = pathParts[pathParts.indexOf('lgpd-requests') + 1]

  try {
    const res = await fetch(
      `${FASTAPI_BASE}/api/v1/rh/lgpd-requests/${requestId}/respond`,
      {
        method: 'PATCH',
        headers: { ...authHeaders },
        body: JSON.stringify(body),
        cache: 'no-store',
      }
    )
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch {
    return NextResponse.json({ error: 'Upstream error' }, { status: 502 })
  }
}
