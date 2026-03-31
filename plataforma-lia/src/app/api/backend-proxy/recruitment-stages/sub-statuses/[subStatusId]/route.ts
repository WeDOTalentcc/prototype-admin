export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.LIA_BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const _bodySchema = z.record(z.string(), z.unknown())

export async function PATCH(
  request: NextRequest,
  { params }: { params: { subStatusId: string } }
) {
  try {
    const { subStatusId } = await params
    const body = _bodySchema.parse(await request.json())

    const response = await fetch(
      `${BACKEND_URL}/api/v1/recruitment-stages/sub-statuses/${subStatusId}`,
      {
        method: 'PATCH',
        headers: { ...getAuthHeaders(request), 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json({ error: 'Erro ao atualizar subetapa', details: errorData }, { status: response.status })
    }

    return NextResponse.json(await response.json())
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao conectar com o backend' }, { status: 500 })
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { subStatusId: string } }
) {
  try {
    const { subStatusId } = await params
    const body = _bodySchema.parse(await request.json())

    const response = await fetch(
      `${BACKEND_URL}/api/v1/recruitment-stages/sub-statuses/${subStatusId}`,
      {
        method: 'PUT',
        headers: { ...getAuthHeaders(request), 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json({ error: 'Erro ao atualizar subetapa', details: errorData }, { status: response.status })
    }

    return NextResponse.json(await response.json())
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao conectar com o backend' }, { status: 500 })
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { subStatusId: string } }
) {
  try {
    const { subStatusId } = await params

    const response = await fetch(
      `${BACKEND_URL}/api/v1/recruitment-stages/sub-statuses/${subStatusId}`,
      {
        method: 'DELETE',
        headers: getAuthHeaders(request),
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json({ error: 'Erro ao deletar subetapa', details: errorData }, { status: response.status })
    }

    return NextResponse.json(await response.json())
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao conectar com o backend' }, { status: 500 })
  }
}
