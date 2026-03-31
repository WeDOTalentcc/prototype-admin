export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get("user_id") || "default_user"
    
    const response = await fetch(
      `${BACKEND_URL}/api/v1/notifications/${id}/dismiss?user_id=${userId}`,
      {
        method: "POST",
        headers: getAuthHeaders(request),
      }
    )
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to dismiss notification" },
      { status: 500 }
    )
  }
}
