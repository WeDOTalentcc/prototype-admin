export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { resolveCompanyId } from '@/lib/api/resolve-company-id'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function POST(request: NextRequest) {
  try {
    const companyId = await resolveCompanyId(request)
    if (!companyId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    let body: unknown = {}
    try { body = await request.json() } catch { /* empty body ok */ }

    const url = `${BACKEND_URL}/api/v1/experience-highlights/generate?company_id=${encodeURIComponent(companyId)}`
    const response = await fetch(url, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(60_000),
    })

    const text = await response.text()
    if (!response.ok) {
      return new NextResponse(text || JSON.stringify({ error: 'Upstream error' }), {
        status: response.status,
        headers: { 'Content-Type': 'application/json' },
      })
    }
    return new NextResponse(text, {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  } catch (error) {
    return NextResponse.json({ error: 'Failed to generate highlight' }, { status: 500 })
  }
}
