export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data

    // Task #1177 (addendum #1175): forward auth headers (Authorization /
    // cookies / X-Dev-Api-Key) so the FastAPI middleware can validate the
    // JWT. Without this the proxy hits the backend unauthenticated and gets
    // 401, surfacing as "[fetchEvaluation] backend error: 401" in the
    // browser console and breaking JD evaluation in the WSI flow.
    const authHeaders = getAuthHeaders(request) as Record<string, string>
    const headers: Record<string, string> = { ...authHeaders, 'Content-Type': 'application/json' }
    const companyHeader = request.headers.get('x-company-id')
    if (companyHeader) headers['x-company-id'] = companyHeader
    const cookieHeader = request.headers.get('cookie')
    if (cookieHeader) headers['cookie'] = cookieHeader

    const response = await fetch(`${BACKEND_URL}/api/v1/wsi/jd-evaluate`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })

    if (response.status === 422) {
      try {
        const raw = await response.json()
        // FastAPI wraps HTTPException detail in { "detail": {...} }
        // Normalize so the hook always receives a flat shape with score/band/indicators at top level
        const payload = (raw && typeof raw.detail === 'object' && raw.detail !== null && !Array.isArray(raw.detail))
          ? raw.detail
          : raw
        return NextResponse.json(payload, { status: 422 })
      } catch (parseErr) {
        console.error('[jd-evaluate] failed to parse 422 body:', parseErr)
        return NextResponse.json(
          { band: 'critico', band_label: 'Crítico', score: 0, max_score: 100, can_generate: false, indicators: [], lia_suggestion: 'JD com qualidade insuficiente para geração de perguntas WSI.' },
          { status: 422 }
        )
      }
    }

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: 'Failed to evaluate JD' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('[jd-evaluate] proxy error:', error)
    return NextResponse.json(
      { success: false, error: 'Proxy connection error' },
      { status: 500 }
    )
  }
}
