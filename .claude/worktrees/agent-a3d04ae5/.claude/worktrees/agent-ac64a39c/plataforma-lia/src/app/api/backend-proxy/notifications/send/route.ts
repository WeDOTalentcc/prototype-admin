import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/v1/notifications/send`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error sending multi-channel notification:", error)
    return NextResponse.json(
      { success: false, error: "Failed to send notification" },
      { status: 500 }
    )
  }
}
