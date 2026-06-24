export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

function getHeaders(request: NextRequest) {
  const headers: Record<string, string> = {
    ...(getAuthHeaders(request) as Record<string, string>),
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

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    
    let backendUrl = `${BACKEND_URL}/api/v1/workforce-planning`
    
    const year = searchParams.get('year')
    const status = searchParams.get('status')
    
    const params = new URLSearchParams()
    if (year) params.append('year', year)
    if (status) params.append('status', status)
    
    if (params.toString()) {
      backendUrl = `${backendUrl}?${params.toString()}`
    }
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar workforce plans', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    // T-1171: unwrap envelope canonico {ok, data, meta} do FastAPI
    const unwrapped = data && typeof data === "object" && "ok" in data && "data" in data ? (data as Record<string, unknown>).data : data
    return NextResponse.json(unwrapped)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const backendUrl = `${BACKEND_URL}/api/v1/workforce-planning`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar workforce plan', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data, { status: 201 })
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
