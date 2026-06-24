export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { validateParams, validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const routeParamsSchema = z.object({
  jobId: z.string().min(1, 'jobId is required'),
})


const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  try {
    const { jobId } = await params
    const paramValidation = validateParams({ jobId }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    let body: Record<string, unknown> = {}
    const parseResult = _bodySchema.safeParse(await request.json().catch(() => ({}))); body = parseResult.success ? parseResult.data : {}
    
    const response = await fetch(`${BACKEND_URL}/api/v1/search/archetypes/from-job`, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify({
        job_id: parseInt(jobId, 10),
        name: body.name || null,
        emoji: body.emoji || '🎯',
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar arquétipo', details: errorData },
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
