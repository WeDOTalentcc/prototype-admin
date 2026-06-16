export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import { unwrapEnvelopeSuccess, unwrapEnvelopeError } from '@/lib/api/unwrapEnvelope'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data

    const response = await fetch(`${BACKEND_URL}/api/v1/skills-catalog/wizard/suggest-skills`, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      // T-1167 addendum #2 — unwrap envelope de erro do FastAPI
      // (ResponseEnvelopeMiddleware) antes de devolver para o hook.
      const errText = await response.text().catch(() => '')
      try {
        const parsed = JSON.parse(errText)
        return NextResponse.json(unwrapEnvelopeError(parsed), { status: response.status })
      } catch {
        return NextResponse.json(
          { detail: { message: errText.slice(0, 200) || 'Failed to suggest skills' } },
          { status: response.status }
        )
      }
    }

    // T-1167 addendum #2 — unwrap envelope de SUCESSO do FastAPI; o hook
    // useJDEvaluation/SkillsPanel espera `technical_skills` / `behavioral_competencies`
    // no topo, não dentro de `data.data`.
    const data = await response.json()
    return NextResponse.json(unwrapEnvelopeSuccess(data))
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Proxy connection error' },
      { status: 500 }
    )
  }
}
