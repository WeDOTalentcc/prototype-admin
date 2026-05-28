export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import { resolveCompanyId } from '@/lib/api/resolve-company-id'
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const companyId = await resolveCompanyId(request)
    if (!companyId) {
      return NextResponse.json({ error: 'Company ID não disponível' }, { status: 401 })
    }
    const backendUrl = `${BACKEND_URL}/api/v1/company-hiring-policy/${companyId}`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(request),
      signal: AbortSignal.timeout(8000),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar politicas', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    // T-1171: backend retorna envelope canônico {ok, data, meta} — unwrap
    // para o frontend que espera o objeto raw. Sem isso, hiringPolicy.pipeline_rules
    // fica undefined e a UI renderiza "Não definido" em todos os campos.
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

const _bodySchema = z.record(z.string(), z.unknown())

export async function PUT(request: NextRequest) {
  try {
    const companyId = await resolveCompanyId(request)
    if (!companyId) {
      return NextResponse.json({ error: 'Company ID não disponível' }, { status: 401 })
    }
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const backendUrl = `${BACKEND_URL}/api/v1/company-hiring-policy/${companyId}`

    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: getAuthHeaders(request),
      signal: AbortSignal.timeout(8000),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar politicas', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    // T-1171: unwrap envelope canonico {ok, data, meta} do FastAPI
    const unwrapped = data && typeof data === "object" && "ok" in data && "data" in data ? (data as Record<string, unknown>).data : data
    return NextResponse.json(unwrapped)
  } catch {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
