import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
const SERVICE_API_TOKEN = process.env.SERVICE_API_TOKEN || 'dev-service-token'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const requestBody = {
      candidate_id: body.candidate_id,
      user_instructions: body.user_instructions,
      use_pearch: body.use_pearch !== undefined ? body.use_pearch : true,
      use_gemini: body.use_gemini !== undefined ? body.use_gemini : true
    }
    
    const response = await fetch(`${BACKEND_URL}/api/v1/candidates/analyze-match-all`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${SERVICE_API_TOKEN}`,
      },
      body: JSON.stringify(requestBody),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error('Analyze match all error:', errorData)
      return NextResponse.json(
        { error: 'Erro ao analisar match para todas as vagas', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Analyze match all proxy error:', error)
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
