export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server"
import { z } from 'zod'
import { validateQuery } from '@/lib/api/validate'
import { getAuthHeadersForForm } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

import { resolveMaxFileSize } from '@/constants/upload'
const MAX_FILE_SIZE = resolveMaxFileSize()
const MAX_FILE_SIZE_MB = Math.max(1, Math.floor(MAX_FILE_SIZE / (1024 * 1024)))

const uploadQuerySchema = z.object({
  title: z.string().optional().default(''),
  consent_acknowledged: z
    .enum(['true', 'false', '1', '0'])
    .optional()
    .transform((v) => v === 'true' || v === '1'),
  // Audit B-02 / Task #858 — id da sessão WebSocket que receberá os
  // `background_task_update` enquanto o worker processa o upload de forma
  // assíncrona. Opcional; quando omitido o backend simplesmente não publica
  // progresso e o cliente precisa consultar status por outro canal.
  session_id: z.string().min(1).max(128).optional(),
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
        { success: false, error: `File too large (max ${MAX_FILE_SIZE_MB}MB)` },
        { status: 413 }
      )
    }

    const { title, consent_acknowledged, session_id } = queryValidation.data
    const url = new URL(`${BACKEND_URL}/api/v1/import/upload-file`)
    if (title) url.searchParams.set("title", title)
    if (consent_acknowledged) url.searchParams.set("consent_acknowledged", "true")
    // Forward session_id so the worker can publish background_task_update
    // events back to the requesting WS session (Audit B-02 / Task #858).
    if (session_id) url.searchParams.set("session_id", session_id)

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

    // Backend now returns 202 + task_id (Audit B-02 / Task #858) — preserve
    // the upstream status so clients can route on `queued` vs `created`.
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Erro de conexão com o backend" },
      { status: 500 },
    )
  }
}
