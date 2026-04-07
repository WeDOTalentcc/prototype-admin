export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const message = body.message as string
    const context = body.context as Record<string, unknown> | undefined
    
    const chatPayload: { content: string; conversation_id: string | null } = {
      content: message,
      conversation_id: (context?.conversation_id as string) || null
    }
    
    if (context?.candidate_id || context?.candidate_name) {
      chatPayload.content = `[Contexto: Candidato ${context.candidate_name as string || ''} (ID: ${context.candidate_id as string || 'N/A'})]\n\n${message}`
    }
    
    const backendUrl = `${BACKEND_URL}/api/v1/chat`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(chatPayload),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao processar mensagem da LIA', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    
    return NextResponse.json({
      success: true,
      response: data.message?.content || data.content || 'Sem resposta',
      conversation_id: data.conversation?.id || data.conversation_id,
      metadata: data.message?.message_metadata || {}
    })
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend da LIA' },
      { status: 500 }
    )
  }
}
