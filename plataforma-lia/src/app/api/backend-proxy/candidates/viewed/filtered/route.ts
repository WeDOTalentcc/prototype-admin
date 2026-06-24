export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'
import { validateBody } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export type HideViewedScope = 
  | "dont_hide"
  | "by_you_this_project"
  | "by_you_all_projects"
  | "shortlisted_by_you"
  | "by_org_this_project"
  | "by_org_all_projects"
  | "shortlisted_org_this_project"
  | "shortlisted_org_all_projects"

export type HideViewedPeriod = 
  | "all_time"
  | "last_24h"
  | "last_2_weeks"
  | "last_3_months"
  | "last_6_months"

function getPeriodDateFilter(period: HideViewedPeriod): Date | null {
  const now = new Date()
  
  switch (period) {
    case "all_time":
      return null
    case "last_24h":
      return new Date(now.getTime() - 24 * 60 * 60 * 1000)
    case "last_2_weeks":
      return new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000)
    case "last_3_months":
      return new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
    case "last_6_months":
      return new Date(now.getTime() - 180 * 24 * 60 * 60 * 1000)
    default:
      return null
  }
}

function isShortlistScope(scope: HideViewedScope): boolean {
  return scope.startsWith('shortlisted_')
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data
    const { 
      scope, 
      period, 
      project_id, 
      user_id, 
      user_email,
      company_id 
    } = body as {
      scope: HideViewedScope
      period: HideViewedPeriod
      project_id?: string
      user_id?: string
      user_email?: string
      company_id?: string
    }

    if (scope === "dont_hide") {
      return NextResponse.json({ candidate_ids: [], count: 0 })
    }

    const periodDate = getPeriodDateFilter(period)
    
    // Handle shortlist scopes - call the interviews endpoint
    if (isShortlistScope(scope)) {
      const queryParams = new URLSearchParams()
      queryParams.append('scope', scope)
      
      if (scope === "shortlisted_by_you") {
        if (user_email) queryParams.append('user_email', user_email)
      } else if (scope === "shortlisted_org_this_project") {
        if (project_id) queryParams.append('project_id', project_id)
        if (company_id) queryParams.append('company_id', company_id)
      } else if (scope === "shortlisted_org_all_projects") {
        if (company_id) queryParams.append('company_id', company_id)
      }
      
      if (periodDate) {
        queryParams.append('since_date', periodDate.toISOString())
      }
      
      const backendUrl = `${BACKEND_URL}/api/v1/interviews/shortlisted/filter?${queryParams.toString()}`
      
      const response = await fetch(backendUrl, {
        method: 'GET',
        headers: getAuthHeaders(request),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        return NextResponse.json(
          { error: 'Erro ao buscar candidatos selecionados', details: errorData },
          { status: response.status }
        )
      }

      const data = await response.json()
      return NextResponse.json(data)
    }
    
    // Handle viewed scopes - call the candidates viewed endpoint
    const queryParams = new URLSearchParams()
    
    if (scope === "by_you_this_project") {
      if (user_id) queryParams.append('user_id', user_id)
      if (project_id) queryParams.append('project_id', project_id)
    } else if (scope === "by_you_all_projects") {
      if (user_id) queryParams.append('user_id', user_id)
    } else if (scope === "by_org_this_project") {
      if (company_id) queryParams.append('company_id', company_id)
      if (project_id) queryParams.append('project_id', project_id)
    } else if (scope === "by_org_all_projects") {
      if (company_id) queryParams.append('company_id', company_id)
    }
    
    if (periodDate) {
      queryParams.append('viewed_after', periodDate.toISOString())
    }
    
    queryParams.append('include_shortlisted', 'true')
    
    const backendUrl = `${BACKEND_URL}/api/v1/candidates/viewed/filter?${queryParams.toString()}`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: getAuthHeaders(request),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return NextResponse.json(
        { error: 'Erro ao buscar candidatos visualizados', details: errorData },
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
