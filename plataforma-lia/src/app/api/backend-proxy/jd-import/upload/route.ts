export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { z } from 'zod'
import { validateQuery } from '@/lib/api/validate'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"
const MAX_FILE_SIZE = 10 * 1024 * 1024

const uploadQuerySchema = z.object({
  title: z.string().optional().default(''),
})

export async function POST(request: NextRequest) {
  try {
    const queryValidation = validateQuery(request, uploadQuerySchema)
    if (!queryValidation.success) return queryValidation.response

    const formData = await request.formData()
    const file = formData.get("file") as File
    if (file && file instanceof File && file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { success: false, error: "File too large (max 10MB)" },
        { status: 413 }
      )
    }

    const { title } = queryValidation.data
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
