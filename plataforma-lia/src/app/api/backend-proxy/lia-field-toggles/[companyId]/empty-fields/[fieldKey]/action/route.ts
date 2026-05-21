export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateParams, validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const routeParamsSchema = z.object({
  companyId: z.string().min(1, 'companyId is required'),
  fieldKey: z.string().min(1, 'fieldKey is required'),
})


function getAuthHeaders(request: NextRequest): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  const authHeader = request.headers.get('Authorization')
  if (authHeader) {
    headers['Authorization'] = authHeader
  }
  return headers
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ companyId: string; fieldKey: string }> }
) {
  try {
    const { companyId, fieldKey } = await params
    const paramValidation = validateParams({ companyId, fieldKey }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const response = await fetch(
      `${BACKEND_URL}/api/v1/company/${companyId}/empty-fields/${fieldKey}/action`,
      {
        method: 'POST',
        headers: getAuthHeaders(request),
        body: JSON.stringify(body),
      }
    )

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { error: 'Failed to update field preference', details: errorText },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
