export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams

  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/clients/dashboard-summary?${searchParams}`,
      {
        headers: {
          'X-Company-ID': 'admin',
          'X-User-Role': 'admin',
          'Content-Type': 'application/json'
        }
      }
    )

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to fetch dashboard summary' },
      { status: 500 }
    )
  }
}
