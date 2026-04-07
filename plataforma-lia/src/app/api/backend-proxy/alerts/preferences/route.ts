export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get('user_id') || 'default'
    
    const backendUrl = `${BACKEND_URL}/api/v1/alerts/preferences?user_id=${userId}`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar preferências de alertas', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { 
        preferences: getDefaultPreferences('default'),
        user_id: 'default'
      },
      { status: 200 }
    )
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const backendUrl = `${BACKEND_URL}/api/v1/alerts/preferences`
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao salvar preferências de alertas', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}

export async function PUT(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    
    const backendUrl = `${BACKEND_URL}/api/v1/alerts/preferences`
    
    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao atualizar preferências de alertas', details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}

function getDefaultPreferences(userId: string) {
  return [
    { alert_type: "time_to_hire_critical", name: "Time to Hire Crítico", description: "Alerta quando time to hire ultrapassa limite", is_enabled: true, threshold: 45, channels: { email: true, bell: true, teams: false, whatsapp: false }, cooldown_hours: 24 },
    { alert_type: "conversion_rate_low", name: "Taxa de Conversão Baixa", description: "Alerta quando taxa de conversão está abaixo do limite", is_enabled: true, threshold: 2, channels: { email: true, bell: true, teams: false, whatsapp: false }, cooldown_hours: 48 },
    { alert_type: "nps_declining", name: "NPS em Declínio", description: "Alerta quando NPS cai abaixo do limite", is_enabled: true, threshold: 75, channels: { email: false, bell: true, teams: false, whatsapp: false }, cooldown_hours: 24 },
    { alert_type: "no_hires", name: "Sem Contratações", description: "Alerta quando não há contratações no período", is_enabled: true, threshold: 0, channels: { email: true, bell: true, teams: true, whatsapp: false }, cooldown_hours: 168 },
    { alert_type: "quality_score_low", name: "Score de Qualidade Baixo", description: "Alerta quando score de qualidade está baixo", is_enabled: true, threshold: 4, channels: { email: true, bell: true, teams: false, whatsapp: false }, cooldown_hours: 48 },
    { alert_type: "sla_near_expiration", name: "SLA Próximo do Vencimento", description: "Alerta quando candidato está há 80% do SLA na mesma etapa", is_enabled: true, threshold: 80, channels: { email: true, bell: true, teams: true, whatsapp: false }, cooldown_hours: 12 },
    { alert_type: "monthly_goal_at_risk", name: "Meta Mensal em Risco", description: "Notifica quando a meta de contratações pode não ser atingida", is_enabled: true, threshold: 50, channels: { email: true, bell: true, teams: false, whatsapp: false }, cooldown_hours: 24 },
    { alert_type: "candidate_no_interaction", name: "Candidato Sem Interação", description: "Alerta para candidatos sem contato há mais de 5 dias", is_enabled: true, threshold: 5, channels: { email: true, bell: true, teams: false, whatsapp: false }, cooldown_hours: 24 },
    { alert_type: "interview_not_confirmed", name: "Entrevista Não Confirmada", description: "Lembrete 24h antes de entrevistas sem confirmação", is_enabled: true, threshold: 24, channels: { email: true, bell: true, teams: true, whatsapp: true }, cooldown_hours: 12 },
    { alert_type: "feedback_pending", name: "Feedback Pendente", description: "Solicita feedback após 48h de entrevista realizada", is_enabled: false, threshold: 48, channels: { email: true, bell: true, teams: false, whatsapp: false }, cooldown_hours: 24 },
    { alert_type: "candidates_stagnant", name: "Candidatos Estagnados", description: "Candidatos parados na mesma etapa por muito tempo", is_enabled: true, threshold: 10, channels: { email: true, bell: true, teams: false, whatsapp: false }, cooldown_hours: 48 },
    { alert_type: "offers_pending_long", name: "Propostas Pendentes", description: "Propostas aguardando resposta por muito tempo", is_enabled: true, threshold: 72, channels: { email: true, bell: true, teams: true, whatsapp: true }, cooldown_hours: 24 },
    { alert_type: "pipeline_empty", name: "Pipeline Vazio", description: "Vaga com poucos candidatos ativos", is_enabled: true, threshold: 3, channels: { email: true, bell: true, teams: false, whatsapp: false }, cooldown_hours: 12 },
    { alert_type: "tasks_overdue", name: "Tarefas Atrasadas", description: "Tarefas pendentes além do prazo", is_enabled: true, threshold: 5, channels: { email: true, bell: true, teams: true, whatsapp: false }, cooldown_hours: 8 },
    { alert_type: "email_delivery_low", name: "Entrega de Email Baixa", description: "Taxa de entrega de emails abaixo do esperado", is_enabled: true, threshold: 80, channels: { email: false, bell: true, teams: false, whatsapp: false }, cooldown_hours: 24 },
    { alert_type: "dropout_risk_high", name: "Risco de Desistência Alto", description: "Candidato com alto risco de desistência", is_enabled: true, threshold: 70, channels: { email: true, bell: true, teams: true, whatsapp: true }, cooldown_hours: 24 },
    { alert_type: "ideal_candidate_found", name: "Candidato Ideal Encontrado", description: "Candidato com match acima de 90%", is_enabled: true, threshold: 90, channels: { email: true, bell: true, teams: true, whatsapp: true }, cooldown_hours: 0 },
    { alert_type: "ats_sync_failed", name: "Falha na Sincronização ATS", description: "Erro na sincronização com sistema ATS", is_enabled: true, threshold: 3, channels: { email: true, bell: true, teams: true, whatsapp: false }, cooldown_hours: 2 },
  ].map(pref => ({ ...pref, user_id: userId, id: null }))
}
