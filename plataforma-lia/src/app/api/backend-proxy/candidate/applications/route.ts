export const dynamic = 'force-dynamic'
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  const token = request.headers.get('Authorization')?.replace('Bearer ', '')
  if (!token) return NextResponse.json({ error: 'missing_token' }, { status: 401 })

  const response = await fetch(`${BACKEND_URL}/api/v1/candidate/applications`, {
    headers: { 'Authorization': `Bearer ${token}` },
  })

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    return NextResponse.json(
      { error: (data as Record<string, unknown>).detail as string || 'erro_backend' },
      { status: response.status }
    )
  }
  return NextResponse.json(data)
}
