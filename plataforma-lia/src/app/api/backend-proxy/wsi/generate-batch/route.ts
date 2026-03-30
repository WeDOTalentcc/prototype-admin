import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.LIA_BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'

const SENIORITY_MAP: Record<string, string> = {
  'jr': 'junior', 'júnior': 'junior', 'junior': 'junior', 'trainee': 'junior', 'estagiário': 'junior', 'estágio': 'junior', 'estágiario': 'junior',
  'pleno': 'pleno', 'mid': 'pleno', 'mid-level': 'pleno', 'intermediário': 'pleno',
  'sr': 'senior', 'sênior': 'senior', 'senior': 'senior', 'especialista': 'senior',
  'lead': 'lead', 'líder': 'lead', 'coordenador': 'lead', 'tech lead': 'lead',
  'executive': 'executive', 'executivo': 'executive', 'diretor': 'executive', 'c-level': 'executive', 'gerente': 'executive',
}

function normalizeSeniority(raw: string | null | undefined): string {
  if (!raw) return 'pleno'
  const normalized = raw.toLowerCase().trim()
  return SENIORITY_MAP[normalized] || 'pleno'
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const backendPayload: Record<string, unknown> = {
      job_title: body.job_title,
      technical_skills: body.technical_skills || [],
      behavioral_competencies: body.behavioral_competencies || [],
      seniority: normalizeSeniority(body.seniority),
      job_description: body.description || null,
      format: body.mode || 'full',
      include_company_questions: true,
      is_affirmative: body.is_affirmative || false,
      affirmative_type: body.affirmative_type || null,
    }

    if (body.department) backendPayload.department = body.department
    if (body.question_count) backendPayload.question_count = body.question_count
    if (body.big_five_profile) backendPayload.big_five_profile = body.big_five_profile
    if (body.company_id) backendPayload.company_id = body.company_id

    const backendUrl = `${BACKEND_URL}/api/v1/wsi/screening-pipeline`

    const authHeader = request.headers.get('Authorization')
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Authorization': authHeader || 'Bearer demo-token',
    }

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(backendPayload),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json({
        error: 'Erro ao gerar perguntas WSI em lote',
        details: errorData,
        status: response.status
      }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro interno ao processar geração WSI em lote', detail: String(error) },
      { status: 500 }
    )
  }
}
