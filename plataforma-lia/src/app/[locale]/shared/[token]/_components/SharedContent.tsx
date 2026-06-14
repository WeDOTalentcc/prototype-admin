'use client'

import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Chip } from '@/components/ui/chip'
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
import type { useSharedToken } from '../_hooks/useSharedToken'

type SharedTokenReturn = ReturnType<typeof useSharedToken>

interface SharedContentProps {
  hook: SharedTokenReturn
}

export function SharedContent({ hook }: SharedContentProps) {
  const {
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
    sessionToken,
  } = hook

  if (loading) {
    return (
      <div className="min-h-screen bg-lia-bg-primary flex items-center justify-center" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="flex flex-col items-center gap-4" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary animate-spin motion-reduce:animate-none" />
          <p className="text-lia-text-tertiary">Carregando...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-lia-bg-primary flex items-center justify-center">
        <div className="bg-lia-btn-primary-bg rounded-xl p-8 max-w-md text-center border border-lia-border-strong">
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
      <div className="min-h-screen bg-lia-bg-primary flex items-center justify-center">
        <div className="bg-lia-btn-primary-bg rounded-xl p-8 max-w-md text-center border border-lia-border-strong">
          <Clock className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
          <h2 className="text-xl text-lia-text-on-inverse mb-2">Link Expirado</h2>
          <p className="text-lia-text-tertiary">
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
    <div className="min-h-screen bg-lia-bg-primary">
      <header className="sticky top-0 z-50 bg-lia-bg-primary/95 backdrop-blur-sm border-b border-lia-border-strong">
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

      <main id="main-content" className="max-w-6xl mx-auto px-4 py-8">
        <section className="mb-8">
          <h1 className="text-3xl font-semibold text-lia-text-on-inverse mb-2">
            Candidatos para sua avaliação
          </h1>
          {sharedData?.title && (
            <h2 className="text-xl text-lia-text-disabled mb-4">{sharedData.title}</h2>
          )}
          <div className="flex flex-wrap gap-4 text-sm text-lia-text-tertiary">
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
            <div className="mt-4 bg-lia-btn-primary-bg rounded-xl p-4 border border-lia-border-strong">
              <p className="text-lia-text-disabled italic">&quot;{sharedData.message}&quot;</p>
            </div>
          )}
        </section>

        {needsAuth && (
          <section className="mb-8">
            <div className="bg-lia-btn-primary-bg rounded-xl p-6 border border-lia-border-strong max-w-md mx-auto">
              <div className="flex items-center gap-3 mb-4">
                <Mail className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                <h3 className="text-lg font-medium text-lia-text-on-inverse">Acesso Necessário</h3>
              </div>
              <p className="text-lia-text-tertiary text-sm mb-4" aria-live="polite" aria-atomic="true">
                Para avaliar os candidatos, insira seu email para receber um código de acesso.
              </p>

              {!otpSent ? (
                <div className="space-y-4">
                  <Input
                    type="email"
                    placeholder="Seu email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="bg-lia-btn-primary-hover border-lia-border-strong text-lia-text-on-inverse placeholder:text-lia-text-secondary"
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
                  <p className="text-lia-text-disabled text-sm">
                    Enviamos um código para <strong>{email}</strong>
                  </p>
                  <Input
                    type="text"
                    placeholder="Código de 6 dígitos"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    maxLength={6}
                    className="bg-lia-btn-primary-hover border-lia-border-strong text-lia-text-on-inverse placeholder:text-lia-text-secondary text-center text-lg tracking-widest"
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
                    className="text-lia-text-tertiary text-sm hover:text-lia-text-muted w-full text-center"
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
              <div className="bg-lia-btn-primary-bg rounded-xl p-4 border border-lia-border-strong">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-lia-text-disabled text-sm">
                    {evaluatedCount}/{totalCount} avaliados
                  </span>
                  <span className="text-lia-text-secondary text-sm">
                    {Math.round((evaluatedCount / totalCount) * 100) || 0}%
                  </span>
                </div>
                <div className="w-full bg-lia-btn-primary-hover rounded-full h-2">
                  <div
                    className="bg-lia-btn-primary-bg dark:bg-lia-bg-secondary h-2 rounded-full transition-[width,height] duration-300"
                    style={{width: `${(evaluatedCount / totalCount) * 100 || 0}%`}}
                  />
                </div>
                <div className="flex gap-4 mt-4 text-sm">
                  <span className="flex items-center gap-1">
                    <span className="text-status-success">{counts.approved}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="text-status-warning">{counts.maybe}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="text-status-error">{counts.rejected}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="text-lia-text-tertiary">{counts.pending}</span>
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
                        : 'bg-lia-btn-primary-bg text-lia-text-tertiary hover:bg-lia-btn-primary-hover border border-lia-border-strong'
                    }`}
                  >
                    {label} ({count})
                  </button>
                ))}
              </div>
            </section>

            <section className="space-y-4">
              {filteredCandidates.length === 0 ? (
                <div className="bg-lia-btn-primary-bg rounded-xl p-8 text-center border border-lia-border-strong">
                  <p className="text-lia-text-tertiary" aria-live="polite" aria-atomic="true">Nenhum candidato encontrado para este filtro.</p>
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
                      className="bg-lia-btn-primary-bg rounded-xl border border-lia-border-strong overflow-hidden"
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
                            <div className="w-14 h-14 rounded-full bg-lia-btn-primary-hover flex items-center justify-center flex-shrink-0">
                              <User className="w-6 h-6 text-lia-text-secondary" />
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-4">
                              <div>
                                <h3 className="text-lg font-medium text-lia-text-on-inverse truncate">
                                  {candidate.name}
                                </h3>
                                {candidate.title && (
                                  <p className="text-lia-text-tertiary text-sm">{candidate.title}</p>
                                )}
                              </div>
                              {candidate.wsi_score !== undefined && (
                                <Chip variant="neutral" muted className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border-0 flex-shrink-0">
                                  WSI {candidate.wsi_score}
                                </Chip>
                              )}
                            </div>
                            <div className="flex flex-wrap gap-3 mt-2 text-sm text-lia-text-secondary">
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
                                  className="flex items-center gap-1 text-lia-text-tertiary hover:text-lia-text-muted transition-colors motion-reduce:transition-none"
                                >
                                  <FileText className="w-3.5 h-3.5" />
                                  Currículo
                                </a>
                              )}
                            </div>
                            {candidate.skills && candidate.skills.length > 0 && (
                              <div className="flex flex-wrap gap-1.5 mt-3">
                                {candidate.skills.slice(0, 5).map((skill) => (
                                  <Chip
                                    key={skill}
                                    variant="neutral" muted
                                    density="relaxed" className="text-lia-text-disabled border-0"
                                  >
                                    {skill}
                                  </Chip>
                                ))}
                                {candidate.skills.length > 5 && (
                                  <Chip
                                    variant="neutral" muted
                                    density="relaxed" className="text-lia-text-secondary border-0"
                                  >
                                    +{candidate.skills.length - 5}
                                  </Chip>
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
                          <div className="mt-4 pt-4 border-t border-lia-border-strong">
                            {candidate.summary && (
                              <div className="mb-4">
                                <h4 className="text-sm font-medium text-lia-text-tertiary mb-1">Resumo</h4>
                                <p className="text-lia-text-tertiary text-sm">{candidate.summary}</p>
                              </div>
                            )}
                            {candidate.education && (
                              <div className="mb-4">
                                <h4 className="text-sm font-medium text-lia-text-tertiary mb-1">Formação</h4>
                                <p className="text-lia-text-tertiary text-sm">{candidate.education}</p>
                              </div>
                            )}
                            {candidate.skills && candidate.skills.length > 5 && (
                              <div>
                                <h4 className="text-sm font-medium text-lia-text-tertiary mb-2">Todas as habilidades</h4>
                                <div className="flex flex-wrap gap-1.5">
                                  {candidate.skills.map((skill) => (
                                    <Chip
                                      key={skill}
                                      variant="neutral" muted
                                      density="relaxed" className="text-lia-text-disabled border-0"
                                    >
                                      {skill}
                                    </Chip>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="bg-lia-bg-primary p-4 border-t border-lia-border-strong">
                        {sharedData?.can_rate === false ? (
                          <div className="flex items-center gap-2 text-lia-text-secondary text-sm">
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
                                <span className="text-lia-text-secondary text-sm ml-2">
                                  • {feedback.comment}
                                </span>
                              )}
                            </div>
                            <button
                              onClick={() => updatePendingFeedback(candidate.id, feedback.rating)}
                              className="text-lia-text-secondary text-sm hover:text-lia-text-muted"
                            >
                              Editar
                            </button>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <div className="flex flex-wrap gap-2">
                              <Button
                                onClick={() => updatePendingFeedback(candidate.id, 'approved')}
                                variant={pending?.rating === 'approved' ? 'primary' : 'outline'}
                                size="sm"
                                className={
                                  pending?.rating === 'approved'
                                    ? 'bg-status-success hover:bg-status-success/10 text-lia-text-on-inverse border-0'
                                    : 'border-lia-border-strong text-lia-text-disabled hover:bg-lia-btn-primary-hover'
                                }
                              >
                                <ThumbsUp className="w-4 h-4 mr-1" />
                                Interessado
                              </Button>
                              <Button
                                onClick={() => updatePendingFeedback(candidate.id, 'maybe')}
                                variant={pending?.rating === 'maybe' ? 'primary' : 'outline'}
                                size="sm"
                                className={
                                  pending?.rating === 'maybe'
                                    ? 'bg-status-warning/10 hover:bg-status-warning/10 text-lia-text-on-inverse border-0'
                                    : 'border-lia-border-strong text-lia-text-disabled hover:bg-lia-btn-primary-hover'
                                }
                              >
                                <HelpCircle className="w-4 h-4 mr-1" />
                                Talvez
                              </Button>
                              <Button
                                onClick={() => updatePendingFeedback(candidate.id, 'rejected')}
                                variant={pending?.rating === 'rejected' ? 'primary' : 'outline'}
                                size="sm"
                                className={
                                  pending?.rating === 'rejected'
                                    ? 'bg-status-error hover:bg-status-error text-lia-text-on-inverse border-0'
                                    : 'border-lia-border-strong text-lia-text-disabled hover:bg-lia-btn-primary-hover'
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
                                    className="w-full bg-lia-btn-primary-hover border border-lia-border-strong rounded-md p-2 text-sm text-lia-text-on-inverse placeholder:text-lia-text-secondary resize-none focus:outline-none focus:border-lia-border-medium"
                                    rows={2}
                                  />
                                )}
                                <div className="flex justify-end gap-2">
                                  <Button
                                    onClick={() => clearPendingFeedback(candidate.id)}
                                    variant="ghost"
                                    size="sm"
                                    className="text-lia-text-tertiary hover:text-lia-text-muted"
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

      <footer className="border-t border-lia-border-strong mt-12">
        <div className="max-w-6xl mx-auto px-4 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-lia-text-secondary text-sm">
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
            className="text-lia-text-secondary text-sm hover:text-lia-text-primary dark:hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
          >
            Política de Privacidade
          </a>
        </div>
      </footer>
    </div>
  )
}
