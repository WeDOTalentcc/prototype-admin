import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ taskId: string }> }
) {
  const { taskId } = await params
  try {
    const body = await request.json()
    const response = await fetch(`${BACKEND_URL}/api/v1/task-lifecycle/${taskId}/reject`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })
    if (!response.ok) {
      return NextResponse.json({ success: false, error: "Backend error" }, { status: response.status })
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ success: false, error: "Connection failed" }, { status: 502 })
  }
}
