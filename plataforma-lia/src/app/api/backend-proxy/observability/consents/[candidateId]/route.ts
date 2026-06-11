export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

interface RouteParams {
  params: { candidateId: string }
}

export async function GET(request: NextRequest, { params }: RouteParams) {
  try {
    const { candidateId } = params
    if (!candidateId) {
      return NextResponse.json({ error: 'candidateId obrigatório' }, { status: 400 })
    }

    const headers = getAuthHeaders(request, true)
    const backendUrl = `${BACKEND_URL}/api/v1/consents/${candidateId}`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar registros de consentimento', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    if (error instanceof Error && error.message.includes('Authentication required')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
