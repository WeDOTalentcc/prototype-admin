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

    const raw = await response.json() as Record<string, unknown>

    // Backend wraps responses in { ok, data: { message: { content } }, meta }
    // Support both the enveloped format and any legacy flat format.
    const envelopeData = (raw.data as Record<string, unknown> | undefined) ?? raw

    const content =
      (envelopeData.content as string | undefined) ||
      ((envelopeData.message as Record<string, unknown> | undefined)?.content as string | undefined) ||
      ((envelopeData.message as Record<string, unknown> | undefined)?.text as string | undefined) ||
      (raw.content as string | undefined) ||
      ''

    const conversationId =
      (envelopeData.conversation_id as string | undefined) ||
      ((envelopeData.message as Record<string, unknown> | undefined)?.conversation_id as string | undefined) ||
      ((envelopeData.conversation as Record<string, unknown> | undefined)?.id as string | undefined) ||
      (raw.conversation_id as string | undefined)

    const messageMetadata =
      (envelopeData.message_metadata as Record<string, unknown> | undefined) ||
      ((envelopeData.message as Record<string, unknown> | undefined)?.message_metadata as Record<string, unknown> | undefined) ||
      (raw.message_metadata as Record<string, unknown> | undefined)

    return NextResponse.json({
      content,
      conversation_id: conversationId,
      message_metadata: messageMetadata,
    })
  } catch {
    return NextResponse.json(
      { content: 'Erro ao conectar com o backend.', error: 'connection_error' },
      { status: 200 }
    )
  }
}
