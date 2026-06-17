import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ alertId: string }> }
) {
  const { alertId } = await params
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get('user_id') || 'current_user'
    const note = searchParams.get('note') || undefined

    let url = `${BACKEND_URL}/api/v1/alerts/${alertId}/resolve?user_id=${userId}`
    if (note) url += `&resolution_note=${encodeURIComponent(note)}`

    const response = await fetch(url, { method: "POST", headers: getAuthHeaders(request) })
    if (!response.ok) {
      return NextResponse.json({ success: false, error: "Backend error" }, { status: response.status })
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ success: false, error: "Connection failed" }, { status: 502 })
  }
}
