export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data

    // Task #1177 (addendum #1175): forward auth headers so the FastAPI
    // middleware can validate the JWT.
    const authHeaders = getAuthHeaders(request) as Record<string, string>
    const headers: Record<string, string> = { ...authHeaders, 'Content-Type': 'application/json' }
    const companyHeader = request.headers.get('x-company-id')
    if (companyHeader) headers['x-company-id'] = companyHeader
    const cookieHeader = request.headers.get('cookie')
    if (cookieHeader) headers['cookie'] = cookieHeader

    const response = await fetch(`${BACKEND_URL}/api/v1/wsi/questions/save`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { success: false, error: 'Failed to save questions' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Proxy connection error' },
      { status: 500 }
    )
  }
}
