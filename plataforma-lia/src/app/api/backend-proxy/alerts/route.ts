
export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const severity = searchParams.get('severity')
    const userId = searchParams.get('user_id')
    const limit = searchParams.get('limit') || '50'
    
    let backendUrl = `${BACKEND_URL}/api/v1/alerts/?limit=${limit}`
    if (severity) backendUrl += `&severity=${severity}`
    if (userId) backendUrl += `&user_id=${userId}`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao buscar alertas' },
        { status: response.status }
      )
    }

    const data = await response.json()
    // Unwrap FastAPI envelope: {ok: true, data: [...], meta: {}}
    const payload = (data && typeof data === 'object' && 'ok' in data && 'data' in data) ? data.data : data
    return NextResponse.json(payload)
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
    
    const backendUrl = `${BACKEND_URL}/api/v1/alerts/check`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Erro ao verificar alertas' },
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
