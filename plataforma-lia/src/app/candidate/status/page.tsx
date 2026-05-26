'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'next/navigation'
import { Loader2, AlertCircle } from 'lucide-react'
import { CandidateChatPage } from '@/components/candidate/CandidateChatPage'
import { CandidateJobSelector, type ApplicationSummary } from '@/components/candidate/CandidateJobSelector'

type PageState =
  | { type: 'loading' }
  | { type: 'error'; message: string }
  | { type: 'selector'; applications: ApplicationSummary[] }
  | { type: 'chat'; vacancyId: string; context: Record<string, string> }

function parseJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload
  } catch {
    return null
  }
}

export default function CandidateStatusPage() {
  const searchParams = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const [state, setState] = useState<PageState>({ type: 'loading' })

  const loadApplications = useCallback(async (tok: string, payload: Record<string, unknown>) => {
    try {
      const res = await fetch('/api/backend-proxy/candidate/applications', {
        headers: { Authorization: `Bearer ${tok}` },
      })

      if (res.status === 401) {
        setState({ type: 'error', message: 'Seu link expirou. Solicite um novo link ao RH.' })
        return
      }

      if (!res.ok) {
        setState({ type: 'error', message: 'Não foi possível carregar suas candidaturas. Tente novamente.' })
        return
      }

      const data = await res.json()
      const applications: ApplicationSummary[] = data?.data ?? []

      if (applications.length === 0) {
        setState({
          type: 'chat',
          vacancyId: payload.vacancy_id as string,
          context: {},
        })
        return
      }

      if (applications.length === 1) {
        const app = applications[0]
        setState({
          type: 'chat',
          vacancyId: app.vacancy_id,
          context: {
            vacancy_title: app.vacancy_title,
            stage: app.stage,
          },
        })
        return
      }

      setState({ type: 'selector', applications })
    } catch {
      setState({ type: 'error', message: 'Erro de conexão. Verifique sua internet.' })
    }
  }, [])

  useEffect(() => {
    if (!token) {
      setState({ type: 'error', message: 'Link inválido. Verifique o link recebido por e-mail ou WhatsApp.' })
      return
    }

    const payload = parseJwtPayload(token)
    if (!payload) {
      setState({ type: 'error', message: 'Link inválido. Solicite um novo link ao RH.' })
      return
    }

    const exp = payload.exp as number | undefined
    if (exp && exp * 1000 < Date.now()) {
      setState({ type: 'error', message: 'Seu link expirou. Solicite um novo link ao RH.' })
      return
    }

    loadApplications(token, payload)
  }, [token, loadApplications])

  const handleSelectApplication = useCallback((app: ApplicationSummary) => {
    setState({
      type: 'chat',
      vacancyId: app.vacancy_id,
      context: {
        vacancy_title: app.vacancy_title,
        stage: app.stage,
      },
    })
  }, [])

  if (state.type === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3 text-center">
          <Loader2 className="h-8 w-8 animate-spin text-wedo-cyan" />
          <p className="text-sm text-muted-foreground">Carregando seu portal...</p>
        </div>
      </div>
    )
  }

  if (state.type === 'error') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="flex max-w-sm flex-col items-center gap-4 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
            <AlertCircle className="h-6 w-6 text-destructive" />
          </div>
          <div className="space-y-1">
            <h2 className="text-base font-semibold text-foreground">Não foi possível abrir o portal</h2>
            <p className="text-sm text-muted-foreground">{state.message}</p>
          </div>
          <p className="text-xs text-muted-foreground">
            Em caso de dúvidas, entre em contato com a empresa que realizou sua candidatura.
          </p>
        </div>
      </div>
    )
  }

  if (state.type === 'selector') {
    return (
      <CandidateJobSelector
        applications={state.applications}
        onSelect={handleSelectApplication}
      />
    )
  }

  return (
    <CandidateChatPage
      token={token}
      vacancyId={state.vacancyId}
      context={state.context}
    />
  )
}
