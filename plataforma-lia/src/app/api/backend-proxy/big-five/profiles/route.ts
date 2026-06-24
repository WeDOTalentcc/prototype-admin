export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    
    let backendUrl = `${BACKEND_URL}/api/v1/big-five/profiles`
    if (queryString) {
      backendUrl = `${backendUrl}?${queryString}`
    }

    const headers: Record<string, string> = {
      ...(getAuthHeaders(request) as Record<string, string>),
    }

    const companyId = request.headers.get('X-Company-ID')
    const userId = request.headers.get('X-User-ID')
    const userRole = request.headers.get('X-User-Role')

    if (companyId) headers['X-Company-ID'] = companyId
    if (userId) headers['X-User-ID'] = userId
    if (userRole) headers['X-User-Role'] = userRole

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ 
        error: 'Erro ao buscar perfis Big Five', 
        details: errorData,
        status: response.status 
      }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ 
      error: 'Erro ao conectar com o backend',
      status: 500 
    }, { status: 500 })
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const backendUrl = `${BACKEND_URL}/api/v1/big-five/profiles`

    const headers: Record<string, string> = {
      ...(getAuthHeaders(request) as Record<string, string>),
    }

    const companyId = request.headers.get('X-Company-ID')
    const userId = request.headers.get('X-User-ID')
    const userRole = request.headers.get('X-User-Role')

    if (companyId) headers['X-Company-ID'] = companyId
    if (userId) headers['X-User-ID'] = userId
    if (userRole) headers['X-User-Role'] = userRole

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar perfil Big Five', details: errorData },
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
