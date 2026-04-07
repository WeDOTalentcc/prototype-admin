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
        context: body.context,
      }),
    })

    if (!response.ok) {
      return NextResponse.json(
        { content: 'Erro ao processar mensagem. Tente novamente.', error: 'backend_error' },
        { status: 200 }
      )
    }

    const data = await response.json() as Record<string, unknown>

    const content =
      (data.content as string | undefined) ||
      ((data.message as Record<string, unknown> | undefined)?.content as string | undefined) ||
      ((data.message as Record<string, unknown> | undefined)?.text as string | undefined) ||
      ''

    const conversationId =
      (data.conversation_id as string | undefined) ||
      ((data.message as Record<string, unknown> | undefined)?.conversation_id as string | undefined) ||
      ((data.conversation as Record<string, unknown> | undefined)?.id as string | undefined)

    return NextResponse.json({
      content,
      conversation_id: conversationId,
      message_metadata: data.message_metadata,
    })
  } catch {
    return NextResponse.json(
      { content: 'Erro ao conectar com o backend.', error: 'connection_error' },
      { status: 200 }
    )
  }
}
