export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

const routeParamsSchema = z.object({
  profileId: z.string().min(1, 'profileId is required'),
})

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ profileId: string }> }
) {
  try {
    const { profileId } = await params
    const paramValidation = validateParams(await Promise.resolve({ profileId }), routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    
    const backendUrl = `${BACKEND_URL}/api/v1/company/auto-enrich/${profileId}`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { error: 'Failed to auto-enrich company profile', details: errorText },
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
