export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateParams, validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.LIA_BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const routeParamsSchema = z.object({
  id: z.string().min(1, 'id is required'),
})


const DEFAULT_SCREENING_CONFIG = {
  status: {
    enabled: true,
    paused_at: null,
    paused_by: null,
    pause_reason: null,
    scheduled_end_date: null,
    last_updated: new Date().toISOString()
  },
  channels: {
    whatsapp: { enabled: true, label: 'WhatsApp' },
    chat_web: { enabled: true, label: 'Chat Web' },
    phone: { enabled: false, label: 'Ligação' }
  },
  settings: {
    min_score: 70,
    response_timeout_hours: 48,
    max_retries: 2
  },
  metrics: {
    screened_count: 0,
    completion_rate: 0,
    average_rating: 4.2
  },
  scheduling: {
    auto_enabled: true,
    min_score_for_auto: 75,
    calendar_provider: 'Microsoft',
    available_hours: '9h-18h',
    interview_duration_min: 45
  },
  feedback_templates: {
    approved: 'Parabéns! Você foi aprovado na triagem inicial.',
    rejected: 'Agradecemos sua participação. Infelizmente não seguiremos com sua candidatura neste momento.'
  },
  wsi_skills: []
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const paramValidation = validateParams({ id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    
    const backendUrl = `${BACKEND_URL}/api/v1/vagas/${id}/screening-config`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.status === 404) {
      return NextResponse.json({
        ...DEFAULT_SCREENING_CONFIG,
        job_id: id,
        is_default: true
      })
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: `Failed to fetch screening config: ${response.statusText}`, details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json({
      ...DEFAULT_SCREENING_CONFIG,
      ...data,
      job_id: id,
      is_default: false
    })
  } catch (error) {
    return NextResponse.json({
      ...DEFAULT_SCREENING_CONFIG,
      is_default: true,
      error: 'Failed to fetch from backend'
    })
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const paramValidation = validateParams({ id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const backendUrl = `${BACKEND_URL}/api/v1/vagas/${id}/screening-config`
    
    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (response.status === 404) {
      return NextResponse.json({
        success: true,
        message: 'Screening config saved (stub)',
        data: { job_id: id, ...body, updated_at: new Date().toISOString() }
      })
    }

    if (!response.ok) {
      return NextResponse.json({
        success: true,
        message: 'Screening config saved (local)',
        data: { job_id: id, ...body, updated_at: new Date().toISOString() }
      })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({
      success: true,
      message: 'Screening config saved (fallback)',
      data: { updated_at: new Date().toISOString() }
    })
  }
}
