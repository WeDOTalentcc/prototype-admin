export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { unwrapEnvelopeSuccess, unwrapEnvelopeError } from '@/lib/api/unwrapEnvelope'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const _bodySchema = z.record(z.string(), z.unknown())

// T-1167 (Bug #3) — proxy para POST /api/v1/jd/extract no FastAPI.
// O endpoint backend reaproveita JDParserService.extract_requirements para
// preencher Responsabilidades / Skills / Competências a partir do JD colado
// no textarea de DESCRIÇÃO. Sem esse proxy, o fetch do frontend cai num
// catch-all desconhecido → 404 (causa do bug reportado pelo usuário).
export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response
    const body = bodyResult.data

    const authHeaders = getAuthHeaders(request) as Record<string, string>
    const headers: Record<string, string> = { ...authHeaders, 'Content-Type': 'application/json' }
    const companyHeader = request.headers.get('x-company-id')
    if (companyHeader) headers['x-company-id'] = companyHeader
    const cookieHeader = request.headers.get('cookie')
    if (cookieHeader) headers['cookie'] = cookieHeader

    const response = await fetch(`${BACKEND_URL}/api/v1/jd/extract`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      // T-1167 addendum #2 — unwrap envelope de erro do FastAPI
      // (ResponseEnvelopeMiddleware) para o frontend ver `{detail: {...}}`
      // canônico em vez de `{error:true, message:{...real...}}`.
      const errText = await response.text().catch(() => '')
      try {
        const parsed = JSON.parse(errText)
        return NextResponse.json(unwrapEnvelopeError(parsed), { status: response.status })
      } catch {
        return NextResponse.json(
          { detail: { message: errText.slice(0, 200) || `status ${response.status}` } },
          { status: response.status }
        )
      }
    }

    const data = await response.json()
    return NextResponse.json(unwrapEnvelopeSuccess(data))
  } catch {
    return NextResponse.json(
      { success: false, error: 'Proxy connection error' },
      { status: 500 }
    )
  }
}
