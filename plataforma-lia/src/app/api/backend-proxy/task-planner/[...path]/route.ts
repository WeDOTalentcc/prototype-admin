export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path } = await params
    const pathStr = path.join("/")
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()

    let backendUrl = `${BACKEND_URL}/api/v1/task-planner/${pathStr}`
    if (queryString) {
      backendUrl = `${backendUrl}?${queryString}`
    }

    const response = await fetch(backendUrl, {
      method: "GET",
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      return NextResponse.json(
        { error: errorData.detail || "Task planner request failed", details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: "Failed to connect to backend" },
      { status: 500 }
    )
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path } = await params
    const pathStr = path.join("/")
    const backendUrl = `${BACKEND_URL}/api/v1/task-planner/${pathStr}`

    const body = await request.json().catch(() => ({}))

    const response = await fetch(backendUrl, {
      method: "POST",
      headers: {
        ...getAuthHeaders(request),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      return NextResponse.json(
        { error: errorData.detail || "Task planner request failed", details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: "Failed to connect to backend" },
      { status: 500 }
    )
  }
}
