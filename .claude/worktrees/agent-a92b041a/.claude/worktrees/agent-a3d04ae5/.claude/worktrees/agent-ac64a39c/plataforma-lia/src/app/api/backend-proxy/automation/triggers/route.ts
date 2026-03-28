import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/automation/triggers`, {
      headers: {
        "Content-Type": "application/json",
      },
    })
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error fetching automation triggers:", error)
    return NextResponse.json(
      { success: false, error: "Failed to fetch automation triggers" },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/v1/automation/triggers`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error updating automation trigger:", error)
    return NextResponse.json(
      { success: false, error: "Failed to update automation trigger" },
      { status: 500 }
    )
  }
}
