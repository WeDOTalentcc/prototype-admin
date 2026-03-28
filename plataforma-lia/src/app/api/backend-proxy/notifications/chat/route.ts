import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const params = new URLSearchParams()
    
    if (searchParams.get("user_id")) params.append("user_id", searchParams.get("user_id")!)
    if (searchParams.get("thread_id")) params.append("thread_id", searchParams.get("thread_id")!)
    if (searchParams.get("undelivered_only")) params.append("undelivered_only", searchParams.get("undelivered_only")!)
    if (searchParams.get("limit")) params.append("limit", searchParams.get("limit")!)
    
    const response = await fetch(`${BACKEND_URL}/api/v1/notifications/chat?${params.toString()}`, {
      headers: {
        "Content-Type": "application/json",
      },
    })
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to fetch chat notifications" },
      { status: 500 }
    )
  }
}
