export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

function getAuthHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  const authHeader = request.headers.get('authorization')
  if (authHeader) {
    headers['Authorization'] = authHeader
  }
  return headers
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const params = new URLSearchParams()

    const page = searchParams.get("page")
    const entity_id = searchParams.get("entity_id")
    const entity_name = searchParams.get("entity_name")
    const limit = searchParams.get("limit")

    if (page) params.append("page", page)
    if (entity_id) params.append("entity_id", entity_id)
    if (entity_name) params.append("entity_name", entity_name)
    if (limit) params.append("limit", limit)

    const response = await fetch(
      `${BACKEND_URL}/api/v1/lia/context-suggestions?${params.toString()}`,
      { headers: getAuthHeaders(request) }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: (errorData as { detail?: string }).detail || "Failed to fetch context suggestions" },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
