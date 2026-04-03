// @validated: no-body action route (no user input to validate)
export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get("user_id") || "default_user"
    const category = searchParams.get("category")
    
    const params = new URLSearchParams()
    params.append("user_id", userId)
    if (category) params.append("category", category)
    
    const response = await fetch(
      `${BACKEND_URL}/api/v1/notifications/read-all?${params.toString()}`,
      {
        method: "POST",
        headers: getAuthHeaders(request),
      }
    )
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to mark all notifications as read" },
      { status: 500 }
    )
  }
}
