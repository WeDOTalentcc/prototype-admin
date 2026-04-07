export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

// GET /api/backend-proxy/pipeline-prediction?vacancy_id=<uuid>&company_id=<uuid>
// → Previsão individual de uma vaga
//
// GET /api/backend-proxy/pipeline-prediction?company_id=<uuid>
// → Visão geral de todas as vagas ativas (sem vacancy_id)
//
// Proxies to:
//   GET /api/v1/pipeline-prediction?vacancy_id=&company_id=
//   GET /api/v1/pipeline-prediction/company-overview?company_id=
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
      backendPath = `${BACKEND_URL}/api/v1/pipeline-prediction`
    } else {
      backendPath = `${BACKEND_URL}/api/v1/pipeline-prediction/company-overview`
    }

    const url = new URL(backendPath)
    url.searchParams.set('company_id', companyId)
    if (vacancyId) {
      url.searchParams.set('vacancy_id', vacancyId)
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao calcular previsão de fechamento' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao calcular previsão de fechamento' },
      { status: 500 }
    )
  }
}
