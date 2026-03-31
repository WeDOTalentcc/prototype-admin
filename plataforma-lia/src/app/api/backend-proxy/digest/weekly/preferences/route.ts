export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get('user_id') || 'default_user'

    const response = await fetch(
      `${BACKEND_URL}/api/v1/digest/weekly/preferences?user_id=${userId}`,
      {
        method: 'GET',
        headers: getAuthHeaders(request),
      }
    )

    if (!response.ok) {
      return NextResponse.json(
        { weekly_report_enabled: true },
        { status: 200 }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { weekly_report_enabled: true },
      { status: 200 }
    )
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()

    const response = await fetch(
      `${BACKEND_URL}/api/v1/digest/weekly/preferences`,
      {
        method: 'PUT',
        headers: {
          ...getAuthHeaders(request),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      }
    )

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
      { error: 'Erro ao atualizar preferência do resumo semanal' },
      { status: 500 }
    )
  }
}
