export const dynamic = "force-dynamic"
import { NextRequest } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const queryString = searchParams.toString()
  const url = `${BACKEND_URL}/api/v1/recruitment-stages/transition/return-event/stream${queryString ? "?" + queryString : ""}`

  const headers = getAuthHeaders(request)

  try {
    const response = await fetch(url, {
      headers,
    })

    if (!response.ok || !response.body) {
      return new Response(JSON.stringify({ error: "SSE connection failed" }), {
        status: response.status,
        headers: { "Content-Type": "application/json" },
      })
    }

    return new Response(response.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    })
  } catch {
    return new Response(JSON.stringify({ error: "Failed to connect to backend" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    })
  }
}
