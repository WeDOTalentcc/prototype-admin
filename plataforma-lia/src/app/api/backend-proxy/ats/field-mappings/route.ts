export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const connectionId = searchParams.get('connection_id')

    if (!connectionId) {
      return NextResponse.json({ mappings: [] })
    }

    const response = await fetch(
      `${BACKEND_URL}/api/v1/ats/field-mappings/${connectionId}`,
      {
        method: 'GET',
        headers: getAuthHeaders(request),
      }
    )

    if (!response.ok) {
      return NextResponse.json({ mappings: [] }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ mappings: [] }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const response = await fetch(`${BACKEND_URL}/api/v1/ats/field-mappings`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(request),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { success: false, message: 'Erro ao salvar mapeamentos' },
      { status: 500 }
    )
  }
}
