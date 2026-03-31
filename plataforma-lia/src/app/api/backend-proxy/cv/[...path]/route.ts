export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
const SERVICE_API_TOKEN = process.env.SERVICE_API_TOKEN || ''

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
    if (SERVICE_API_TOKEN) {
      headers['Authorization'] = `Bearer ${SERVICE_API_TOKEN}`
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
    
    const fetchOptions: RequestInit = {
      method: 'POST',
    }
    
    if (contentType.includes('multipart/form-data')) {
      const formData = await request.formData()
      fetchOptions.body = formData
      if (SERVICE_API_TOKEN) {
        fetchOptions.headers = {
          'Authorization': `Bearer ${SERVICE_API_TOKEN}`
        }
      }
    } else {
      const body = _bodySchema.parse(await request.json())
      fetchOptions.headers = {
        'Content-Type': 'application/json',
      }
      if (SERVICE_API_TOKEN) {
        fetchOptions.headers['Authorization'] = `Bearer ${SERVICE_API_TOKEN}`
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
