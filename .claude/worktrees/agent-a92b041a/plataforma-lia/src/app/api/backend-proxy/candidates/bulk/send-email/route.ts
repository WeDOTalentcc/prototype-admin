import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
const SERVICE_API_TOKEN = process.env.SERVICE_API_TOKEN || 'dev-service-token'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const requestBody = {
      candidate_ids: body.candidate_ids,
      template_id: body.template_id,
      custom_variables: body.custom_variables || body.custom_data
    }
    
    const response = await fetch(`${BACKEND_URL}/api/v1/candidates/bulk/send-email`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${SERVICE_API_TOKEN}`,
      },
      body: JSON.stringify(requestBody),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error('Bulk send email error:', errorData)
      return NextResponse.json(
        { error: 'Erro ao enviar emails', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Bulk send email proxy error:', error)
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
