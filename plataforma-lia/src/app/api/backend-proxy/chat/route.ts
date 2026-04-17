export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { proxyFetchWithRetry } from '@/lib/api/proxy-fetch-with-retry'
import { z } from 'zod'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    // LIA-CHAT-422: backend expects field "content", proxy may receive "message"
    const mappedBody = { ...body, content: (body as any).content ?? (body as any).message }

    const response = await proxyFetchWithRetry(request, '/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify(mappedBody),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao processar mensagem', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    if (data && typeof data === "object" && "thought" in data) {
      const { thought: _thought, ...safeData } = data
      return NextResponse.json(safeData)
    }
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const conversationId = searchParams.get('conversation_id')
    
    let backendPath = '/api/v1/chat/conversations'
    if (conversationId) {
      backendPath = `/api/v1/chat/conversations/${conversationId}`
    } else {
      const queryString = searchParams.toString()
      if (queryString) {
        backendPath = `${backendPath}?${queryString}`
      }
    }
    
    const response = await proxyFetchWithRetry(request, backendPath, {
      method: 'GET',
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao buscar conversas' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
