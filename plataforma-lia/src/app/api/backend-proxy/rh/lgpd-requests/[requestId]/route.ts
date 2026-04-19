import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'

const FASTAPI_BASE = process.env.FASTAPI_URL || 'http://localhost:8000'

async function getAuthHeaders(req: NextRequest): Promise<Record<string, string>> {
  const authHeader = req.headers.get('authorization')
  if (authHeader) return { Authorization: authHeader }
  try {
    const session = await getServerSession()
    if ((session as any)?.accessToken) {
      return { Authorization: `Bearer ${(session as any).accessToken}` }
    }
  } catch {}
  return {}
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: { requestId: string } }
) {
  const authHeaders = await getAuthHeaders(req)
  try {
    const res = await fetch(
      `${FASTAPI_BASE}/api/v1/rh/lgpd-requests/${params.requestId}/respond`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', ...authHeaders },
        cache: 'no-store',
      }
    )
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch {
    return NextResponse.json({ error: 'Upstream error' }, { status: 502 })
  }
}
