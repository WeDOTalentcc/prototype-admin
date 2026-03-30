import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { z } from 'zod'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { noteId: string } }
) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/interview-notes/${params.noteId}`,
      { method: 'GET', headers: getAuthHeaders(request) }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Nota de entrevista não encontrada', details: errorData },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao conectar com o backend' }, { status: 500 })
  }
}

const _bodySchema = z.record(z.unknown())

export async function PATCH(
  request: NextRequest,
  { params }: { params: { noteId: string } }
) {
  try {
    const body = _bodySchema.parse(await request.json())

    const response = await fetch(
      `${BACKEND_URL}/api/v1/interview-notes/${params.noteId}`,
      {
        method: 'PATCH',
        headers: {
          ...getAuthHeaders(request),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar nota de entrevista', details: errorData },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao conectar com o backend' }, { status: 500 })
  }
}
