import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const path = searchParams.get("path") || ""
    const params = new URLSearchParams()

    if (searchParams.get("limit")) params.append("limit", searchParams.get("limit")!)

    const queryString = params.toString() ? `?${params.toString()}` : ""
    const url = `${BACKEND_URL}/api/v1/proactive-actions/${path}${queryString}`

    const response = await fetch(url, {
      headers: getAuthHeaders(request),
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Proactive actions proxy error:", error)
    return NextResponse.json(
      { success: false, error: "Failed to fetch proactive actions" },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const path = searchParams.get("path") || ""
    const body = await request.json()
    const url = `${BACKEND_URL}/api/v1/proactive-actions/${path}`

    const response = await fetch(url, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Proactive actions proxy error:", error)
    return NextResponse.json(
      { success: false, error: "Failed to process proactive action" },
      { status: 500 }
    )
  }
}
