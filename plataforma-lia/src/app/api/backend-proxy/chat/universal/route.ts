import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

/**
 * Proxy para o endpoint universal de chat da LIA.
 * POST /api/v1/chat/universal
 *
 * Aceita mensagens de qualquer contexto de página e roteia
 * para o domínio correto automaticamente via MainOrchestrator.
 *
 * Body: {
 *   message: string
 *   context_page: "sourcing" | "job" | "pipeline" | "kanban" | "analytics" | "general"
 *   entity_id?: string
 *   entity_type?: "sourcing" | "job" | "candidate"
 *   conversation_id?: string
 *   candidates?: object[]
 *   selected_candidate_ids?: string[]
 *   job_context?: object
 *   search_context?: object
 *   target_job?: object
 * }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const authHeader = request.headers.get('authorization')

    const backendUrl = `${BACKEND_URL}/api/v1/chat/universal`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (authHeader) {
      headers['Authorization'] = authHeader
    }

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao processar mensagem', details: errorData },
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
