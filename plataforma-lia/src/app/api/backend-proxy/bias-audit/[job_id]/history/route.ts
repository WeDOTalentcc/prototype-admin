export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

// GET /api/backend-proxy/bias-audit/[job_id]/history
// Proxies to: GET /api/v1/bias-audit/job/{job_id}/history
// Returns: { job_id, history: BiasAuditSnapshot[], count }
export async function GET(
  request: NextRequest,
  { params }: { params: { job_id: string } }
) {
  try {
    const { job_id } = params

    if (!job_id) {
      return NextResponse.json({ error: 'job_id é obrigatório' }, { status: 422 })
    }

    const { searchParams } = new URL(request.url)
    const limit = searchParams.get('limit') ?? '10'

    const response = await fetch(
      `${BACKEND_URL}/api/v1/bias-audit/job/${job_id}/history?limit=${limit}`,
      {
        method: 'GET',
        headers: getAuthHeaders(request),
      }
    )

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao consultar histórico de auditoria de viés' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao consultar histórico de bias audit' },
      { status: 500 }
    )
  }
}
