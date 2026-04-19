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

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const params = new URLSearchParams()
  searchParams.forEach((v, k) => params.set(k, v))

  const authHeaders = await getAuthHeaders(req)
  const upstream = `${FASTAPI_BASE}/api/v1/rh/lgpd-requests?${params}`

  try {
    const res = await fetch(upstream, {
      headers: { 'Content-Type': 'application/json', ...authHeaders },
      cache: 'no-store',
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    return NextResponse.json({ error: 'Upstream error' }, { status: 502 })
  }
}

export async function PATCH(req: NextRequest) {
  const body = await req.json().catch(() => ({}))
  const authHeaders = await getAuthHeaders(req)

  const pathParts = req.nextUrl.pathname.split('/')
  const requestId = pathParts[pathParts.indexOf('lgpd-requests') + 1]

  try {
    const res = await fetch(
      `${FASTAPI_BASE}/api/v1/rh/lgpd-requests/${requestId}/respond`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', ...authHeaders },
        body: JSON.stringify(body),
        cache: 'no-store',
      }
    )
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    return NextResponse.json({ error: 'Upstream error' }, { status: 502 })
  }
}
