export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())
    
    
    const response = await fetch(`${BACKEND_URL}/api/v1/wizard/smart-orchestrate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: body.message,
        current_stage: body.current_stage || 'input-evaluation',
        collected_data: body.collected_data || {},
        conversation_history: body.conversation_history || [],
        conversation_id: body.conversation_id || `session-${Date.now()}`,
        company_id: body.company_id || 'default',
        user_id: body.user_id || 'default'
      }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json({
        success: false,
        lia_message: 'Erro ao processar sua mensagem. Tente novamente.',
        detected_criteria: {},
        auto_transition: false,
        tool_results: [],
        confidence: 0.3,
        reasoning_steps: [],
        error: `Backend error: ${response.status}`
      }, { status: 200 })
    }

    const data = await response.json()
    
    
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({
      success: false,
      lia_message: 'Erro de conexão com o servidor. Tente novamente.',
      detected_criteria: {},
      auto_transition: false,
      tool_results: [],
      confidence: 0.3,
      reasoning_steps: [],
      error: 'Connection error'
    }, { status: 200 })
  }
}
