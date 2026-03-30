import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

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

const _bodySchema = z.record(z.unknown())

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ companyId: string; fieldKey: string }> }
) {
  try {
    const { companyId, fieldKey } = await params
    const body = _bodySchema.parse(await request.json())
    
    const response = await fetch(
      `${BACKEND_URL}/api/v1/lia-field-toggles/${companyId}/empty-fields/${fieldKey}/action`,
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
