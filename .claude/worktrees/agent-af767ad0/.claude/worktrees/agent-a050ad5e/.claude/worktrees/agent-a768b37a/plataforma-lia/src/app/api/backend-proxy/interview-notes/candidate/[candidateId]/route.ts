import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { candidateId: string } }
) {
  try {
    const { searchParams } = new URL(request.url)
    const jobId = searchParams.get('jobId')
    const query = jobId ? `?job_id=${jobId}` : ''

    const response = await fetch(
      `${BACKEND_URL}/api/v1/interview-notes/candidate/${params.candidateId}${query}`,
      { method: 'GET', headers: getAuthHeaders(request) }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar notas do candidato', details: errorData },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch (error) {
    console.error('Interview notes candidate proxy error:', error)
    return NextResponse.json({ error: 'Erro ao conectar com o backend' }, { status: 500 })
  }
}
