export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { validateBody } from "@/lib/api/validate"
import { z } from "zod"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function GET(request: NextRequest) {
  try {
    const headers = getAuthHeaders(request)
    const response = await fetch(`${BACKEND_URL}/api/v1/company/offer-rules`, {
      method: "GET",
      headers,
      signal: AbortSignal.timeout(8000),
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      return NextResponse.json({ error: "Erro ao buscar regras de oferta", details: err }, { status: response.status })
    }

    const data = await response.json()
    const unwrapped = data?.ok === true && "data" in data ? data.data : data
    return NextResponse.json(unwrapped)
  } catch {
    return NextResponse.json({ error: "Erro ao conectar com o backend" }, { status: 500 })
  }
}

const _schema = z.record(z.string(), z.unknown())

export async function PUT(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _schema)
    if (!bodyResult.success) return bodyResult.response

    const headers = getAuthHeaders(request)
    const response = await fetch(`${BACKEND_URL}/api/v1/company/offer-rules`, {
      method: "PUT",
      headers,
      signal: AbortSignal.timeout(8000),
      body: JSON.stringify(bodyResult.data),
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      return NextResponse.json({ error: "Erro ao salvar regras de oferta", details: err }, { status: response.status })
    }

    const data = await response.json()
    const unwrapped = data?.ok === true && "data" in data ? data.data : data
    return NextResponse.json(unwrapped)
  } catch {
    return NextResponse.json({ error: "Erro ao conectar com o backend" }, { status: 500 })
  }
}
