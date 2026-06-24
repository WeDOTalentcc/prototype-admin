'use client'

import React, { useState, useEffect, useCallback, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Loader2, AlertCircle } from 'lucide-react'
import { NextIntlClientProvider, useTranslations } from 'next-intl'
import ptBRMessages from '@/../messages/pt-BR.json'
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

function CandidateStatusContent() {
  const t = useTranslations('candidateStatus')
  const searchParams = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const [state, setState] = useState<PageState>({ type: 'loading' })

  const loadApplications = useCallback(async (tok: string, payload: Record<string, unknown>) => {
    try {
      const res = await fetch('/api/backend-proxy/candidate/applications', {
        headers: { Authorization: `Bearer ${tok}` },
      })

      if (res.status === 401) {
        setState({ type: 'error', message: t('errors.linkExpiredRh') })
        return
      }

      if (!res.ok) {
        setState({ type: 'error', message: t('errors.loadFailed') })
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
      setState({ type: 'error', message: t('errors.connectionError') })
    }
  }, [t])

  useEffect(() => {
    if (!token) {
      setState({ type: 'error', message: t('errors.invalidLinkContact') })
      return
    }

    const payload = parseJwtPayload(token)
    if (!payload) {
      setState({ type: 'error', message: t('errors.invalidLinkRh') })
      return
    }

    const exp = payload.exp as number | undefined
    if (exp && exp * 1000 < Date.now()) {
      setState({ type: 'error', message: t('errors.linkExpiredRh') })
      return
    }

    loadApplications(token, payload)
  }, [token, loadApplications, t])

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
          <p className="text-sm text-muted-foreground">{t('loading.portal')}</p>
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
            <h2 className="text-base font-semibold text-foreground">{t('errorState.title')}</h2>
            <p className="text-sm text-muted-foreground">{state.message}</p>
          </div>
          <p className="text-xs text-muted-foreground">
            {t('errorState.contactHint')}
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


export default function CandidateStatusPage() {
  return (
    <NextIntlClientProvider locale="pt" messages={ptBRMessages} timeZone="America/Sao_Paulo">
      <Suspense
        fallback={
          <div className="min-h-screen flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        }
      >
        <CandidateStatusContent />
      </Suspense>
    </NextIntlClientProvider>
  )
}
