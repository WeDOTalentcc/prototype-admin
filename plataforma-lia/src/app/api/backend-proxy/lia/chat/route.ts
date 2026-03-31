export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())
    
    const { message, context } = body
    
    const chatPayload = {
      content: message,
      conversation_id: context?.conversation_id || null
    }
    
    if (context?.candidate_id || context?.candidate_name) {
      chatPayload.content = `[Contexto: Candidato ${context.candidate_name || ''} (ID: ${context.candidate_id || 'N/A'})]\n\n${message}`
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
