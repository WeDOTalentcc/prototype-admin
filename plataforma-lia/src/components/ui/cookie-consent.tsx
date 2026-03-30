'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Cookie, X, Check } from 'lucide-react'

const CONSENT_KEY = 'lia-cookie-consent'

type ConsentState = 'accepted' | 'declined' | null

export function CookieConsent() {
  const [consent, setConsent] = useState<ConsentState>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem(CONSENT_KEY) as ConsentState
    if (!stored) {
      // Mostrar banner após 500ms (não bloquear renderização inicial)
      const timer = setTimeout(() => setVisible(true), 500)
      return () => clearTimeout(timer)
    }
    setConsent(stored)
  }, [])

  const handleAccept = () => {
    localStorage.setItem(CONSENT_KEY, 'accepted')
    setConsent('accepted')
    setVisible(false)
  }

  const handleDecline = () => {
    localStorage.setItem(CONSENT_KEY, 'declined')
    setConsent('declined')
    setVisible(false)
  }

  if (!visible || consent !== null) return null

  return (
    <div
      role="dialog"
      aria-label="Consentimento de cookies"
      aria-live="polite"
      className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6"
    >
      <div className="max-w-4xl mx-auto bg-lia-bg-elevated border border-lia-border-default rounded-xl shadow-lg p-5 flex flex-col md:flex-row items-start md:items-center gap-4">
        <div className="flex items-start gap-3 flex-1">
          <Cookie className="w-5 h-5 text-wedo-cyan shrink-0 mt-0.5" aria-hidden="true" />
          <div className="space-y-1">
            <p className="text-sm font-medium text-lia-text-primary">
              Preferências de cookies e privacidade
            </p>
            <p className="text-xs text-lia-text-secondary">
              Utilizamos cookies essenciais para o funcionamento da plataforma. Em conformidade com a{' '}
              <Link href="/politica-de-privacidade" className="underline hover:text-wedo-cyan">
                LGPD (Lei 13.709/2018)
              </Link>
              , você pode aceitar ou recusar cookies não essenciais.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleDecline}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-lia-text-secondary border border-lia-border-default rounded-lg hover:bg-lia-bg-tertiary transition-colors"
          >
            <X className="w-3.5 h-3.5" aria-hidden="true" />
            Recusar
          </button>
          <button
            onClick={handleAccept}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-wedo-cyan rounded-lg hover:bg-wedo-cyan-dark transition-colors"
          >
            <Check className="w-3.5 h-3.5" aria-hidden="true" />
            Aceitar
          </button>
        </div>
      </div>
    </div>
  )
}
