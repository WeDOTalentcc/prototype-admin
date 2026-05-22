export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const headers = getAuthHeaders(request, true)
    const { id } = await params

    const { searchParams } = new URL(request.url)
    const queryParams = new URLSearchParams()

    if (searchParams.get('status')) queryParams.set('status', searchParams.get('status')!)
    if (searchParams.get('limit')) queryParams.set('limit', searchParams.get('limit')!)
    if (searchParams.get('offset')) queryParams.set('offset', searchParams.get('offset')!)

    const backendUrl = `${BACKEND_URL}/api/v1/webhooks/${id}/logs?${queryParams.toString()}`

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar logs do webhook', details: errorData },
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
