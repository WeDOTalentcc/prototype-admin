export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

function getAuthHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const authHeader = request.headers.get('authorization')
  if (authHeader) {
    headers['Authorization'] = authHeader
  }
  const cookie = request.headers.get('cookie')
  if (cookie) {
    headers['Cookie'] = cookie
  }
  return headers
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    
    let backendUrl = `${BACKEND_URL}/api/v1/company/profile`
    if (queryString) {
      backendUrl = `${backendUrl}?${queryString}`
    }
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (response.status === 404) {
      return NextResponse.json({ notFound: true, status: 404 })
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ 
        error: 'Erro ao buscar perfil da empresa', 
        details: errorData,
        status: response.status 
      })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({ 
      error: 'Erro ao conectar com o backend',
      status: 500 
    })
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const backendUrl = `${BACKEND_URL}/api/v1/company/profile`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: getAuthHeaders(request),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar perfil da empresa', details: errorData },
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

export async function PUT(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const authHeaders = getAuthHeaders(request)
    const getResponse = await fetch(`${BACKEND_URL}/api/v1/company/profile`, {
      method: 'GET',
      headers: authHeaders,
    })
    
    if (!getResponse.ok) {
      if (getResponse.status === 404 || getResponse.status === 400) {
        const createResponse = await fetch(`${BACKEND_URL}/api/v1/company/profile`, {
          method: 'POST',
          headers: authHeaders,
          body: JSON.stringify(body),
        })
        
        if (!createResponse.ok) {
          const errorData = await createResponse.json().catch(() => ({}))
          return NextResponse.json(
            { error: 'Erro ao criar perfil da empresa', details: errorData },
            { status: createResponse.status }
          )
        }
        
        const data = await createResponse.json()
        return NextResponse.json(data)
      }
      
      const errorData = await getResponse.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar perfil da empresa', details: errorData },
        { status: getResponse.status }
      )
    }
    
    const profile = await getResponse.json()
    const profileId = profile.id
    
    const backendUrl = `${BACKEND_URL}/api/v1/company/profile/${profileId}`
    
    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: authHeaders,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar perfil da empresa', details: errorData },
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
