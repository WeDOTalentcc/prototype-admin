export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { proxyFetchWithRetry } from '@/lib/api/proxy-fetch-with-retry'
import { z } from 'zod'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data

    const response = await proxyFetchWithRetry(request, '/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify({
        content: body.message || body.content || '',
        user_id: body.user_id,
        conversation_id: body.conversation_id,
      }),
    })

    if (!response.ok) {
      return NextResponse.json(
        { content: 'Erro ao processar mensagem. Tente novamente.', error: 'backend_error' },
        { status: 200 }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { content: 'Erro ao conectar com o backend.', error: 'connection_error' },
      { status: 200 }
    )
  }
}
