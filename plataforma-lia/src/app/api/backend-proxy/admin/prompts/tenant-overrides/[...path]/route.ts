/**
 * Wave 2 Agent B / T-13 — Admin Prompts tenant-override catch-all proxy.
 *
 * GET    /api/backend-proxy/admin/prompts/tenant-overrides/[...path]
 * PUT    /api/backend-proxy/admin/prompts/tenant-overrides/[...path]
 * DELETE /api/backend-proxy/admin/prompts/tenant-overrides/[...path]
 *
 * Multi-tenancy: backend valida company_id via JWT. company_id NUNCA no payload.
 */
export const dynamic = "force-dynamic"

import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function buildHeaders(request: NextRequest, includeContentType = true): HeadersInit {
  const headers: Record<string, string> = {}
  if (includeContentType) headers["Content-Type"] = "application/json"
  const authHeader = request.headers.get("Authorization")
  if (authHeader) headers["Authorization"] = authHeader
  return headers
}

async function resolveBackendUrl(
  request: NextRequest,
  pathSegments: string[],
): Promise<string> {
  const pathStr = pathSegments.map(encodeURIComponent).join("/")
  const { searchParams } = new URL(request.url)
  const qs = searchParams.toString()
  return `${BACKEND_URL}/api/v1/admin/prompts/tenant-overrides/${pathStr}${qs ? "?" + qs : ""}`
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  try {
    const { path } = await params
    const backendUrl = await resolveBackendUrl(request, path)
    const response = await fetch(backendUrl, {
      method: "GET",
      headers: buildHeaders(request, false),
    })
    const data = await response.json().catch(() => ({ detail: response.statusText }))
    return NextResponse.json(data, { status: response.status })
  } catch {
    return NextResponse.json(
      { error: "Failed to connect to backend" },
      { status: 500 },
    )
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  try {
    const { path } = await params
    const backendUrl = await resolveBackendUrl(request, path)
    let body: unknown
    try {
      body = await request.json()
    } catch {
      return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 })
    }
    const response = await fetch(backendUrl, {
      method: "PUT",
      headers: buildHeaders(request, true),
      body: JSON.stringify(body),
    })
    const data = await response.json().catch(() => ({ detail: response.statusText }))
    return NextResponse.json(data, { status: response.status })
  } catch {
    return NextResponse.json(
      { error: "Failed to connect to backend" },
      { status: 500 },
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  try {
    const { path } = await params
    const backendUrl = await resolveBackendUrl(request, path)
    const response = await fetch(backendUrl, {
      method: "DELETE",
      headers: buildHeaders(request, false),
    })
    const data = await response.json().catch(() => ({ detail: response.statusText }))
    return NextResponse.json(data, { status: response.status })
  } catch {
    return NextResponse.json(
      { error: "Failed to connect to backend" },
      { status: 500 },
    )
  }
}
