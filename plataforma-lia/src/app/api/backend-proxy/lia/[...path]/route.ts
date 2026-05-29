export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { isBackendUnavailableError } from './backend-error'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'
const MAX_BODY_SIZE = 2 * 1024 * 1024
const BACKEND_FETCH_TIMEOUT_MS = 8_000

const catchAllPathSchema = z.object({
  path: z.array(z.string().min(1)).min(1, 'Path is required'),
})

function getHeaders(request: NextRequest): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  // Forward user auth token (required for LIA endpoints)
  const auth = request.headers.get('Authorization')
  if (auth) {
    headers['Authorization'] = auth
  }

  const companyId = request.headers.get('X-Company-ID')
  if (companyId) headers['X-Company-ID'] = companyId

  const userId = request.headers.get('X-User-ID')
  if (userId) headers['X-User-ID'] = userId

  const userRole = request.headers.get('X-User-Role')
  if (userRole) headers['X-User-Role'] = userRole

  return headers
}

/**
 * Task #1177 — classify a `fetch()` rejection as "backend is not reachable
 * yet" (transient, retryable) vs. an unexpected proxy bug. Cold start on
 * Replit and rolling restarts in prod surface as ECONNREFUSED / ENOTFOUND /
 * AbortError, and clients (chiefly the wizard hydration in UnifiedChat) can
 * recover with a short retry — so we report 503 + `retryable: true` instead
 * of an opaque 500 that triggers the dev overlay and a hard toast.
 */
async function proxyRequest(
  request: NextRequest,
  params: Promise<{ path: string[] }>,
  method: string
): Promise<NextResponse> {
  try {
    const { path } = await params
    const pathValidation = catchAllPathSchema.safeParse({ path })
    if (!pathValidation.success) {
      return NextResponse.json({ error: 'Invalid path' }, { status: 400 })
    }
    const pathStr = path.join('/')
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()

    let backendUrl = `${BACKEND_URL}/api/v1/lia/${pathStr}`
    if (queryString) backendUrl = `${backendUrl}?${queryString}`

    const fetchOptions: RequestInit = {
      method,
      headers: getHeaders(request),
      signal: AbortSignal.timeout(BACKEND_FETCH_TIMEOUT_MS),
    }

    if (method !== 'GET' && method !== 'HEAD') {
      try {
        const body = await request.text()
        if (body.length > MAX_BODY_SIZE) {
          return NextResponse.json({ error: 'Request body too large' }, { status: 413 })
        }
        if (body) fetchOptions.body = body
      } catch { /* ignore empty body */ }
    }

    let response: Response
    try {
      response = await fetch(backendUrl, fetchOptions)
    } catch (fetchErr) {
      const cls = isBackendUnavailableError(fetchErr)
      if (cls.unavailable) {
        // Task #1177 — log at warn (not error) so the dev overlay stays
        // quiet during cold-start; the client retries this status.
        console.warn(
          `[lia-proxy] backend unavailable (${cls.code}) for ${method} /api/v1/lia/${pathStr}`,
        )
        return NextResponse.json(
          { error: 'backend unavailable', retryable: true, code: cls.code },
          { status: 503 },
        )
      }
      throw fetchErr
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      return NextResponse.json(
        { error: errorData.detail || 'LIA API request failed', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('[lia-proxy] error:', error)
    return NextResponse.json({ error: 'Failed to connect to backend' }, { status: 500 })
  }
}

type RouteParams = { params: Promise<{ path: string[] }> }

export async function GET(req: NextRequest, { params }: RouteParams) {
  return proxyRequest(req, params, 'GET')
}
export async function POST(req: NextRequest, { params }: RouteParams) {
  return proxyRequest(req, params, 'POST')
}
export async function PUT(req: NextRequest, { params }: RouteParams) {
  return proxyRequest(req, params, 'PUT')
}
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  return proxyRequest(req, params, 'PATCH')
}
export async function DELETE(req: NextRequest, { params }: RouteParams) {
  return proxyRequest(req, params, 'DELETE')
}
