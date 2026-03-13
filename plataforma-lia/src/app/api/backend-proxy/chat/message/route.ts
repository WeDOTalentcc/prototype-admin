import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const response = await fetch(`${BACKEND_URL}/chat/message`, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      if (process.env.NODE_ENV === 'development') {
        console.warn(`[Chat Message] Backend ${response.status}:`, JSON.stringify(errorData).slice(0, 200))
      }
      return NextResponse.json(
        { content: 'Erro ao processar mensagem. Tente novamente.', error: 'backend_error' },
        { status: 200 }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    if (process.env.NODE_ENV === 'development') {
      console.warn('[Chat Message] Proxy error:', (error as Error)?.message || error)
    }
    return NextResponse.json(
      { content: 'Erro ao conectar com o backend.', error: 'connection_error' },
      { status: 200 }
    )
  }
}
