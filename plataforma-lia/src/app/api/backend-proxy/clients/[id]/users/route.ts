import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { verifyAndDecodeSession, SessionPayload } from '@/lib/session-crypto'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
const WORKOS_SESSION_COOKIE = 'workos_session'
const IS_DEVELOPMENT = process.env.NODE_ENV === 'development'

interface AuthResult {
  success: true
  headers: Record<string, string>
  session: SessionPayload
}

interface AuthError {
  success: false
  response: NextResponse
}

async function getSessionAuth(): Promise<AuthResult | AuthError> {
  const cookieStore = await cookies()
  const sessionCookie = cookieStore.get(WORKOS_SESSION_COOKIE)

  if (!sessionCookie) {
    if (IS_DEVELOPMENT) {
      return {
        success: true,
        headers: {
          'Content-Type': 'application/json',
          'X-Company-ID': 'admin_company',
          'X-User-ID': 'admin_user',
          'X-User-Role': 'admin'
        },
        session: {} as SessionPayload
      }
    }
    return {
      success: false,
      response: NextResponse.json(
        { error: 'Não autenticado', code: 'UNAUTHORIZED' },
        { status: 401 }
      )
    }
  }

  const sessionData = verifyAndDecodeSession(sessionCookie.value)

  if (!sessionData) {
    if (IS_DEVELOPMENT) {
      return {
        success: true,
        headers: {
          'Content-Type': 'application/json',
          'X-Company-ID': 'admin_company',
          'X-User-ID': 'admin_user',
          'X-User-Role': 'admin'
        },
        session: {} as SessionPayload
      }
    }
    return {
      success: false,
      response: NextResponse.json(
        { error: 'Sessão inválida ou expirada', code: 'SESSION_EXPIRED' },
        { status: 401 }
      )
    }
  }

  const companyId = sessionData.workosProfile.organizationId || sessionData.workosProfile.id
  const userId = sessionData.workosProfile.id
  const userRole = sessionData.workosProfile.connectionType === 'SSO' ? 'admin' : 'user'

  return {
    success: true,
    headers: {
      'Content-Type': 'application/json',
      'X-Company-ID': companyId,
      'X-User-ID': userId,
      'X-User-Role': userRole
    },
    session: sessionData
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const authResult = await getSessionAuth()
    if (!authResult.success) {
      return authResult.response
    }

    const { id } = await params
    const { searchParams } = new URL(request.url)
    
    const queryString = searchParams.toString()
    const backendUrl = `${BACKEND_URL}/api/v1/clients/${id}/users${queryString ? `?${queryString}` : ''}`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: authResult.headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar usuários do cliente', details: errorData },
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

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const authResult = await getSessionAuth()
    if (!authResult.success) {
      return authResult.response
    }

    const { id } = await params
    const body = _bodySchema.parse(await request.json())
    
    const backendUrl = `${BACKEND_URL}/api/v1/clients/${id}/users`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: authResult.headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar usuário', details: errorData },
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
