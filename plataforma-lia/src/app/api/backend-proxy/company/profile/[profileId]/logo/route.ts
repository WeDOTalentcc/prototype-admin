export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(request: NextRequest): HeadersInit {
  const headers: HeadersInit = {}
  const authHeader = request.headers.get("Authorization")
  if (authHeader) {
    headers["Authorization"] = authHeader
  }
  // NOTE: Do NOT set Content-Type — fetch must set multipart boundary
  return headers
}

/**
 * POST /api/backend-proxy/company/profile/{profileId}/logo
 * Forwards multipart/form-data upload to FastAPI backend.
 * Audit 2026-05-20 Sessão I Step 4 (P1.13 extended).
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ profileId: string }> },
) {
  const { profileId } = await params
  if (!profileId) {
    return NextResponse.json(
      { error: "profileId required" },
      { status: 400 },
    )
  }

  try {
    const formData = await request.formData()
    const res = await fetch(
      `${BACKEND_URL}/api/v1/company/profile/${encodeURIComponent(profileId)}/logo`,
      {
        method: "POST",
        headers: getAuthHeaders(request),
        body: formData,
      },
    )
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Upload failed" },
      { status: 500 },
    )
  }
}
