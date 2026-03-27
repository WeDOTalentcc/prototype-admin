import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

// GET /api/backend-proxy/early-warning?company_id=<uuid>&min_risk_level=medium
// Proxies to: GET /api/v1/early-warning?company_id=<uuid>&min_risk_level=medium
// Returns: { summary: { total, by_risk_level, top_critical, top_high }, data: [...] }
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const companyId = searchParams.get('company_id')
    const minRiskLevel = searchParams.get('min_risk_level') || 'medium'

    if (!companyId) {
      return NextResponse.json({ error: 'company_id é obrigatório' }, { status: 422 })
    }

    const url = new URL(`${BACKEND_URL}/api/v1/early-warning`)
    url.searchParams.set('company_id', companyId)
    url.searchParams.set('min_risk_level', minRiskLevel)

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao calcular Early Warning Score' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao calcular Early Warning Score' },
      { status: 500 }
    )
  }
}
