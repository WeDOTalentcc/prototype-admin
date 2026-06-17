export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders as canonicalAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(request: NextRequest): HeadersInit {
  // Multipart upload: canonical helper sets Content-Type: application/json,
  // which interferes with FormData boundary auto-detection. Strip it.
  // Auditoria 2026-05-22: ainda forwarda JWT via canonical (cookie fallback).
  const { "Content-Type": _ct, ...rest } = canonicalAuthHeaders(request) as Record<string, string>
  return rest
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
