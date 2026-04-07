export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { cookies } from 'next/headers'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

async function getAuthHeaders(request: NextRequest): Promise<HeadersInit> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  
  const authHeader = request.headers.get('Authorization')
  if (authHeader) {
    headers['Authorization'] = authHeader
  }
  
  const cookieStore = await cookies()
  const accessToken = cookieStore.get('access_token')?.value
  if (accessToken && !authHeader) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }
  
  return headers
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const params = new URLSearchParams()
    
    if (searchParams.get('company_id')) params.set('company_id', searchParams.get('company_id')!)
    if (searchParams.get('module')) params.set('module', searchParams.get('module')!)
    if (searchParams.get('is_active')) params.set('is_active', searchParams.get('is_active')!)
    
    const backendUrl = `${BACKEND_URL}/api/v1/communication-matrix?${params.toString()}`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: await getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar matriz de comunicações', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
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
    
    const backendUrl = `${BACKEND_URL}/api/v1/communication-matrix/seed`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: await getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao popular matriz', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
