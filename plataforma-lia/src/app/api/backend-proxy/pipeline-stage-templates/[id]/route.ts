export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(request: NextRequest): HeadersInit {
  const h: HeadersInit = { "Content-Type": "application/json" }
  const a = request.headers.get("Authorization")
  if (a) h["Authorization"] = a
  return h
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/v1/pipeline-stage-templates/${encodeURIComponent(id)}`,
      { method: "GET", headers: getAuthHeaders(request) },
    )
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Failed" },
      { status: 500 },
    )
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  try {
    const body = await request.json()
    const res = await fetch(
      `${BACKEND_URL}/api/v1/pipeline-stage-templates/${encodeURIComponent(id)}`,
      {
        method: "PUT",
        headers: getAuthHeaders(request),
        body: JSON.stringify(body),
      },
    )
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Failed" },
      { status: 500 },
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/v1/pipeline-stage-templates/${encodeURIComponent(id)}`,
      { method: "DELETE", headers: getAuthHeaders(request) },
    )
    if (res.status === 204) {
      return new NextResponse(null, { status: 204 })
    }
    const data = await res.json().catch(() => ({}))
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Failed" },
      { status: 500 },
    )
  }
}
