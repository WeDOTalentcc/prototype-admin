/**
 * Proxy: GET /api/backend-proxy/agent-events/[session_id]
 *
 * Forwards SSE agent lifecycle events from the FastAPI backend to the browser.
 * Uses the same auth-header pattern as the chat stream proxy:
 *   - Auth cookie → getAuthHeaders() → Bearer token to backend
 *   - Last-Event-ID forwarded for reconnection replay
 *   - Passthrough of SSE stream (no buffering)
 */
import { NextRequest } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export const dynamic = "force-dynamic"
export const runtime = "nodejs"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ session_id: string }> },
): Promise<Response> {
  const { session_id } = await params
  const auth = getAuthHeaders(request) as Record<string, string>
  const lastEventId = request.headers.get("Last-Event-ID")

  let upstream: Response
  try {
    upstream = await fetch(
      `${BACKEND_URL}/api/v1/agent-events/${encodeURIComponent(session_id)}`,
      {
        method: "GET",
        headers: {
          ...auth,
          Accept: "text/event-stream",
          "Cache-Control": "no-cache",
          ...(lastEventId ? { "Last-Event-ID": lastEventId } : {}),
        },
      },
    )
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
      "Connection": "keep-alive",
    },
  })
}
