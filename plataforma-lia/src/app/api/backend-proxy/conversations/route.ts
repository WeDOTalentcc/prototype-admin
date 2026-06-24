export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { proxyFetchWithRetry } from '@/lib/api/proxy-fetch-with-retry'
import { createProxyHandlers } from '@/lib/api/proxy-handler'
import { z } from 'zod'

const _bodySchema = z.record(z.string(), z.unknown())

const _proxy = createProxyHandlers({
  backendPath: "/api/v1/conversations",
  methods: ["GET"],
})

export const GET = _proxy.GET

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const response = await proxyFetchWithRetry(request, '/api/v1/conversations', {
      method: 'POST',
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Failed to create conversation', details: errorData },
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
