export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

const FALLBACK_QUESTIONS = {
  questions: [],
  behavioral_questions: [
    {
      id: 'fb-1',
      text: 'Descreva uma situação onde você precisou resolver um problema de forma criativa.',
      category: 'behavioral',
      trait: 'openness',
      bloom_level: 3,
      bloom_label: 'Aplicação',
      dreyfus_stage: 3,
      dreyfus_label: 'Competente',
      framework: 'BigFive',
      weight: 1.0,
      expected_signals: ['Criatividade', 'Resolução de problemas'],
      scoring_criteria: { '1': 'Resposta superficial', '3': 'Resposta adequada', '5': 'Resposta excepcional' },
      is_selected: true,
      order: 1
    }
  ],
  technical_questions: [
    {
      id: 'ft-1',
      text: 'Descreva um projeto desafiador que você trabalhou e como superou os obstáculos.',
      category: 'technical',
      skill: 'Problem Solving',
      bloom_level: 4,
      bloom_label: 'Análise',
      dreyfus_stage: 3,
      dreyfus_label: 'Competente',
      framework: 'CBI',
      weight: 1.0,
      expected_signals: ['Análise técnica', 'Superação de desafios'],
      scoring_criteria: { '1': 'Resposta superficial', '3': 'Resposta adequada', '5': 'Resposta excepcional' },
      is_selected: true,
      order: 1
    }
  ],
  cultural_questions: [
    {
      id: 'fc-1',
      text: 'Como você se adapta a diferentes ambientes e culturas de trabalho?',
      category: 'cultural',
      bloom_level: 3,
      bloom_label: 'Aplicação',
      dreyfus_stage: 3,
      dreyfus_label: 'Competente',
      framework: 'CBI',
      weight: 1.0,
      expected_signals: ['Adaptabilidade', 'Flexibilidade'],
      scoring_criteria: { '1': 'Resposta superficial', '3': 'Resposta adequada', '5': 'Resposta excepcional' },
      is_selected: true,
      order: 1
    }
  ],
  total_count: 3,
  metadata: {
    seniority: 'pleno',
    dreyfus_stage: 3,
    bloom_levels: [3, 4],
    skills_count: 0,
    title: 'Vaga',
    department: undefined
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const backendUrl = `${BACKEND_URL}/api/v1/screening/questions`
    
    const authHeader = request.headers.get('Authorization')
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (authHeader) {
      headers['Authorization'] = authHeader
    }
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })

    if (response.status === 404) {
      return NextResponse.json({
        ...FALLBACK_QUESTIONS,
        metadata: {
          ...FALLBACK_QUESTIONS.metadata,
          title: body.title || 'Vaga',
          department: body.department,
          seniority: body.seniority || 'pleno'
        }
      })
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({ 
        error: 'Erro ao gerar perguntas de triagem', 
        details: errorData,
        status: response.status 
      }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(FALLBACK_QUESTIONS)
  }
}
