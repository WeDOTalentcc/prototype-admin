export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateParams, validateBody } from '@/lib/api/validate'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const routeParamsSchema = z.object({
  listId: z.string().min(1, 'listId is required'),
})


const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(
  request: NextRequest,
  { params: pRaw }: { params: Promise<{ listId: string }> }
) {
  try {
    const { listId } = await pRaw
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const backendUrl = `${BACKEND_URL}/api/v1/short-lists/${listId}/candidates${queryString ? `?${queryString}` : ''}`

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: { ...getAuthHeaders(request), 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao adicionar candidato', details: errorData },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json(), { status: 201 })
  } catch (error) {
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
