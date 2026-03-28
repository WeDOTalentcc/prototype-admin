import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

// GET /api/backend-proxy/recruiter-metrics/[recruiter_id]/benchmark?company_id=<uuid>
// Proxies to: GET /api/v1/recruiter-metrics/{recruiter_id}/benchmark?company_id=<uuid>
// Returns: personal metrics + company median + comparison per metric + overall_performance
export async function GET(
  request: NextRequest,
  { params }: { params: { recruiter_id: string } }
) {
  try {
    const { recruiter_id } = params
    const { searchParams } = new URL(request.url)
    const companyId = searchParams.get('company_id')

    if (!companyId) {
      return NextResponse.json({ error: 'company_id é obrigatório' }, { status: 422 })
    }

    const url = new URL(`${BACKEND_URL}/api/v1/recruiter-metrics/${recruiter_id}/benchmark`)
    url.searchParams.set('company_id', companyId)

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao calcular benchmark do recrutador' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao calcular benchmark do recrutador' },
      { status: 500 }
    )
  }
}
