import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

// R-020 P0-A: replaced next-auth (not installed) with canonical getAuthHeaders
const FASTAPI_BASE = process.env.FASTAPI_URL || process.env.BACKEND_URL || 'http://localhost:8000'

export async function PATCH(
  req: NextRequest,
  { params }: { params: { requestId: string } }
) {
  const authHeaders = getAuthHeaders(req)
  try {
    const res = await fetch(
      `${FASTAPI_BASE}/api/v1/rh/lgpd-requests/${params.requestId}/respond`,
      {
        method: 'PATCH',
        headers: { ...authHeaders },
        cache: 'no-store',
      }
    )
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch {
    return NextResponse.json({ error: 'Upstream error' }, { status: 502 })
  }
}
