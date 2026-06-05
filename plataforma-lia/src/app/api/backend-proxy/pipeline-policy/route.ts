export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { resolveCompanyId } from '@/lib/api/resolve-company-id'
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const action = searchParams.get('action') || 'templates'
    const companyId = await resolveCompanyId(request)
    if (!companyId) {
      return NextResponse.json({ error: 'Company ID não disponível' }, { status: 401 })
    }
    const candidateId = searchParams.get('candidate_id') || ''
    const targetStage = searchParams.get('target_stage') || ''

    let backendUrl: string

    if (action === 'validate-transition') {
      backendUrl = `${BACKEND_URL}/api/v1/pipeline-policy/${companyId}/validate-transition?candidate_id=${candidateId}&target_stage=${targetStage}`
    } else {
      backendUrl = `${BACKEND_URL}/api/v1/pipeline-policy/${companyId}/templates`
    }

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao consultar política de pipeline', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
