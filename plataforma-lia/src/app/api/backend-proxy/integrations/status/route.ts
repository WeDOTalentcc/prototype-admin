export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/integrations/status`, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { teams: { configured: false }, webhooks: { available: true } },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { teams: { configured: false }, webhooks: { available: true } },
      { status: 500 }
    )
  }
}
