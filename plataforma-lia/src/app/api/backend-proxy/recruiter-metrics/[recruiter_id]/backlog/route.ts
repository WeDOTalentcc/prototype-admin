export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

// GET /api/backend-proxy/recruiter-metrics/[recruiter_id]/backlog
// Proxies to: GET /api/v1/recruiter-metrics/{recruiter_id}/backlog
// Returns prioritized list of candidates waiting for recruiter action
export async function GET(
  request: NextRequest,
  { params }: { params: { recruiter_id: string } }
) {
  try {
    const { recruiter_id } = params
    const { searchParams } = new URL(request.url)
    const companyId = searchParams.get('company_id')

    if (!companyId) {
      return NextResponse.json({ error: 'company_id é obrigatório' }, { status: 400 })
    }

    const url = new URL(`${BACKEND_URL}/api/v1/recruiter-metrics/${recruiter_id}/backlog`)
    url.searchParams.set('company_id', companyId)

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao buscar backlog do recrutador' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao buscar backlog do recrutador' },
      { status: 500 }
    )
  }
}
