export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getWorkOSSession } from '@/lib/workos-session'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

async function getAuthHeaders(request: NextRequest) {
  const session = await getWorkOSSession()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (session?.accessToken) {
    headers['Authorization'] = `Bearer ${session.accessToken}`
  }
  const companyId = request.headers.get('x-company-id')
  if (companyId) {
    headers['x-company-id'] = companyId
  }
  return headers
}

export async function POST(request: NextRequest) {
  try {
    const headers = await getAuthHeaders(request)
    
    const backendUrl = `${BACKEND_URL}/api/v1/company/screening-questions/seed`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar perguntas padrão', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to seed questions' },
      { status: 500 }
    )
  }
}
