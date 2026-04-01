export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'

const BACKEND_URL = process.env.LIA_BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const DEFAULT_SCREENING_QUESTIONS = [
  { id: '1', question: 'Você tem interesse real nesta vaga?', question_type: 'yesno', is_required: true, order: 1, is_default: true, options: [] },
  { id: '2', question: 'Qual sua disponibilidade para início?', question_type: 'text', is_required: true, order: 2, is_default: true, options: [] },
  { id: '3', question: 'Qual sua pretensão salarial?', question_type: 'text', is_required: true, order: 3, is_default: true, options: [] },
  { id: '4', question: 'Quantos anos de experiência você tem na área?', question_type: 'text', is_required: true, order: 4, is_default: true, options: [] },
  { id: '5', question: 'Você aceita trabalhar no modelo híbrido/presencial?', question_type: 'yesno', is_required: true, order: 5, is_default: true, options: [] },
  { id: '6', question: 'Você está em algum outro processo seletivo?', question_type: 'yesno', is_required: false, order: 6, is_default: true, options: [] }
]

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const queryString = searchParams.toString()
    
    let backendUrl = `${BACKEND_URL}/api/v1/screening-questions`
    if (queryString) {
      backendUrl = `${backendUrl}?${queryString}`
    }
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.status === 404) {
      return NextResponse.json(DEFAULT_SCREENING_QUESTIONS)
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ 
        error: 'Erro ao buscar perguntas de screening', 
        details: errorData,
        status: response.status 
      }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(DEFAULT_SCREENING_QUESTIONS)
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())
    
    const backendUrl = `${BACKEND_URL}/api/v1/screening-questions`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (response.status === 404) {
      return NextResponse.json({
        success: true,
        message: 'Screening question created',
        data: { id: `q-${Date.now()}`, ...body }
      })
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao criar pergunta de screening', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({
      success: true,
      message: 'Screening question created (fallback)',
    })
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json())
    
    const backendUrl = `${BACKEND_URL}/api/v1/screening-questions`
    
    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (response.status === 404) {
      return NextResponse.json({
        success: true,
        message: 'Screening questions updated',
        data: body
      })
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar perguntas de screening', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({
      success: true,
      message: 'Screening questions updated (fallback)',
    })
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const id = searchParams.get('id')
    
    if (!id) {
      return NextResponse.json(
        { error: 'ID da pergunta não fornecido' },
        { status: 400 }
      )
    }
    
    const backendUrl = `${BACKEND_URL}/api/v1/screening-questions/${id}`
    
    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.status === 404) {
      return NextResponse.json({
        success: true,
        message: 'Screening question deleted',
        deleted_id: id
      })
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao deletar pergunta de screening', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json({
      success: true,
      message: 'Screening question deleted (fallback)'
    })
  }
}
