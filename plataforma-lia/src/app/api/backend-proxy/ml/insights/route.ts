export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { getAuthHeaders } from "@/lib/api/auth-headers"
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

/**
 * POST /api/backend-proxy/ml/insights
 *
 * Proxy para insights de hiring via ML.
 * Mapeia para: POST /api/v1/ml/insights/hiring
 */
const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data

    const response = await fetch(`${BACKEND_URL}/api/v1/ml/insights/hiring`, {
      method: "POST",
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { success: false, error: errorText || "Falha ao obter insights" },
        { status: response.status },
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Erro de conexão com o backend" },
      { status: 500 },
    )
  }
}
