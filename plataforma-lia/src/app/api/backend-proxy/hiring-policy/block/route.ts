export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import { resolveCompanyId } from '@/lib/api/resolve-company-id'
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const _bodySchema = z.record(z.string(), z.unknown())

export async function PATCH(request: NextRequest) {
  try {
    const companyId = await resolveCompanyId(request)
    if (!companyId) {
      return NextResponse.json({ error: 'Company ID não disponível' }, { status: 401 })
    }
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const backendUrl = `${BACKEND_URL}/api/v1/company-hiring-policy/${companyId}/block`

    const response = await fetch(backendUrl, {
      method: 'PATCH',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar bloco', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    // T-1171: backend retorna envelope canônico {ok, data, meta} — unwrap
    // para que o frontend receba a row atualizada (mesmo shape do GET).
    const unwrapped = data && typeof data === 'object' && data.ok === true && 'data' in data
      ? data.data
      : data
    return NextResponse.json(unwrapped)
  } catch {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
