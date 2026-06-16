'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'next/navigation'
import { useUIPreferencesStore } from '@/stores/ui-preferences-store'

export interface Candidate {
  id: string
  name: string
  title?: string
  company?: string
  location?: string
  experience_years?: number
  skills?: string[]
  wsi_score?: number
  photo_url?: string
  summary?: string
  education?: string
  linkedin_url?: string
  resume_url?: string
}

export interface Feedback {
  candidate_id: string
  rating: 'approved' | 'maybe' | 'rejected'
  comment?: string
  created_at?: string
}

export interface PublicSharedSearchResponse {
  id: string
  title: string
  shared_by_name: string
  shared_by_email?: string
  message?: string
  expires_at: string
  client_logo_url?: string
  candidates: Candidate[]
  feedbacks: Feedback[]
  requires_auth: boolean
  can_comment?: boolean
  can_rate?: boolean
}

export type FilterType = 'all' | 'approved' | 'maybe' | 'rejected' | 'pending'

export function useSharedToken() {
  const params = useParams()
  const token = params?.token as string

  const [sessionToken, setSessionToken] = useState<string | null>(null)
  const [sharedData, setSharedData] = useState<PublicSharedSearchResponse | null>(null)
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [loading, setLoading] = useState(true)
  const [authLoading, setAuthLoading] = useState(false)
  const [feedbacks, setFeedbacks] = useState<Map<string, Feedback>>(new Map())
  const [activeFilter, setActiveFilter] = useState<FilterType>('all')
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set())
  const [pendingFeedbacks, setPendingFeedbacks] = useState<Map<string, { rating: 'approved' | 'maybe' | 'rejected', comment: string }>>(new Map())
  const [savingFeedback, setSavingFeedback] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [authError, setAuthError] = useState<string | null>(null)

  const fetchSharedData = useCallback(async () => {
    if (!token) return

    try {
      setLoading(true)
      setError(null)

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }

      if (sessionToken) {
        headers['Authorization'] = `Bearer ${sessionToken}`
      }

      const response = await fetch(`/api/public-proxy/shared/${token}`, {
        headers,
      })

      if (!response.ok) {
        if (response.status === 404) {
          setError('Link de compartilhamento não encontrado ou expirado.')
        } else if (response.status === 401) {
          useUIPreferencesStore.getState().removeSharedSessionToken(token)
          setSessionToken(null)
          setError('Sessão expirada. Por favor, faça login novamente.')
        } else {
          setError('Erro ao carregar os dados. Tente novamente.')
        }
        return
      }

      const data: PublicSharedSearchResponse = await response.json()
      setSharedData(data)

      const feedbackMap = new Map<string, Feedback>()
      data.feedbacks?.forEach((f) => {
        feedbackMap.set(f.candidate_id, f)
      })
      setFeedbacks(feedbackMap)
    } catch (err) {
      setError('Erro de conexão. Verifique sua internet e tente novamente.')
    } finally {
      setLoading(false)
    }
  }, [token, sessionToken])

  useEffect(() => {
    if (token) {
      const storedToken = useUIPreferencesStore.getState().getSharedSessionToken(token)
      if (storedToken) {
        setSessionToken(storedToken)
      }
    }
  }, [token])

  useEffect(() => {
    fetchSharedData()
  }, [fetchSharedData])

  const handleRequestOtp = async () => {
    if (!email.trim()) {
      setAuthError('Por favor, insira seu email.')
      return
    }

    try {
      setAuthLoading(true)
      setAuthError(null)

      const response = await fetch(`/api/public-proxy/shared/${token}/request-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        setAuthError(data.error || 'Erro ao enviar código. Verifique seu email.')
        return
      }

      setOtpSent(true)
    } catch (err) {
      setAuthError('Erro de conexão. Tente novamente.')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleVerifyOtp = async () => {
    if (!otp.trim()) {
      setAuthError('Por favor, insira o código de verificação.')
      return
    }

    try {
      setAuthLoading(true)
      setAuthError(null)

      const response = await fetch(`/api/public-proxy/shared/${token}/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), otp: otp.trim() }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        setAuthError(data.error || 'Código inválido ou expirado.')
        return
      }

      const data = await response.json()
      const newSessionToken = data.session_token || data.token

      if (newSessionToken) {
        useUIPreferencesStore.getState().setSharedSessionToken(token, newSessionToken)
        setSessionToken(newSessionToken)
        setOtpSent(false)
        setOtp('')
        setEmail('')
      }
    } catch (err) {
      setAuthError('Erro de conexão. Tente novamente.')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleSaveFeedback = async (candidateId: string) => {
    const pending = pendingFeedbacks.get(candidateId)
    if (!pending) return

    try {
      setSavingFeedback(candidateId)

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }

      if (sessionToken) {
        headers['Authorization'] = `Bearer ${sessionToken}`
      }

      const response = await fetch(`/api/public-proxy/shared/${token}/feedback`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          candidate_id: candidateId,
          rating: pending.rating,
          comment: pending.comment || undefined,
        }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        alert(data.error || 'Erro ao salvar avaliação.')
        return
      }

      const newFeedback: Feedback = {
        candidate_id: candidateId,
        rating: pending.rating,
        comment: pending.comment,
        created_at: new Date().toISOString(),
      }

      setFeedbacks((prev) => new Map(prev).set(candidateId, newFeedback))
      setPendingFeedbacks((prev) => {
        const updated = new Map(prev)
        updated.delete(candidateId)
        return updated
      })
    } catch (err) {
      alert('Erro de conexão. Tente novamente.')
    } finally {
      setSavingFeedback(null)
    }
  }

  const updatePendingFeedback = (candidateId: string, rating: 'approved' | 'maybe' | 'rejected') => {
    setPendingFeedbacks((prev) => {
      const existing = prev.get(candidateId)
      return new Map(prev).set(candidateId, {
        rating,
        comment: existing?.comment || '',
      })
    })
  }

  const updatePendingComment = (candidateId: string, comment: string) => {
    setPendingFeedbacks((prev) => {
      const existing = prev.get(candidateId)
      if (!existing) return prev
      return new Map(prev).set(candidateId, { ...existing, comment })
    })
  }

  const toggleCardExpanded = (candidateId: string) => {
    setExpandedCards((prev) => {
      const updated = new Set(prev)
      if (updated.has(candidateId)) {
        updated.delete(candidateId)
      } else {
        updated.add(candidateId)
      }
      return updated
    })
  }

  const clearPendingFeedback = (candidateId: string) => {
    setPendingFeedbacks((prev) => {
      const updated = new Map(prev)
      updated.delete(candidateId)
      return updated
    })
  }

  const getFilteredCandidates = () => {
    if (!sharedData?.candidates) return []

    return sharedData.candidates.filter((candidate) => {
      const feedback = feedbacks.get(candidate.id)

      switch (activeFilter) {
        case 'approved':
          return feedback?.rating === 'approved'
        case 'maybe':
          return feedback?.rating === 'maybe'
        case 'rejected':
          return feedback?.rating === 'rejected'
        case 'pending':
          return !feedback
        default:
          return true
      }
    })
  }

  const getFeedbackCounts = () => {
    const counts = { approved: 0, maybe: 0, rejected: 0, pending: 0 }
    
    sharedData?.candidates?.forEach((candidate) => {
      const feedback = feedbacks.get(candidate.id)
      if (feedback) {
        counts[feedback.rating]++
      } else {
        counts.pending++
      }
    })

    return counts
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'long',
        year: 'numeric',
      })
    } catch {
      return dateString
    }
  }

  const isExpired = sharedData?.expires_at 
    ? new Date(sharedData.expires_at) < new Date() 
    : false

  const needsAuth = sharedData?.requires_auth && !sessionToken

  return {
    token,
    sessionToken,
    sharedData,
    email,
    setEmail,
    otp,
    setOtp,
    otpSent,
    setOtpSent,
    loading,
    authLoading,
    feedbacks,
    activeFilter,
    setActiveFilter,
    expandedCards,
    pendingFeedbacks,
    savingFeedback,
    error,
    authError,
    setAuthError,
    fetchSharedData,
    handleRequestOtp,
    handleVerifyOtp,
    handleSaveFeedback,
    updatePendingFeedback,
    updatePendingComment,
    toggleCardExpanded,
    clearPendingFeedback,
    getFilteredCandidates,
    getFeedbackCounts,
    formatDate,
    isExpired,
    needsAuth,
  }
}
