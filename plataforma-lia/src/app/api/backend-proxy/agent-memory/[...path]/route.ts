export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const catchAllPathSchema = z.object({
  path: z.array(z.string().min(1)).min(1, 'Path is required'),
})
function getHeaders(request: NextRequest): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  const authHeader = request.headers.get('Authorization')
  if (authHeader) {
    headers['Authorization'] = authHeader
  }

  const companyId = request.headers.get('X-Company-ID')
  if (companyId) {
    headers['X-Company-ID'] = companyId
  }

  const userId = request.headers.get('X-User-ID')
  if (userId) {
    headers['X-User-ID'] = userId
  }

  const userRole = request.headers.get('X-User-Role')
  if (userRole) {
    headers['X-User-Role'] = userRole
  }

  return headers
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path } = await params
    const pathValidation = catchAllPathSchema.safeParse({ path })
    if (!pathValidation.success) {
      return NextResponse.json({ error: 'Invalid path' }, { status: 400 })
    }
    const pathStr = path.join('/')
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    
    let backendUrl = `${BACKEND_URL}/api/v1/agent-memory/${pathStr}`
    if (queryString) {
      backendUrl = `${backendUrl}?${queryString}`
    }
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      return NextResponse.json(
        { error: errorData.detail || 'Agent memory API request failed', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path } = await params
    const pathValidation = catchAllPathSchema.safeParse({ path })
    if (!pathValidation.success) {
      return NextResponse.json({ error: 'Invalid path' }, { status: 400 })
    }
    const pathStr = path.join('/')
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()

    let backendUrl = `${BACKEND_URL}/api/v1/agent-memory/${pathStr}`
    if (queryString) {
      backendUrl = `${backendUrl}?${queryString}`
    }
    
    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers: getHeaders(request),
    })

    if (response.status === 204) {
      return new NextResponse(null, { status: 204 })
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      return NextResponse.json(
        { error: errorData.detail || 'Agent memory API request failed', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 500 }
    )
  }
}
