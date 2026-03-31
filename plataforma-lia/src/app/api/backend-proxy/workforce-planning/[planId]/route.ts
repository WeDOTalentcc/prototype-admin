export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

function getHeaders(request: NextRequest) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
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
  { params }: { params: Promise<{ planId: string }> }
) {
  try {
    const { planId } = await params
    const backendUrl = `${BACKEND_URL}/api/v1/workforce-planning/${planId}`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar workforce plan', details: errorData },
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

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ planId: string }> }
) {
  try {
    const { planId } = await params
    const body = _bodySchema.parse(await request.json())
    
    const backendUrl = `${BACKEND_URL}/api/v1/workforce-planning/${planId}`
    
    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: getHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar workforce plan', details: errorData },
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

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ planId: string }> }
) {
  try {
    const { planId } = await params
    const backendUrl = `${BACKEND_URL}/api/v1/workforce-planning/${planId}`
    
    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers: getHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao excluir workforce plan', details: errorData },
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
