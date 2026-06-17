export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function POST(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/audit-logs/retention-policies/seed`, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify({})
    })
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ error: error.detail || 'Failed to seed retention policies' }, { status: response.status })
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
