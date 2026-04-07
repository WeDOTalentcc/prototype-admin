export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { getWorkOSSession } from '@/lib/workos-session'
import { z } from 'zod'

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

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const headers = await getAuthHeaders(request)
    
    const backendUrl = `${BACKEND_URL}/api/v1/company/screening-questions/reorder`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao reordenar perguntas', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to reorder questions' },
      { status: 500 }
    )
  }
}
