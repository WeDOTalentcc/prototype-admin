export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

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

const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())
    
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
