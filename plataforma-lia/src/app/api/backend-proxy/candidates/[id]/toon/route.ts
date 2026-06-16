export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params

    if (!id) {
      return NextResponse.json({ error: 'candidateId é obrigatório' }, { status: 400 })
    }

    const { searchParams } = request.nextUrl
    const backendParams = new URLSearchParams()

    const jobId = searchParams.get('job_id')
    if (jobId) backendParams.set('job_id', jobId)

    const companyId = searchParams.get('company_id')
    if (companyId) backendParams.set('company_id', companyId)

    const anonymize = searchParams.get('anonymize')
    if (anonymize) backendParams.set('anonymize', anonymize)

    const queryString = backendParams.toString()
    const url = `${BACKEND_URL}/api/v1/candidates/${id}/toon${queryString ? `?${queryString}` : ''}`

    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({ error: 'Erro ao obter TOON card' }))
      return NextResponse.json(errorBody, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao obter TOON card' },
      { status: 500 }
    )
  }
}
