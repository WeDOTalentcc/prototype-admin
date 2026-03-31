export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    
    let backendUrl = `${BACKEND_URL}/api/v1/big-five/profiles`
    if (queryString) {
      backendUrl = `${backendUrl}?${queryString}`
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
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
    const body = _bodySchema.parse(await request.json())
    
    const backendUrl = `${BACKEND_URL}/api/v1/big-five/profiles`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
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
