export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { z } from 'zod'

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://127.0.0.1:8000"
const MAX_FILE_SIZE = 10 * 1024 * 1024

/**
 * POST /api/backend-proxy/jd-import/upload
 *
 * Faz proxy de upload de arquivo JD para o backend.
 * Repassa multipart/form-data sem transformação.
 */
export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File
    if (file && file instanceof File && file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { success: false, error: "File too large (max 10MB)" },
        { status: 413 }
      )
    }
    const { searchParams } = new URL(request.url)
    const title = searchParams.get("title") || ""

    const url = new URL(`${BACKEND_URL}/api/v1/import/upload-file`)
    if (title) url.searchParams.set("title", title)

    const response = await fetch(url.toString(), {
      method: "POST",
      body: formData,
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { success: false, error: errorText || "Falha no upload" },
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
