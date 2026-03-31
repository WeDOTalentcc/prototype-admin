export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

function getAuthHeaders(request: NextRequest): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Company-ID': request.headers.get('X-Company-ID') || 'admin_company',
    'X-User-ID': request.headers.get('X-User-ID') || 'admin_user',
    'X-User-Role': request.headers.get('X-User-Role') || 'admin'
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())
    const response = await fetch(`${BACKEND_URL}/api/v1/recruitment-stages/transition/execute`, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })
    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to execute transition' },
        { status: response.status }
      )
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Backend unavailable' },
      { status: 503 }
    )
  }
}
