/**
 * Proxy: POST /api/backend-proxy/navigation-intent
 *
 * Repassa para POST /api/v1/navigation-intent no backend.
 * Retorna { page, confidence, hint, matched_pattern }.
 */
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const response = await fetch(`${BACKEND_URL}/api/v1/navigation-intent`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: "navigation-intent error", details: err },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("navigation-intent proxy error:", error)
    return NextResponse.json(
      { error: "Internal error", message: error instanceof Error ? error.message : "Unknown" },
      { status: 500 }
    )
  }
}
