export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const url = `${BACKEND_URL}/api/v1/candidates/${encodeURIComponent(id)}/education`
  try {
    const body = await request.json()
    const response = await fetch(url, {
      method: "PUT",
      headers: { ...getAuthHeaders(request), "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      return NextResponse.json(err, { status: response.status })
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ error: "Failed to connect to backend" }, { status: 500 })
  }
}
