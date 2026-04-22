export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { getSessionAuth } from '@/lib/api/session-auth'
import { BACKEND_URL } from '@/lib/api/backend-url'
import { z } from 'zod'

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const auth = await getSessionAuth()
    if (!auth.success) return auth.response

    const bodyResult = await validateBody(request, _bodySchema)
    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const response = await fetch(`${BACKEND_URL}/api/v1/recruitment-stages/transition/execute`, {
      method: 'POST',
      headers: auth.headers,
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
  } catch {
    return NextResponse.json(
      { error: 'Backend unavailable' },
      { status: 503 }
    )
  }
}
