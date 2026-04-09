export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders, getAuthHeadersForForm } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const { searchParams } = new URL(request.url)
  const queryString = searchParams.toString()
  const url = `${BACKEND_URL}/api/v1/candidates/${encodeURIComponent(id)}/files${queryString ? "?" + queryString : ""}`

  try {
    const response = await fetch(url, { headers: getAuthHeaders(request) })
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(errorData, { status: response.status })
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ error: "Failed to connect to backend" }, { status: 500 })
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const { searchParams } = new URL(request.url)
  const queryString = searchParams.toString()
  const url = `${BACKEND_URL}/api/v1/candidates/${encodeURIComponent(id)}/files${queryString ? "?" + queryString : ""}`

  try {
    const formData = await request.formData()
    const headers = getAuthHeadersForForm(request)

    const response = await fetch(url, {
      method: "POST",
      headers,
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(errorData, { status: response.status })
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ error: "Failed to upload file" }, { status: 500 })
  }
}
