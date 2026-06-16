// P1-W2-11: migrado — fix fallback silencioso
// GET: 404 retorna defaults com isDefault:true (empresa nova = legítimo)
//      5xx retorna erro real (não esconde falha de backend como HTTP 200)
// PUT: sem mudança de comportamento
export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

// P2-W2: manual proxy implementation (uses BACKEND_URL env var correctly).
// TODO: migrate to createProxyHandlers({backendTarget:"fastapi"}) to align with other proxy patterns.
const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

const DEFAULT_COMMUNICATION_SETTINGS = {
  isDefault: true,
  signature: "",
  sending_hours_start: 8,
  sending_hours_end: 20,
  respect_holidays: true,
  respect_weekends: true,
  max_messages_per_day: 3,
}

export async function GET(request: NextRequest) {
  try {
    const backendUrl = BACKEND_URL + "/api/v1/company/communication-settings"
    // REGRA 6 CLAUDE.md (2026-05-22 audit): nao forwardar X-Company-ID do
    // browser — JWT canonical via getAuthHeaders ja carrega company_id.
    const response = await fetch(backendUrl, {
      method: "GET",
      headers: getAuthHeaders(request),
      signal: AbortSignal.timeout(15000),
    })

    if (response.status === 404) {
      // P1-W2-11: empresa nova sem config = legítimo, retornar defaults com flag
      return NextResponse.json(DEFAULT_COMMUNICATION_SETTINGS)
    }

    if (!response.ok) {
      // P1-W2-11: falha real de backend — não mascarar como HTTP 200 com defaults
      return NextResponse.json(
        { error: "Erro ao carregar configurações de comunicação" },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: "Erro ao conectar com o backend" },
      { status: 502 }
    )
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    const backendUrl = BACKEND_URL + "/api/v1/company/communication-settings"
    // REGRA 6 CLAUDE.md (2026-05-22 audit): nao forwardar X-Company-ID.
    const response = await fetch(backendUrl, {
      method: "PUT",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(15000),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: "Erro ao salvar configurações de comunicação", details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { error: "Erro ao conectar com o backend" },
      { status: 500 }
    )
  }
}
