export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/recruitment-stages/company-pipeline`, {
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch company pipeline' },
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

const _bodySchema = z.record(z.string(), z.unknown())

export async function PUT(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())
    const response = await fetch(`${BACKEND_URL}/api/v1/recruitment-stages/company-pipeline`, {
      method: 'PUT',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to update company pipeline' }))
      return NextResponse.json(errorData, { status: response.status })
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
