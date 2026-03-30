import { NextRequest, NextResponse } from 'next/server'
import { validateBody, validateParams } from '@/lib/api/validate'
import { jobStatusSchema } from '@/lib/schemas'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const jobIdSchema = z.object({ jobId: z.string().min(1) })

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  try {
    const rawParams = await params
    const paramsResult = validateParams(rawParams, jobIdSchema)
    if (!paramsResult.success) return paramsResult.response

    const bodyResult = await validateBody(request, jobStatusSchema)
    if (!bodyResult.success) return bodyResult.response

    const { jobId } = paramsResult.data
    const backendUrl = `${BACKEND_URL}/api/v1/job-vacancies/${jobId}/close`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyResult.data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao fechar vaga', details: errorData },
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
