export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const routeParamsSchema = z.object({
  id: z.string().min(1, 'id is required'),
})

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const paramValidation = validateParams(await Promise.resolve({ id }), routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    
    const response = await fetch(`${BACKEND_URL}/api/v1/conversations/${id}/archive`, {
      method: 'POST',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Failed to archive conversation', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
