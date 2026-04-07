export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

type Params = { params: { job_id: string } }

// GET /api/backend-proxy/async/jobs/[job_id]/status → GET /api/v1/async/jobs/{job_id}/status
export async function GET(request: NextRequest, { params }: Params) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/async/jobs/${params.job_id}/status`,
      { method: 'GET', headers: getAuthHeaders(request) }
    )

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Tarefa não encontrada' },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
