export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

// GET /api/backend-proxy/recruiter-metrics/[recruiter_id]
// Proxies to: GET /api/v1/recruiter-metrics/{recruiter_id}
// Returns weekly productivity summary: backlog_count, critical_count, most_urgent,
// avg_response_time_days, candidates_advanced_this_week, offers_pending
export async function GET(
  request: NextRequest,
  { params }: { params: { recruiter_id: string } }
) {
  try {
    const { recruiter_id } = params
    const { searchParams } = new URL(request.url)
    const companyId = searchParams.get('company_id')
    const periodDays = searchParams.get('period_days') || '30'

    if (!companyId) {
      return NextResponse.json({ error: 'company_id é obrigatório' }, { status: 400 })
    }

    const url = new URL(`${BACKEND_URL}/api/v1/recruiter-metrics/${recruiter_id}`)
    url.searchParams.set('company_id', companyId)
    url.searchParams.set('period_days', periodDays)

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao buscar métricas do recrutador' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao buscar métricas do recrutador' },
      { status: 500 }
    )
  }
}
