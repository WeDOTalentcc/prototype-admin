import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { unwrapEnvelopeSuccess, unwrapEnvelopeError } from "@/lib/api/unwrapEnvelope"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const qs = searchParams.toString()
    const res = await fetch(
      `${BACKEND_URL}/api/v1/custom-agents/studio/compliance-summary${qs ? `?${qs}` : ""}`,
      { headers: getAuthHeaders(req) },
    )

    const rawText = await res.text()

    // Se o backend devolveu non-JSON, repassa verbatim preservando o
    // content-type real (mesmo comportamento do factory createProxyHandlers).
    const contentType = res.headers.get("content-type") || ""
    if (!contentType.includes("application/json")) {
      return new NextResponse(rawText, {
        status: res.status,
        headers: { "Content-Type": contentType || "text/plain" },
      })
    }

    let parsed: unknown
    try {
      parsed = JSON.parse(rawText)
    } catch {
      return new NextResponse(rawText, {
        status: res.status,
        headers: { "Content-Type": contentType },
      })
    }

    if (!res.ok) {
      // Desembrulha o envelope de erro do FastAPI (ResponseEnvelopeMiddleware)
      // para o frontend ver `{detail: {...}}` canônico.
      return NextResponse.json(unwrapEnvelopeError(parsed), { status: res.status })
    }

    // Desembrulha o envelope de sucesso `{ok, data, meta}` — o consumidor
    // (StudioComplianceView) espera o payload (`trend`, `top_blocked_agents`)
    // no topo, como faz o proxy factory createProxyHandlers. Sem isso,
    // `data.trend` chega undefined e o componente quebra em `.length`.
    return NextResponse.json(unwrapEnvelopeSuccess(parsed), { status: res.status })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
