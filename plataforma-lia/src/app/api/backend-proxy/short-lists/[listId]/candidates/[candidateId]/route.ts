export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const routeParamsSchema = z.object({
  listId: z.string().min(1, 'listId is required'),
  candidateId: z.string().min(1, 'candidateId is required'),
})

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ listId: string; candidateId: string }> }
) {
  try {
    const { listId, candidateId } = await params
    const paramValidation = validateParams({ listId, candidateId }, routeParamsSchema)
    if (!paramValidation.success) return paramValidation.response
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    const backendUrl = `${BACKEND_URL}/api/v1/short-lists/${listId}/candidates/${candidateId}${queryString ? `?${queryString}` : ''}`

    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao remover candidato', details: errorData },
        { status: response.status }
      )
    }

    return new NextResponse(null, { status: 204 })
  } catch (error) {
    return NextResponse.json({ error: 'Erro interno' }, { status: 500 })
  }
}
