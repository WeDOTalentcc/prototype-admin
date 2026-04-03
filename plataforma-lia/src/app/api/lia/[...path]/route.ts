export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
const MAX_BODY_SIZE = 2 * 1024 * 1024

const catchAllPathSchema = z.object({
  path: z.array(z.string().min(1)).min(1, 'Path is required'),
})

async function proxyRequest(
  request: NextRequest,
  path: string[]
): Promise<NextResponse> {
  try {
    const pathValidation = catchAllPathSchema.safeParse({ path })
    if (!pathValidation.success) {
      return NextResponse.json({ error: 'Invalid path' }, { status: 400 })
    }

    const pathname = path.join('/')
    const searchParams = request.nextUrl.searchParams.toString()
    const backendUrl = `${BACKEND_URL}/${pathname}${searchParams ? `?${searchParams}` : ''}`

    const contentType = request.headers.get('content-type')
    const isMultipart = contentType?.includes('multipart/form-data')
    
    const headers: HeadersInit = {}
    
    if (!isMultipart && contentType) {
      headers['Content-Type'] = contentType
    }

    const options: RequestInit = {
      method: request.method,
      headers,
    }

    if (request.method !== 'GET' && request.method !== 'HEAD') {
      if (isMultipart) {
        const formData = await request.formData()
        options.body = formData
      } else {
        const body = await request.text()
        if (body.length > MAX_BODY_SIZE) {
          return NextResponse.json({ error: 'Request body too large' }, { status: 413 })
        }
        if (body) {
          options.body = body
          if (!contentType) {
            headers['Content-Type'] = 'application/json'
          }
        }
      }
    }

    const response = await fetch(backendUrl, options)

    const responseContentType = response.headers.get('content-type')
    let data: unknown

    if (responseContentType?.includes('application/json')) {
      data = await response.json()
    } else {
      data = await response.text()
    }

    if (!response.ok) {
      return NextResponse.json(
        { error: (data as Record<string, unknown>)?.detail || data || 'Backend request failed' },
        { status: response.status }
      )
    }


    return NextResponse.json(data, { status: response.status })
    
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to connect to LIA backend' },
      { status: 500 }
    )
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  return proxyRequest(request, resolvedParams.path)
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  return proxyRequest(request, resolvedParams.path)
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  return proxyRequest(request, resolvedParams.path)
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  return proxyRequest(request, resolvedParams.path)
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params
  return proxyRequest(request, resolvedParams.path)
}
