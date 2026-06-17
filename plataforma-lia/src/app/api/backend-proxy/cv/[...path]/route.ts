export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path } = await params
    const pathStr = path.join('/')
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    
    let backendUrl = `${BACKEND_URL}/api/v1/cv/${pathStr}`
    if (queryString) {
      backendUrl = `${backendUrl}?${queryString}`
    }
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    const authHeader = request.headers.get('Authorization')
    if (authHeader) {
      headers['Authorization'] = authHeader
    }
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      return NextResponse.json(
        { error: errorData.detail || 'CV parser request failed', details: errorData },
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

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path } = await params
    const pathStr = path.join('/')
    const backendUrl = `${BACKEND_URL}/api/v1/cv/${pathStr}`
    
    const contentType = request.headers.get('content-type') || ''
    const authHeader = request.headers.get('Authorization')
    
    const fetchOptions: RequestInit = {
      method: 'POST',
    }
    
    if (contentType.includes('multipart/form-data')) {
      const formData = await request.formData()
      fetchOptions.body = formData
      if (authHeader) {
        fetchOptions.headers = {
          'Authorization': authHeader
        }
      }
    } else {
      const bodyResult = await validateBody(request, _bodySchema)

      if (!bodyResult.success) return bodyResult.response

      const body = bodyResult.data
      fetchOptions.headers = {
        'Content-Type': 'application/json',
      }
      if (authHeader) {
        fetchOptions.headers['Authorization'] = authHeader
      }
      fetchOptions.body = JSON.stringify(body)
    }
    
    const response = await fetch(backendUrl, fetchOptions)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }))
      return NextResponse.json(
        { error: errorData.detail || 'CV parser request failed', details: errorData },
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
