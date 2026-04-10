export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const recruiterIdParam = searchParams.get('recruiter_id')

    const backendUrl = new URL(`${BACKEND_URL}/api/v1/digest/weekly/preview`)
    if (recruiterIdParam) {
      backendUrl.searchParams.set('recruiter_id', recruiterIdParam)
    }

    const response = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errText = await response.text()
      return NextResponse.json(
        { error: errText },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: 'Erro ao buscar resumo semanal' },
      { status: 500 }
    )
  }
}
