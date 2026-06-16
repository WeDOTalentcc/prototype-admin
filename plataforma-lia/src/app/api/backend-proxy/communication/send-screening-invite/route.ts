export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const companyId = request.headers.get('X-Company-ID') || (body.company_id as string | undefined) || ''
    
    const backendUrl = `${BACKEND_URL}/api/v1/communication/send-screening-invite`
    
    const requestBody = {
      channel: body.channel,
      candidate_id: body.candidate_id,
      candidate_name: body.candidate_name,
      candidate_email: body.candidate_email,
      candidate_phone: body.candidate_phone,
      subject: body.subject,
      message: body.message,
      vacancy_id: body.vacancy_id,
      vacancy_title: body.vacancy_title,
      screening_question_ids: body.screening_question_ids,
      stage: body.stage,
      tone_style: body.tone_style,
      company_id: companyId,
      override_saturation: body.override_saturation || false,
    }
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(request),
        'X-Company-ID': companyId,
      },
      body: JSON.stringify(requestBody),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      return NextResponse.json(
        { 
          success: false,
          error: data.detail || 'Erro ao enviar convite de triagem',
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
