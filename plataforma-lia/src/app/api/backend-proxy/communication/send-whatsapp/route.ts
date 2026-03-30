import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())
    const companyId = request.headers.get('X-Company-ID') || body.company_id || 'default'
    
    const backendUrl = `${BACKEND_URL}/api/v1/communication/send-whatsapp`
    
    const requestBody = {
      to_phone: body.to_phone || body.phone,
      message: body.message,
      candidate_id: body.candidate_id,
      candidate_name: body.candidate_name,
      vacancy_id: body.vacancy_id,
      vacancy_title: body.vacancy_title,
      communication_type: body.communication_type || body.type || 'whatsapp',
      metadata: body.metadata,
      company_id: companyId,
    }
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Company-ID': companyId,
      },
      body: JSON.stringify(requestBody),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      return NextResponse.json(
        { 
          success: false,
          error: data.detail || 'Erro ao enviar WhatsApp',
          details: data 
        },
        { status: response.status }
      )
    }

    return NextResponse.json({
      success: true,
      ...data
    })
  } catch (error) {
    return NextResponse.json(
      { 
        success: false,
        error: 'Erro ao conectar com o backend',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}
