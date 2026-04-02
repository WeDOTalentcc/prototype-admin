'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { 
  ThumbsUp, 
  ThumbsDown, 
  HelpCircle, 
  Clock, 
  MapPin, 
  Briefcase, 
  ChevronDown, 
  ChevronUp,
  Calendar,
  User,
  Users,
  Mail,
  Send,
  Check,
  Loader2,
  Linkedin,
  FileText
} from 'lucide-react'

interface Candidate {
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

interface Feedback {
  candidate_id: string
  rating: 'approved' | 'maybe' | 'rejected'
  comment?: string
  created_at?: string
}

interface PublicSharedSearchResponse {
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

type FilterType = 'all' | 'approved' | 'maybe' | 'rejected' | 'pending'

const STORAGE_KEY_PREFIX = 'wedo_shared_session_'

export default function SharedSearchPage() {
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
          localStorage.removeItem(`${STORAGE_KEY_PREFIX}${token}`)
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
      const storedToken = localStorage.getItem(`${STORAGE_KEY_PREFIX}${token}`)
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
        localStorage.setItem(`${STORAGE_KEY_PREFIX}${token}`, newSessionToken)
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

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center font-['Open_Sans']" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="flex flex-col items-center gap-4" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary animate-spin motion-reduce:animate-none" />
          <p className="text-zinc-400">Carregando...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center font-['Open_Sans']">
        <div className="bg-zinc-900 rounded-md p-8 max-w-md text-center border border-zinc-800">
          <div className="text-status-error text-lg mb-4">{error}</div>
          <Button
            onClick={() => fetchSharedData()}
            className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active"
          >
            Tentar novamente
          </Button>
        </div>
      </div>
    )
  }

