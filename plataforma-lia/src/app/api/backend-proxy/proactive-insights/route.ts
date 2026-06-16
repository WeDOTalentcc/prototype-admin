export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const params = new URLSearchParams()
    if (searchParams.get('company_id')) params.set('company_id', searchParams.get('company_id')!)
    if (searchParams.get('job_id')) params.set('job_id', searchParams.get('job_id')!)
    if (searchParams.get('limit')) params.set('limit', searchParams.get('limit')!)

    const response = await fetch(
      `${BACKEND_URL}/api/v1/proactive-actions/insights?${params.toString()}`,
      { headers: getAuthHeaders(request) }
    )

    if (!response.ok) {
      return NextResponse.json([], { status: 200 })
    }

    const data = await response.json()
    return NextResponse.json(Array.isArray(data) ? data : [])
  } catch {
    return NextResponse.json([])
  }
}
