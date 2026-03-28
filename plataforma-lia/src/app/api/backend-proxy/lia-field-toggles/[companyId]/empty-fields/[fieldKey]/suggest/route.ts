import { NextRequest, NextResponse } from 'next/server'

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

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ companyId: string; fieldKey: string }> }
) {
  try {
    const { companyId, fieldKey } = await params
    const body = await request.json()
    
    const response = await fetch(
      `${BACKEND_URL}/api/v1/lia-field-toggles/${companyId}/empty-fields/${fieldKey}/suggest`,
      {
        method: 'POST',
        headers: getAuthHeaders(request),
        body: JSON.stringify(body),
      }
    )

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { error: 'Failed to get field suggestion', details: errorText },
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
