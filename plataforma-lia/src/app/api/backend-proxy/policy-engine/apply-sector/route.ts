import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"

/**
 * POST /api/backend-proxy/policy-engine/apply-sector
 *
 * Proxy para aplicar templates de política por setor.
 * Mapeia para: POST /api/v1/policy-engine/apply-sector/{companyId}?sector=
 */
export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const companyId = searchParams.get("companyId") || ""
    const sector = searchParams.get("sector") || ""

    if (!companyId) {
      return NextResponse.json(
        { success: false, error: "companyId é obrigatório" },
        { status: 400 },
      )
    }

    const url = new URL(
      `${BACKEND_URL}/api/v1/policy-engine/apply-sector/${companyId}`,
    )
    if (sector) url.searchParams.set("sector", sector)

    const response = await fetch(url.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { success: false, error: errorText || "Falha ao aplicar setor" },
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
