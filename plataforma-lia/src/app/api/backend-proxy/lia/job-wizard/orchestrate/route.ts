import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.LIA_BACKEND_URL || 'http://0.0.0.0:8000'

const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())
    
    const response = await fetch(`${BACKEND_URL}/api/v1/lia/job-wizard/orchestrate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      return NextResponse.json(
        { 
          action: "respond",
          response: "Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?",
          confidence: 0.3
        },
        { status: 200 }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { 
        action: "respond",
        response: "Desculpe, tive um problema ao processar sua mensagem. Pode tentar novamente?",
        confidence: 0.3
      },
      { status: 200 }
    )
  }
}
