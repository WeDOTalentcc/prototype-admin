import { NextRequest } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

// GAP-09-001: SSE proxy for kanban real-time broadcast.
// GET request — client opens EventSource, backend streams candidate stage changes.
const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export const dynamic = "force-dynamic"
export const runtime = "nodejs"

export async function GET(request: NextRequest) {
  const auth = getAuthHeaders(request) as Record<string, string>
  const jobId = request.nextUrl.searchParams.get("job_id") || ""
  const params = jobId ? `?job_id=${encodeURIComponent(jobId)}` : ""

  let upstream: Response
  try {
    upstream = await fetch(`${BACKEND_URL}/api/v1/kanban/events${params}`, {
      method: "GET",
      headers: {
        ...auth,
        Accept: "text/event-stream",
      },
    })
  } catch (err) {
    return new Response(
      JSON.stringify({ error: "upstream_unreachable", detail: String(err) }),
      { status: 502, headers: { "Content-Type": "application/json" } },
    )
  }

  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text().catch(() => "")
    return new Response(text || JSON.stringify({ error: "upstream_error" }), {
      status: upstream.status || 502,
      headers: { "Content-Type": "application/json" },
    })
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
    },
  })
}
