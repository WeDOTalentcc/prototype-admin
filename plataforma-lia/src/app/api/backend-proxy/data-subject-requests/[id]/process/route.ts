export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { validateParams, validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const routeParamsSchema = z.object({
  id: z.string().min(1, 'id is required'),
})



const _bodySchema = z.record(z.string(), z.unknown())

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const paramValidation = validateParams({ id }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    let body: Record<string, unknown> = {}
    const parseResult = _bodySchema.safeParse(await request.json().catch(() => ({}))); body = parseResult.success ? parseResult.data : {}
    
    const response = await fetch(`${BACKEND_URL}/api/v1/data-subject-requests/${id}/process`, {
      method: 'PUT',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body)
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json(
        { error: error.detail || 'Failed to process request' },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
