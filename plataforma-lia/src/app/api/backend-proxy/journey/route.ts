export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

// GET /api/backend-proxy/journey?vacancy_id=<uuid>&company_id=<uuid>
//   → GET /api/v1/journey/metrics (detailed funnel per vacancy)
//
// GET /api/backend-proxy/journey?company_id=<uuid>  (no vacancy_id)
//   → GET /api/v1/journey/company-overview (all open vacancies health)
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const companyId = searchParams.get('company_id')
    const vacancyId = searchParams.get('vacancy_id')

    if (!companyId) {
      return NextResponse.json({ error: 'company_id é obrigatório' }, { status: 400 })
    }

    let backendPath: string
    if (vacancyId) {
      const url = new URL(`${BACKEND_URL}/api/v1/journey/metrics`)
      url.searchParams.set('vacancy_id', vacancyId)
      url.searchParams.set('company_id', companyId)
      backendPath = url.toString()
    } else {
      const url = new URL(`${BACKEND_URL}/api/v1/journey/company-overview`)
      url.searchParams.set('company_id', companyId)
      backendPath = url.toString()
    }

    const response = await fetch(backendPath, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao buscar métricas de jornada' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao buscar métricas de jornada' },
      { status: 500 }
    )
  }
}
