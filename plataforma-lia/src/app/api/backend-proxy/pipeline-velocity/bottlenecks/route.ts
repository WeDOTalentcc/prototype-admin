export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

// GET /api/backend-proxy/pipeline-velocity/bottlenecks?company_id=<uuid>
// Proxies to: GET /api/v1/pipeline/velocity/bottlenecks
// Returns list of candidates currently exceeding their stage time threshold
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const companyId = searchParams.get('company_id')

    if (!companyId) {
      return NextResponse.json({ error: 'company_id é obrigatório' }, { status: 400 })
    }

    const response = await fetch(
      `${BACKEND_URL}/api/v1/pipeline/velocity/bottlenecks?company_id=${companyId}`,
      {
        method: 'GET',
        headers: getAuthHeaders(request),
      }
    )

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao consultar candidatos em gargalo' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao consultar gargalos do pipeline' },
      { status: 500 }
    )
  }
}
