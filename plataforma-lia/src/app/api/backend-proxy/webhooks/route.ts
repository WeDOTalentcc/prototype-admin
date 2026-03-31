export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

function getAuthHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Company-ID': 'demo_company',
    'X-User-ID': 'admin_user',
    'X-User-Role': 'admin'
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const params = new URLSearchParams()
    
    if (searchParams.get('is_active')) params.set('is_active', searchParams.get('is_active')!)
    if (searchParams.get('event')) params.set('event', searchParams.get('event')!)
    if (searchParams.get('limit')) params.set('limit', searchParams.get('limit')!)
    if (searchParams.get('offset')) params.set('offset', searchParams.get('offset')!)
    
    const backendUrl = `${BACKEND_URL}/api/v1/webhooks?${params.toString()}`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar webhooks', details: errorData },
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

const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())
    
    const backendUrl = `${BACKEND_URL}/api/v1/webhooks`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar webhook', details: errorData },
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
