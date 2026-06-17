export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json() as {
      candidate_ids: string[]
      vacancy_id?: string
      send_notification?: boolean
    }

    const backendPath = "/api/v1/candidates/bulk/request-data"
    const response = await fetch(`${BACKEND_URL}${backendPath}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(request.headers.get("Authorization")
          ? { Authorization: request.headers.get("Authorization")! }
          : {}),
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: "Erro ao solicitar dados dos candidatos", details: errorData },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch (error) {
    return NextResponse.json(
      { error: "Erro ao conectar com o backend" },
      { status: 500 }
    )
  }
}
