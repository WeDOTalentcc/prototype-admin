import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get("user_id") || "default_user"
    
    const response = await fetch(`${BACKEND_URL}/api/v1/notifications/unread-count?user_id=${userId}`, {
      headers: {
        "Content-Type": "application/json",
      },
    })
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error fetching unread count:", error)
    return NextResponse.json(
      { success: false, error: "Failed to fetch unread count" },
      { status: 500 }
    )
  }
}
