export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.LIA_BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { stageId: string } }
) {
  try {
    const { stageId } = await params
    const { searchParams } = new URL(request.url)
    const includeInactive = searchParams.get('include_inactive') === 'true'

    const backendUrl = new URL(`${BACKEND_URL}/api/v1/recruitment-stages/stages/${stageId}/sub-statuses`)
    if (includeInactive) backendUrl.searchParams.set('include_inactive', 'true')

    const response = await fetch(backendUrl.toString(), { headers: getAuthHeaders(request) })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ error: 'Erro ao buscar subetapas', details: errorData }, { status: response.status })
    }

    return NextResponse.json(await response.json())
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao conectar com o backend' }, { status: 500 })
  }
}
