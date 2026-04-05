export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8001'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data

    const response = await fetch(`${BACKEND_URL}/api/v1/chat`, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify({
        content: body.message || body.content || '',
        user_id: body.user_id,
        conversation_id: body.conversation_id,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      if (process.env.NODE_ENV === 'development') {
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
    }
    return NextResponse.json(
      { content: 'Erro ao conectar com o backend.', error: 'connection_error' },
      { status: 200 }
    )
  }
}
