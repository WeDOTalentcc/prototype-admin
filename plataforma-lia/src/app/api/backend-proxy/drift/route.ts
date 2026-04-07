export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

// GET /api/backend-proxy/drift?company_id=<uuid>
// Proxies to: GET /api/v1/drift/status?company_id=<uuid>
// Returns DriftStatusResponse: { company_id, evaluated_at, drift_detected, alert_level, triggers }
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const companyId = searchParams.get('company_id')

    if (!companyId) {
      return NextResponse.json({ error: 'company_id é obrigatório' }, { status: 400 })
    }

    const response = await fetch(
      `${BACKEND_URL}/api/v1/drift/status?company_id=${companyId}`,
      {
        method: 'GET',
        headers: getAuthHeaders(request),
      }
    )

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao consultar status de drift' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao consultar drift status' },
      { status: 500 }
    )
  }
}
