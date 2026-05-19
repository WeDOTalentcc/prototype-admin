export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { unwrapEnvelopeSuccess, unwrapEnvelopeError } from '@/lib/api/unwrapEnvelope'

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
        // T-1167 addendum #2 — backend envelopa erros em
        // `{error:true, status_code:422, message:<detail original>}`.
        // Antes esse desembrulho só lidava com `.detail` mas não com `.message`
        // do envelope global, então o hook recebia o envelope cru e o branch
        // "200 OK + setEvaluation success=false" não disparava (status era 422,
        // mas o conteúdo do detail ficava aninhado sob message). Agora
        // `unwrapEnvelopeError` devolve `{detail: <inner>}` e a normalização
        // canônica abaixo extrai o detail real (com score/band/indicators).
        const unwrapped = unwrapEnvelopeError(raw)
        const payload = (unwrapped && typeof unwrapped === 'object' && 'detail' in (unwrapped as Record<string, unknown>)
          && typeof (unwrapped as Record<string, unknown>).detail === 'object'
          && (unwrapped as Record<string, unknown>).detail !== null
          && !Array.isArray((unwrapped as Record<string, unknown>).detail))
          ? (unwrapped as Record<string, unknown>).detail
          : unwrapped
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
      // T-1167 addendum #2 — unwrap envelope de erro do FastAPI também aqui.
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

    // T-1167 addendum #2 — unwrap envelope de SUCESSO do FastAPI
    // (`ResponseEnvelopeMiddleware` envelopa em `{ok:true, data:..., meta:{}}`)
    // para o hook receber `{success, score, band, indicators}` direto, em vez de
    // logar "success=false" porque procurava `data.success` no topo do envelope.
    const data = await response.json()
    return NextResponse.json(unwrapEnvelopeSuccess(data))
  } catch (error) {
    console.error('[jd-evaluate] proxy error:', error)
    return NextResponse.json(
      { success: false, error: 'Proxy connection error' },
      { status: 500 }
    )
  }
}