  if (isExpired) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center font-['Open_Sans']">
        <div className="bg-zinc-900 rounded-md p-8 max-w-md text-center border border-zinc-800">
          <Clock className="w-12 h-12 text-zinc-500 mx-auto mb-4" />
          <h2 className="text-xl text-white mb-2">Link Expirado</h2>
          <p className="text-zinc-400">
            Este link de compartilhamento expirou em {formatDate(sharedData?.expires_at || '')}.
          </p>
        </div>
      </div>
    )
  }

  const counts = getFeedbackCounts()
  const filteredCandidates = getFilteredCandidates()
  const evaluatedCount = counts.approved + counts.maybe + counts.rejected
  const totalCount = sharedData?.candidates?.length || 0

  return (
    <div className="min-h-screen bg-zinc-950 font-['Open_Sans']">
      <header className="sticky top-0 z-50 bg-zinc-950/95 backdrop-blur-sm border-b border-zinc-800">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Image
            src="/logos/wedo-logo.png"
            alt="WeDoTalent"
            width={140}
            height={40}
            className="h-8 w-auto"
          />
          {sharedData?.client_logo_url && (
            <img
              src={sharedData.client_logo_url}
              alt="Cliente"
              className="h-8 w-auto object-contain"
            />
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        <section className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Candidatos para sua avaliação
          </h1>
          {sharedData?.title && (
            <h2 className="text-xl text-zinc-300 mb-4">{sharedData.title}</h2>
          )}
          <div className="flex flex-wrap gap-4 text-sm text-zinc-400">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              <span aria-live="polite" aria-atomic="true">{totalCount} candidato{totalCount !== 1 ? 's' : ''}</span>
            </div>
            {sharedData?.shared_by_name && (
              <div className="flex items-center gap-2">
                <User className="w-4 h-4" />
                <span>Compartilhado por {sharedData.shared_by_name}</span>
              </div>
            )}
            {sharedData?.expires_at && (
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>Expira em {formatDate(sharedData.expires_at)}</span>
              </div>
            )}
          </div>
          {sharedData?.message && (
            <div className="mt-4 bg-zinc-900 rounded-md p-4 border border-zinc-800">
              <p className="text-zinc-300 italic">"{sharedData.message}"</p>
            </div>
          )}
        </section>

        {needsAuth && (
          <section className="mb-8">
            <div className="bg-zinc-900 rounded-md p-6 border border-zinc-800 max-w-md mx-auto">
              <div className="flex items-center gap-3 mb-4">
                <Mail className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                <h3 className="text-lg font-medium text-white">Acesso Necessário</h3>
              </div>
              <p className="text-zinc-400 text-sm mb-4" aria-live="polite" aria-atomic="true">
                Para avaliar os candidatos, insira seu email para receber um código de acesso.
              </p>

              {!otpSent ? (
                <div className="space-y-4">
                  <Input
                    type="email"
                    placeholder="Seu email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-500"
                  />
                  {authError && (
                    <p className="text-status-error text-sm">{authError}</p>
                  )}
                  <Button
                    onClick={handleRequestOtp}
                    disabled={authLoading}
                    className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active"
                  >
                    {authLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" />
                    ) : (
                      <Send className="w-4 h-4 mr-2" />
                    )}
                    Enviar código de acesso
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <p className="text-zinc-300 text-sm">
                    Enviamos um código para <strong>{email}</strong>
                  </p>
                  <Input
                    type="text"
                    placeholder="Código de 6 dígitos"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    maxLength={6}
                    className="bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-500 text-center text-lg tracking-widest"
                  />
                  {authError && (
                    <p className="text-status-error text-sm">{authError}</p>
                  )}
                  <Button
                    onClick={handleVerifyOtp}
                    disabled={authLoading}
                    className="w-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active"
                  >
                    {authLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" />
                    ) : (
                      <Check className="w-4 h-4 mr-2" />
                    )}
                    Verificar
                  </Button>
                  <button
                    onClick={() => {
                      setOtpSent(false)
                      setOtp('')
                      setAuthError(null)
                    }}
                    className="text-zinc-400 text-sm hover:text-zinc-300 w-full text-center"
                  >
                    Voltar
                  </button>
                </div>
              )}
            </div>
          </section>
        )}

        {(!sharedData?.requires_auth || sessionToken) && sharedData?.candidates && (
          <>
            <section className="mb-6">
              <div className="bg-zinc-900 rounded-md p-4 border border-zinc-800">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-zinc-300 text-sm">
                    {evaluatedCount}/{totalCount} avaliados
                  </span>
                  <span className="text-zinc-500 text-sm">
                    {Math.round((evaluatedCount / totalCount) * 100) || 0}%
                  </span>
                </div>
                <div className="w-full bg-zinc-800 rounded-full h-2">
                  <div
                    className="bg-lia-btn-primary-bg dark:bg-lia-bg-secondary h-2 rounded-full transition-[width,height] duration-300"
                    style={{width: `${(evaluatedCount / totalCount) * 100 || 0}%`}}
                  />
                </div>
                <div className="flex gap-4 mt-4 text-sm">
                  <span className="flex items-center gap-1">
                    👍 <span className="text-status-success">{counts.approved}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    🤔 <span className="text-status-warning">{counts.maybe}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    👎 <span className="text-status-error">{counts.rejected}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    ⏳ <span className="text-zinc-400">{counts.pending}</span>
                  </span>
                </div>
              </div>
            </section>

            <section className="mb-6">
              <div className="flex flex-wrap gap-2">
                {([
                  { key: 'all', label: 'Todos', count: totalCount },
                  { key: 'approved', label: 'Interessados', count: counts.approved },
                  { key: 'maybe', label: 'Talvez', count: counts.maybe },
                  { key: 'rejected', label: 'Não', count: counts.rejected },
                  { key: 'pending', label: 'Pendentes', count: counts.pending },
                ] as const).map(({ key, label, count }) => (
                  <button
                    key={key}
                    onClick={() => setActiveFilter(key)}
                    className={`px-4 py-2 rounded-md text-sm transition-colors motion-reduce:transition-none ${
                      activeFilter === key
                        ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary'
                        : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800 border border-zinc-800'
                    }`}
                  >
                    {label} ({count})
                  </button>
                ))}
              </div>
            </section>

            <section className="space-y-4">
              {filteredCandidates.length === 0 ? (
                <div className="bg-zinc-900 rounded-md p-8 text-center border border-zinc-800">
                  <p className="text-zinc-400" aria-live="polite" aria-atomic="true">Nenhum candidato encontrado para este filtro.</p>
                </div>
              ) : (
                filteredCandidates.map((candidate) => {
                  const feedback = feedbacks.get(candidate.id)
                  const pending = pendingFeedbacks.get(candidate.id)
                  const isExpanded = expandedCards.has(candidate.id)
                  const isSaving = savingFeedback === candidate.id

                  return (
                    <div
                      key={candidate.id}
                      className="bg-zinc-900 rounded-md border border-zinc-800 overflow-hidden"
                    >
                      <div className="p-4">
                        <div className="flex items-start gap-4">
                          {candidate.photo_url ? (
                            <img
                              src={candidate.photo_url}
                              alt={candidate.name}
                              className="w-14 h-14 rounded-full object-cover flex-shrink-0"
                            />
                          ) : (
                            <div className="w-14 h-14 rounded-full bg-zinc-800 flex items-center justify-center flex-shrink-0">
                              <User className="w-6 h-6 text-zinc-600" />
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-4">
                              <div>
                                <h3 className="text-lg font-medium text-white truncate">
                                  {candidate.name}
                                </h3>
                                {candidate.title && (
                                  <p className="text-zinc-400 text-sm">{candidate.title}</p>
                                )}
                              </div>
                              {candidate.wsi_score !== undefined && (
                                <Badge className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border-0 flex-shrink-0">
                                  WSI {candidate.wsi_score}
                                </Badge>
                              )}
                            </div>
                            <div className="flex flex-wrap gap-3 mt-2 text-sm text-zinc-500">
                              {candidate.company && (
                                <span className="flex items-center gap-1">
                                  <Briefcase className="w-3.5 h-3.5" />
                                  {candidate.company}
                                </span>
                              )}
                              {candidate.location && (
                                <span className="flex items-center gap-1">
                                  <MapPin className="w-3.5 h-3.5" />
                                  {candidate.location}
                                </span>
                              )}
                              {candidate.experience_years !== undefined && (
                                <span className="flex items-center gap-1">
                                  <Clock className="w-3.5 h-3.5" />
                                  {candidate.experience_years} anos exp.
                                </span>
                              )}
                              {candidate.linkedin_url && (
                                <a
                                  href={candidate.linkedin_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-1 text-brand-linkedin hover:text-brand-linkedin-hover transition-colors motion-reduce:transition-none"
                                >
                                  <Linkedin className="w-3.5 h-3.5" />
                                  LinkedIn
                                </a>
                              )}
                              {candidate.resume_url && (
                                <a
                                  href={candidate.resume_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-1 text-zinc-400 hover:text-zinc-200 transition-colors motion-reduce:transition-none"
                                >
                                  <FileText className="w-3.5 h-3.5" />
                                  Currículo
                                </a>
                              )}
                            </div>
                            {candidate.skills && candidate.skills.length > 0 && (
                              <div className="flex flex-wrap gap-1.5 mt-3">
                                {candidate.skills.slice(0, 5).map((skill) => (
                                  <Badge
                                    key={skill}
                                    variant="secondary"
                                    className="bg-zinc-800 text-zinc-300 border-0 text-xs"
                                  >
                                    {skill}
                                  </Badge>
                                ))}
                                {candidate.skills.length > 5 && (
                                  <Badge
                                    variant="secondary"
                                    className="bg-zinc-800 text-zinc-500 border-0 text-xs"
                                  >
                                    +{candidate.skills.length - 5}
                                  </Badge>
                                )}
                              </div>
                            )}
                          </div>
                        </div>

                        <button
                          onClick={() => toggleCardExpanded(candidate.id)}
                          className="flex items-center gap-1 text-lia-text-secondary dark:text-lia-text-tertiary text-sm mt-4 hover:text-wedo-cyan-dark transition-colors motion-reduce:transition-none"
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="w-4 h-4" />
                              Menos detalhes
                            </>
                          ) : (
                            <>
                              <ChevronDown className="w-4 h-4" />
                              Ver perfil completo
                            </>
                          )}
                        </button>

                        {isExpanded && (
                          <div className="mt-4 pt-4 border-t border-zinc-800">
                            {candidate.summary && (
                              <div className="mb-4">
                                <h4 className="text-sm font-medium text-zinc-300 mb-1">Resumo</h4>
                                <p className="text-zinc-400 text-sm">{candidate.summary}</p>
                              </div>
                            )}
                            {candidate.education && (
                              <div className="mb-4">
                                <h4 className="text-sm font-medium text-zinc-300 mb-1">Formação</h4>
                                <p className="text-zinc-400 text-sm">{candidate.education}</p>
                              </div>
                            )}
                            {candidate.skills && candidate.skills.length > 5 && (
                              <div>
                                <h4 className="text-sm font-medium text-zinc-300 mb-2">Todas as habilidades</h4>
                                <div className="flex flex-wrap gap-1.5">
                                  {candidate.skills.map((skill) => (
                                    <Badge
                                      key={skill}
                                      variant="secondary"
                                      className="bg-zinc-800 text-zinc-300 border-0 text-xs"
                                    >
                                      {skill}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="bg-zinc-950 p-4 border-t border-zinc-800">
                        {sharedData?.can_rate === false ? (
                          <div className="flex items-center gap-2 text-zinc-500 text-sm">
                            <span>Visualização apenas — avaliações desativadas pelo recrutador.</span>
                          </div>
                        ) : feedback && !pending ? (
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              {feedback.rating === 'approved' && (
                                <span className="flex items-center gap-2 text-status-success">
                                  <ThumbsUp className="w-4 h-4" />
                                  Interessado
                                </span>
                              )}
                              {feedback.rating === 'maybe' && (
                                <span className="flex items-center gap-2 text-status-warning">
                                  <HelpCircle className="w-4 h-4" />
                                  Talvez
                                </span>
                              )}
                              {feedback.rating === 'rejected' && (
                                <span className="flex items-center gap-2 text-status-error">
                                  <ThumbsDown className="w-4 h-4" />
                                  Não interessado
                                </span>
                              )}
                              {feedback.comment && (
                                <span className="text-zinc-500 text-sm ml-2">
                                  • {feedback.comment}
                                </span>
                              )}
                            </div>
                            <button
                              onClick={() => updatePendingFeedback(candidate.id, feedback.rating)}
                              className="text-zinc-500 text-sm hover:text-zinc-300"
                            >
                              Editar
                            </button>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <div className="flex flex-wrap gap-2">
                              <Button
                                onClick={() => updatePendingFeedback(candidate.id, 'approved')}
                                // @ts-ignore TODO: fix type
                                variant={pending?.rating === 'approved' ? 'default' : 'outline'}
                                size="sm"
                                className={
                                  pending?.rating === 'approved'
                                    ? 'bg-status-success hover:bg-status-success/10 text-white border-0'
                                    : 'border-zinc-700 text-zinc-300 hover:bg-zinc-800'
                                }
                              >
                                <ThumbsUp className="w-4 h-4 mr-1" />
                                Interessado
                              </Button>
                              <Button
                                onClick={() => updatePendingFeedback(candidate.id, 'maybe')}
                                // @ts-ignore TODO: fix type
                                variant={pending?.rating === 'maybe' ? 'default' : 'outline'}
                                size="sm"
                                className={
                                  pending?.rating === 'maybe'
                                    ? 'bg-status-warning/10 hover:bg-status-warning/10 text-white border-0'
                                    : 'border-zinc-700 text-zinc-300 hover:bg-zinc-800'
                                }
                              >
                                <HelpCircle className="w-4 h-4 mr-1" />
                                Talvez
                              </Button>
                              <Button
                                onClick={() => updatePendingFeedback(candidate.id, 'rejected')}
                                // @ts-ignore TODO: fix type
                                variant={pending?.rating === 'rejected' ? 'default' : 'outline'}
                                size="sm"
                                className={
                                  pending?.rating === 'rejected'
                                    ? 'bg-status-error hover:bg-status-error text-white border-0'
                                    : 'border-zinc-700 text-zinc-300 hover:bg-zinc-800'
                                }
                              >
                                <ThumbsDown className="w-4 h-4 mr-1" />
                                Não interessado
                              </Button>
                            </div>
                            {pending && (
                              <>
                                {sharedData?.can_comment !== false && (
                                  <textarea
                                    placeholder="Comentário (opcional)"
                                    value={pending.comment}
                                    onChange={(e) =>
                                      updatePendingComment(candidate.id, e.target.value)
                                    }
                                    className="w-full bg-zinc-800 border border-zinc-700 rounded-md p-2 text-sm text-white placeholder:text-zinc-500 resize-none focus:outline-none focus:border-lia-border-medium"
                                    rows={2}
                                  />
                                )}
                                <div className="flex justify-end gap-2">
                                  <Button
                                    onClick={() => {
                                      setPendingFeedbacks((prev) => {
                                        const updated = new Map(prev)
                                        updated.delete(candidate.id)
                                        return updated
                                      })
                                    }}
                                    variant="ghost"
                                    size="sm"
                                    className="text-zinc-400 hover:text-zinc-300"
                                  >
                                    Cancelar
                                  </Button>
                                  <Button
                                    onClick={() => handleSaveFeedback(candidate.id)}
                                    disabled={isSaving}
                                    size="sm"
                                    className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active"
                                  >
                                    {isSaving ? (
                                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-1" />
                                    ) : (
                                      <Check className="w-4 h-4 mr-1" />
                                    )}
                                    Salvar
                                  </Button>
                                </div>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })
              )}
            </section>
          </>
        )}
      </main>

      <footer className="border-t border-zinc-800 mt-12">
        <div className="max-w-6xl mx-auto px-4 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-zinc-500 text-sm">
            <span>Powered by</span>
            <Image
              src="/logos/wedo-logo.png"
              alt="WeDoTalent"
              width={100}
              height={28}
              className="h-5 w-auto opacity-60"
            />
          </div>
          <a
            href="/privacidade"
            target="_blank"
            rel="noopener noreferrer"
            className="text-zinc-500 text-sm hover:lia-text-900 dark:hover:lia-text-50 transition-colors motion-reduce:transition-none"
          >
            Política de Privacidade
          </a>
        </div>
      </footer>
    </div>
  )
}
