import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const params = new URLSearchParams()
    
    if (searchParams.get("user_id")) params.append("user_id", searchParams.get("user_id")!)
    if (searchParams.get("unread_only")) params.append("unread_only", searchParams.get("unread_only")!)
    if (searchParams.get("category")) params.append("category", searchParams.get("category")!)
    if (searchParams.get("limit")) params.append("limit", searchParams.get("limit")!)
    
    const response = await fetch(`${BACKEND_URL}/api/v1/notifications?${params.toString()}`, {
      headers: getAuthHeaders(request),
    })
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error fetching notifications:", error)
    return NextResponse.json(
      { success: false, error: "Failed to fetch notifications" },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/v1/notifications`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error creating notification:", error)
    return NextResponse.json(
      { success: false, error: "Failed to create notification" },
      { status: 500 }
    )
  }
}
