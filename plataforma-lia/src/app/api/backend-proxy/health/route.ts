// proxy-auth-exempt: health check publico (liveness), sem dado de tenant
export const dynamic = "force-dynamic"
import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/health`, {
      signal: AbortSignal.timeout(5000),
    })

    if (!response.ok) {
      return NextResponse.json({ status: 'unhealthy' }, { status: 502 })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ status: 'unreachable' }, { status: 503 })
  }
}
