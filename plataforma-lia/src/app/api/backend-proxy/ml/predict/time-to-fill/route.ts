export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { z } from 'zod'

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"

/**
 * POST /api/backend-proxy/ml/predict/time-to-fill
 *
 * Proxy para previsão de tempo de preenchimento de vaga.
 * Mapeia para: POST /api/v1/ml/predict/time-to-fill
 */
const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())

    const response = await fetch(
      `${BACKEND_URL}/api/v1/ml/predict/time-to-fill`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    )

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { success: false, error: errorText || "Falha na previsão" },
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
