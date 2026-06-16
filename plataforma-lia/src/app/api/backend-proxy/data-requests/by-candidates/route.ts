export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server'
import { getAuthHeaders } from '@/lib/api/auth-headers'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8001'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const candidateIds = searchParams.get('candidate_ids')
    const vacancyId = searchParams.get('vacancy_id')
    
    if (!candidateIds) {
      return NextResponse.json(
        { error: 'candidate_ids parameter is required' },
        { status: 400 }
      )
    }
    
    const ids = candidateIds.split(',').filter(id => id.trim())
    if (ids.length === 0) {
      return NextResponse.json({ items: [], byCandidate: {} })
    }
    
    const allRequests: Record<string, unknown>[] = []
    const fetchPromises = ids.map(async (candidateId) => {
      const params = new URLSearchParams()
      params.set('candidate_id', candidateId.trim())
      if (vacancyId) {
        params.set('vacancy_id', vacancyId)
      }
      
      try {
        const response = await fetch(
          `${BACKEND_URL}/api/v1/data-requests?${params.toString()}`,
          {
            method: 'GET',
            headers: getAuthHeaders(request),
          }
        )
        
        if (response.ok) {
          const data = await response.json()
          return data.items || []
        }
        return []
      } catch (e) {
        return []
      }
    })
    
    const results = await Promise.all(fetchPromises)
    results.forEach(items => allRequests.push(...items))
    
    const byCandidate: Record<string, unknown> = {}
    for (const req of allRequests) {
      const cid = (req.candidate_id || req.candidateId) as string | undefined
      if (!cid) continue
      
      const mapped = {
        id: req.id,
        candidateId: cid,
        jobVacancyId: req.vacancy_id || req.jobVacancyId,
        status: req.status,
        fieldsRequested: (req.fields_requested as Record<string, unknown>[] || []).map((f) => ({
          id: f.name || f.id,
          name: f.name || f.id,
          displayName: f.label || f.displayName || f.name,
          status: 'pending',
        })),
        fieldsCompleted: (req.fields_completed as Record<string, unknown>[] || []).map((f) => ({
          id: f.name || f.id,
          name: f.name || f.id,
          displayName: f.label || f.displayName || f.name,
          status: 'completed',
        })),
        expiresAt: req.expires_at || req.expiresAt,
        createdAt: req.created_at || req.createdAt,
        reminderCount: req.reminder_count || req.reminderCount || 0,
      }
      
      if (!byCandidate[cid]) {
        byCandidate[cid] = mapped
      } else {
        const existing = byCandidate[cid] as typeof mapped
        const existingActive = existing.status === 'pending' || existing.status === 'partial'
        const newActive = mapped.status === 'pending' || mapped.status === 'partial'
        
        if (newActive && !existingActive) {
          byCandidate[cid] = mapped
        } else if (existingActive === newActive) {
          const existingDate = new Date(existing.createdAt as string).getTime()
          const newDate = new Date(mapped.createdAt as string).getTime()
          if (newDate > existingDate) {
            byCandidate[cid] = mapped
          }
        }
      }
    }
    
    return NextResponse.json({
      items: allRequests,
      byCandidate,
    })
  } catch (error) {
    return NextResponse.json(
      { error: 'Erro ao conectar com o backend' },
      { status: 500 }
    )
  }
}
