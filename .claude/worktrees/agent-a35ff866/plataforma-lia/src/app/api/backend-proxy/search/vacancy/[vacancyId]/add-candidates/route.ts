import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ vacancyId: string }> }
) {
  try {
    const { vacancyId } = await params
    const body = await request.json()
    
    const response = await fetch(
      `${BACKEND_URL}/api/v1/search/vacancy/${vacancyId}/add-candidates`,
      {
        method: 'POST',
        headers: getAuthHeaders(request),
        body: JSON.stringify(body),
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error('Add candidates to vacancy error:', errorData)
      return NextResponse.json(
        { error: 'Erro ao adicionar candidatos à vaga', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Add candidates to vacancy proxy error:', error)
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
