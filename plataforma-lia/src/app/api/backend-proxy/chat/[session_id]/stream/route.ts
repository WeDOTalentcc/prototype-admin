import { NextRequest } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

// SSE-e2e (2026-06-04): proxy de streaming para o endpoint SSE do backend.
// Motivo: o sendMessageViaSSE batia DIRETO no backend (cross-origin) → o cookie
// de auth não ia e o ws-token (Bearer) falhava. Roteando pelo proxy (mesma
// origem), o cookie chega aqui e `getAuthHeaders` injeta o Bearer pro backend —
// mesma auth do REST que já funciona. Faz passthrough do stream SSE (sem buffer).
const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export const dynamic = "force-dynamic"
export const runtime = "nodejs"

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ session_id: string }> },
) {
  const { session_id } = await params
  const body = await request.text()
  const auth = getAuthHeaders(request) as Record<string, string>
  const lastEventId = request.headers.get("Last-Event-ID")

  let upstream: Response
  try {
    upstream = await fetch(
      `${BACKEND_URL}/api/v1/chat/${encodeURIComponent(session_id)}/stream`,
      {
        method: "POST",
        headers: {
          ...auth,
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          ...(lastEventId ? { "Last-Event-ID": lastEventId } : {}),
        },
        body,
      },
    )
  } catch (err) {
    return new Response(
      JSON.stringify({ error: "upstream_unreachable", detail: String(err) }),
      { status: 502, headers: { "Content-Type": "application/json" } },
    )
  }

  // Erro não-stream (401/4xx/5xx): repassa o corpo JSON como está.
  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text().catch(() => "")
    return new Response(text || JSON.stringify({ error: "upstream_error" }), {
      status: upstream.status || 502,
      headers: { "Content-Type": "application/json" },
    })
  }

  // Passthrough do stream SSE direto pro cliente (sem buffering).
  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
    },
  })
}
