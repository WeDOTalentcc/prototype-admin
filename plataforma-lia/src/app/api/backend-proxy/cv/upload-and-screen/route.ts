export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

/**
 * POST /api/backend-proxy/cv/upload-and-screen
 *
 * Proxies to backend POST /api/v1/cv/upload-and-screen
 * Accepts: multipart/form-data with file + optional vacancy info
 * OR: application/json with cv_text + optional vacancy info
 *
 * Returns: { success, candidate_id, candidate_name, match_score, recommendation, message, parsed }
 */
export async function POST(request: NextRequest) {
  try {
    const contentType = request.headers.get('content-type') || ''
    const authHeaders = getAuthHeaders(request)

    let backendResponse: Response

    if (contentType.includes('multipart/form-data')) {
      // Forward multipart form data directly
      const formData = await request.formData()
      backendResponse = await fetch(`${BACKEND_URL}/api/v1/cv/upload-and-screen`, {
        method: 'POST',
        headers: {
          ...authHeaders,
          // Don't set Content-Type for multipart — fetch sets it with boundary
        },
        body: formData,
      })
    } else {
      // JSON body with cv_text
      const body = await request.json()
      const formData = new FormData()
      if (body.cv_text) formData.append('cv_text', body.cv_text)
      if (body.vacancy_title) formData.append('vacancy_title', body.vacancy_title)
      if (body.vacancy_id) formData.append('vacancy_id', body.vacancy_id)
      if (body.run_bars !== undefined) formData.append('run_bars', String(body.run_bars))

      backendResponse = await fetch(`${BACKEND_URL}/api/v1/cv/upload-and-screen`, {
        method: 'POST',
        headers: authHeaders,
        body: formData,
      })
    }

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({}))
      return NextResponse.json(
        { success: false, error: 'Erro ao processar CV', details: errorData },
        { status: backendResponse.status }
      )
    }

    const data = await backendResponse.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('[CV upload-and-screen proxy]', error)
    return NextResponse.json(
      { success: false, error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
