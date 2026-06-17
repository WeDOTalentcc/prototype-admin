export const dynamic = "force-dynamic"
/**
 * POST /api/backend-proxy/messages/schedule
 *
 * Proxy for POST /api/v1/communication/schedule-message on the FastAPI backend.
 * GAP-07-007 — recruiter-initiated message scheduling.
 *
 * Forwards auth headers (JWT) so the backend can extract company_id.
 * Never injects company_id from payload — multi-tenancy enforced by BE.
 */
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json().catch(() => null)

    if (!body) {
      return NextResponse.json(
        { success: false, error: "Request body is required" },
        { status: 400 }
      )
    }

    const backendUrl = `${BACKEND_URL}/api/v1/communication/schedule-message`

    const response = await fetch(backendUrl, {
      method: "POST",
      headers: {
        ...getAuthHeaders(request),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        candidate_id: body.candidate_id,
        candidate_name: body.candidate_name,
        vacancy_id: body.vacancy_id,
        channel: body.channel,
        message: body.message,
        subject: body.subject,
        send_at: body.send_at,
      }),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      return NextResponse.json(
        {
          success: false,
          error: data?.detail?.message ?? data?.detail ?? "Erro ao agendar mensagem",
          details: data,
        },
        { status: response.status }
      )
    }

    return NextResponse.json(data, { status: 201 })
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: "Erro ao conectar com o backend",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    )
  }
}
