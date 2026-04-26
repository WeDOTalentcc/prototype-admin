export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { z } from 'zod'
import { validateQuery } from '@/lib/api/validate'
import { getAuthHeadersForForm } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"
const MAX_FILE_SIZE = 10 * 1024 * 1024

const uploadQuerySchema = z.object({
  title: z.string().optional().default(''),
  consent_acknowledged: z
    .enum(['true', 'false', '1', '0'])
    .optional()
    .transform((v) => v === 'true' || v === '1'),
})

export async function POST(request: NextRequest) {
  try {
    const queryValidation = validateQuery(request, uploadQuerySchema)
    if (!queryValidation.success) return queryValidation.response

    // Task #838 / M-09: backend now requires strict auth on JD upload.
    // Forward the caller's bearer token (Authorization header, lia_access_token
    // cookie, or workos_session) so legitimate users don't see 401s. `required`
    // is true so unauthenticated requests fail fast at the proxy with 401.
    let authHeaders: HeadersInit
    try {
      authHeaders = getAuthHeadersForForm(request, true)
    } catch {
      return NextResponse.json(
        { success: false, error: "Authentication required" },
        { status: 401 },
      )
    }

    const formData = await request.formData()
    const file = formData.get("file") as File
    if (file && file instanceof File && file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { success: false, error: "File too large (max 10MB)" },
        { status: 413 }
      )
    }

    const { title, consent_acknowledged } = queryValidation.data
    const url = new URL(`${BACKEND_URL}/api/v1/import/upload-file`)
    if (title) url.searchParams.set("title", title)
    if (consent_acknowledged) url.searchParams.set("consent_acknowledged", "true")

    const response = await fetch(url.toString(), {
      method: "POST",
      body: formData,
      headers: authHeaders,
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
