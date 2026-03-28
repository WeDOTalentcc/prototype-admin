/**
 * LIA Backend API Proxy
 * 
 * Encaminha todas as requisições de /api/lia/* para o backend FastAPI (porta 8000)
 * Necessário porque apenas a porta 5000 é exposta publicamente no Replit
 */

import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

async function proxyRequest(
  request: NextRequest,
  path: string[]
): Promise<NextResponse> {
  try {
    const pathname = path.join('/')
    const searchParams = request.nextUrl.searchParams.toString()
    const backendUrl = `${BACKEND_URL}/${pathname}${searchParams ? `?${searchParams}` : ''}`

    console.log(`[LIA Proxy] ${request.method} /${pathname} → ${backendUrl}`)

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
    let data: any

    if (responseContentType?.includes('application/json')) {
      data = await response.json()
    } else {
      data = await response.text()
    }

    if (!response.ok) {
      console.error(`[LIA Proxy] Error ${response.status}: ${JSON.stringify(data)}`)
      return NextResponse.json(
        { error: data.detail || data || 'Backend request failed' },
        { status: response.status }
      )
    }

    console.log(`[LIA Proxy] Success ${response.status}`)

    return NextResponse.json(data, { status: response.status })
    
  } catch (error) {
    console.error('[LIA Proxy] Request failed:', error)
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
