export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

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

async function proxyRequest(
  request: NextRequest,
  params: Promise<{ path: string[] }>,
  method: string
): Promise<NextResponse> {
  try {
    const { path } = await params
    const pathStr = path.join('/')
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()

    let backendUrl = `${BACKEND_URL}/api/v1/lia/${pathStr}`
    if (queryString) backendUrl = `${backendUrl}?${queryString}`

    const fetchOptions: RequestInit = { method, headers: getHeaders(request) }

    if (method !== 'GET' && method !== 'HEAD') {
      try {
        const body = await request.text()
        if (body) fetchOptions.body = body
      } catch { /* ignore empty body */ }
    }

    const response = await fetch(backendUrl, fetchOptions)

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
