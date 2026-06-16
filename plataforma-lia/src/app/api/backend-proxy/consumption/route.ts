export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

/**
 * Backend proxy for /api/v1/consumption/* endpoints.
 * Query params:
 *   path: "budget-status" | "report" | "dashboard" | "tenant-summary" | ...
 * Additional query params are passed through to backend.
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const path = searchParams.get("path") || "dashboard"

    // Forward all other query params
    const forwarded = new URLSearchParams()
    searchParams.forEach((value, key) => {
      if (key !== "path") forwarded.append(key, value)
    })

    const qs = forwarded.toString() ? `?${forwarded.toString()}` : ""
    const url = `${BACKEND_URL}/api/v1/consumption/${path}${qs}`

    const response = await fetch(url, { headers: getAuthHeaders(request) })
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to fetch consumption data" },
      { status: 500 },
    )
  }
}
