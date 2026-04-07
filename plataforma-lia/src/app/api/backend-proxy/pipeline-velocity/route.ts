export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

// GET /api/backend-proxy/pipeline-velocity?vacancy_id=<uuid>&company_id=<uuid>
// Proxies to: GET /api/v1/pipeline/velocity
// Returns per-stage velocity metrics: avg_days, median_days, max_days,
//   candidate_count, threshold_days, is_bottleneck, overall_health
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const vacancyId = searchParams.get('vacancy_id')
    const companyId = searchParams.get('company_id')

    const params = new URLSearchParams()
    if (vacancyId) params.set('vacancy_id', vacancyId)
    if (companyId) params.set('company_id', companyId)

    const query = params.toString() ? `?${params.toString()}` : ''

    const response = await fetch(
      `${BACKEND_URL}/api/v1/pipeline/velocity${query}`,
      {
        method: 'GET',
        headers: getAuthHeaders(request),
      }
    )

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao consultar métricas de velocidade do pipeline' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao consultar velocidade do pipeline' },
      { status: 500 }
    )
  }
}
