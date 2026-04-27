"use client"

import React, { useState } from "react"
import { useLocale } from "next-intl"
import { cn } from "@/lib/utils"
import { LIAIcon } from "@/components/ui/lia-icon"
import { Clock, Shield, CheckSquare, Square, MapPin, Briefcase, DollarSign, Gift, Phone } from "lucide-react"
import type { TriagemConfig } from "@/components/triagem/types"

interface WelcomeCardProps {
  config: TriagemConfig
  onStart: (voiceMode?: boolean) => void
  onRequestCall?: () => void
  /** Task #425 — opens phone confirm modal in WhatsApp mode (shared form). */
  onRequestWhatsapp?: () => void
  isStarting?: boolean
  className?: string
}

function formatSalary(range: { min?: number; max?: number; currency?: string }, isEn: boolean): string {
  const currency = range.currency || (isEn ? "USD" : "BRL")
  const intlLocale = isEn ? "en-US" : "pt-BR"
  const fmt = (v: number) =>
    v.toLocaleString(intlLocale, { style: "currency", currency, minimumFractionDigits: 0, maximumFractionDigits: 0 })
  if (range.min && range.max) return `${fmt(range.min)} - ${fmt(range.max)}`
  if (range.min) return isEn ? `From ${fmt(range.min)}` : `A partir de ${fmt(range.min)}`
  if (range.max) return isEn ? `Up to ${fmt(range.max)}` : `Até ${fmt(range.max)}`
  return ""
}

const WORK_MODEL_LABELS_PT: Record<string, string> = {
  remoto: "Remoto",
  "híbrido": "Híbrido",
  presencial: "Presencial",
}

const WORK_MODEL_LABELS_EN: Record<string, string> = {
  remoto: "Remote",
  "híbrido": "Hybrid",
  presencial: "On-site",
}

export function WelcomeCard({ config, onStart, onRequestCall, onRequestWhatsapp, isStarting = false, className }: WelcomeCardProps) {
  const locale = useLocale()
  const isEn = locale === "en"
  const [consentChecked, setConsentChecked] = useState(false)

  const t = isEn
    ? {
        logoAlt: (name: string) => `${name} logo`,
        greeting: (name: string) => `Hi ${name}, I'm LIA.`,
        defaultWelcome:
          "I'll guide you through your screening for this role. The conversation will cover your experience and skills in an objective way.",
        estimatedTime: "Estimated time:",
        minutes: "minutes",
        consentText: "I agree to the processing of my personal data for the purposes of this screening, in line with the",
        privacyPolicyLink: "Privacy Policy",
        consentSuffix: "and applicable data protection laws.",
        noChannels:
          "This screening doesn't have any contact channel enabled. Please ask the recruiter to review the configuration.",
        chatStarting: "Starting...",
        chatStart: "Start Chat Conversation",
        chatStartAria: "Start chat screening conversation",
        whatsapp: "Continue on WhatsApp",
        whatsappAria: "Continue the screening on WhatsApp",
        phone: "Receive an Automated Call",
        phoneAria: "Request an automated phone call",
        voice: "Voice in Browser",
        voiceAria: "Start voice conversation in the browser",
        privacyFooter: "Privacy Policy",
        privacyFooterAria: "Privacy policy",
      }
    : {
        logoAlt: (name: string) => `Logo ${name}`,
        greeting: (name: string) => `Olá, ${name}. Eu sou a LIA.`,
        defaultWelcome:
          "Vou conduzir sua triagem para esta vaga. A conversa abordará sua experiência e habilidades de forma objetiva.",
        estimatedTime: "Tempo estimado:",
        minutes: "minutos",
        consentText: "Concordo com o tratamento dos meus dados pessoais para fins desta triagem, conforme a",
        privacyPolicyLink: "Política de Privacidade",
        consentSuffix: "e a Lei Geral de Proteção de Dados (LGPD).",
        noChannels:
          "Esta triagem não tem nenhum canal de contato habilitado. Por favor, peça ao recrutador para revisar a configuração.",
        chatStarting: "Iniciando...",
        chatStart: "Iniciar Conversa por Chat",
        chatStartAria: "Iniciar conversa de triagem por chat",
        whatsapp: "Continuar pelo WhatsApp",
        whatsappAria: "Continuar a triagem pelo WhatsApp",
        phone: "Receber Ligação Automática",
        phoneAria: "Solicitar ligação telefônica automática",
        voice: "Voz no Navegador",
        voiceAria: "Iniciar conversa por voz no navegador",
        privacyFooter: "Política de Privacidade",
        privacyFooterAria: "Política de privacidade",
      }

  const workModelLabels = isEn ? WORK_MODEL_LABELS_EN : WORK_MODEL_LABELS_PT

  const hasJobDetails = config.jobDescription || config.location || config.workModel
  const hasSalary = config.showSalary && config.salaryRange && (config.salaryRange.min || config.salaryRange.max)
  const hasBenefits = config.showBenefits && config.benefits && config.benefits.length > 0

  return (
    <div
      className={cn(
        "flex-1 flex items-center justify-center px-4 py-8",
        className
      )}
    >
      <div className="w-full max-w-md bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl shadow-lia-sm p-6 space-y-5">
        <div className="flex flex-col items-center gap-4 text-center">
          {config.companyLogoUrl ? (
            <img
              src={config.companyLogoUrl}
              alt={t.logoAlt(config.companyName)}
              className="h-12 object-contain"
            />
          ) : (
            <div className="h-12 px-4 flex items-center justify-center bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-lg">
              <span className="text-sm font-semibold text-lia-text-secondary">
                {config.companyName}
              </span>
            </div>
          )}

          <h1 className="text-lg font-semibold text-lia-text-primary">
            {config.jobTitle}
          </h1>
        </div>

        {hasJobDetails && (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-lia-text-tertiary">
            {config.location && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
                {config.location}
              </span>
            )}
            {config.workModel && (
              <span className="flex items-center gap-1">
                <Briefcase className="w-3.5 h-3.5 flex-shrink-0" />
                {workModelLabels[config.workModel] || config.workModel}
              </span>
            )}
          </div>
        )}

        {config.jobDescription && (
          <p className="text-sm text-lia-text-secondary leading-relaxed line-clamp-4">
            {config.jobDescription}
          </p>
        )}

        {(hasSalary || hasBenefits) && (
          <div className="space-y-2">
            {hasSalary && config.salaryRange && (
              <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
                <DollarSign className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{formatSalary(config.salaryRange, isEn)}</span>
              </div>
            )}
            {hasBenefits && config.benefits && (
              <div className="flex items-start gap-2 text-xs text-lia-text-tertiary">
                <Gift className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                <span>{config.benefits.join(" · ")}</span>
              </div>
            )}
          </div>
        )}

        <div className="flex items-start gap-3 p-4 bg-wedo-cyan/10 dark:bg-wedo-cyan/15 rounded-lg">
          <LIAIcon size="sm" className="flex-shrink-0 bg-wedo-cyan/10" />
          <div className="text-sm text-lia-text-secondary leading-relaxed">
            <p className="font-semibold text-lia-text-primary mb-1">
              {t.greeting(config.candidateName)}
            </p>
            <p>{config.welcomeMessage || t.defaultWelcome}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
          <Clock className="w-3.5 h-3.5" />
          <span>
            {t.estimatedTime}{" "}
            <span className="font-['Inter',sans-serif] font-medium">~{config.estimatedMinutes}</span> {t.minutes}
          </span>
        </div>

        <label
          className="flex items-start gap-3 cursor-pointer group"
          htmlFor="lgpd-consent"
        >
          <button
            type="button"
            id="lgpd-consent"
            role="checkbox"
            aria-checked={consentChecked}
            onClick={() => setConsentChecked(!consentChecked)}
            className="mt-0.5 flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 rounded"
          >
            {consentChecked ? (
              <CheckSquare className="w-5 h-5 text-lia-btn-primary-bg" />
            ) : (
              <Square className="w-5 h-5 text-lia-text-tertiary group-hover:text-lia-text-secondary transition-colors" />
            )}
          </button>
          <span className="text-xs text-lia-text-secondary leading-relaxed select-none">
            {t.consentText}{" "}
            <a
              href={config.privacyPolicyUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="underline text-lia-text-primary hover:text-wedo-cyan transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              {t.privacyPolicyLink}
            </a>{" "}
            {t.consentSuffix}
          </span>
        </label>

        {/* Task #425: candidate channel selector — render only enabled channels.
            Default true preserves backward-compat for legacy configs without
            channel flags; phoneEnabled and voiceWebEnabled default false to
            avoid silently surfacing unconfigured PSTN/voz_web. */}
        {(() => {
          const chatWebOn = config.chatWebEnabled !== false
          const whatsappOn = config.whatsappEnabled !== false
          const phoneOn = !!config.phoneEnabled
          const voiceWebOn = !!config.voiceWebEnabled
          const noChannels = !chatWebOn && !whatsappOn && !phoneOn && !voiceWebOn
          if (noChannels) {
            return (
              <div className="rounded-lg border border-status-error/30 bg-status-error/10 p-3 text-xs text-status-error">
                {t.noChannels}
              </div>
            )
          }
          return (
            <div className="space-y-2">
              {chatWebOn && (
                <button
                  type="button"
                  onClick={() => onStart(false)}
                  disabled={isStarting || !consentChecked}
                  aria-label={t.chatStartAria}
                  className="w-full h-11 flex items-center justify-center rounded-lg bg-lia-btn-primary-bg text-lia-btn-primary-text text-sm font-medium hover:bg-lia-btn-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none"
                >
                  {isStarting ? t.chatStarting : t.chatStart}
                </button>
              )}
              {whatsappOn && onRequestWhatsapp && (
                <button
                  type="button"
                  onClick={onRequestWhatsapp}
                  disabled={isStarting || !consentChecked}
                  aria-label={t.whatsappAria}
                  className="w-full h-11 flex items-center justify-center gap-2 rounded-lg border border-lia-border-subtle text-lia-text-primary text-sm font-medium hover:bg-lia-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none"
                >
                  {t.whatsapp}
                </button>
              )}
              {phoneOn && onRequestCall && (
                <button
                  type="button"
                  onClick={onRequestCall}
                  disabled={isStarting || !consentChecked}
                  aria-label={t.phoneAria}
                  className="w-full h-11 flex items-center justify-center gap-2 rounded-lg border border-lia-border-subtle text-lia-text-primary text-sm font-medium hover:bg-lia-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none"
                >
                  <Phone className="w-4 h-4" />
                  {t.phone}
                </button>
              )}
              {voiceWebOn && (
                <button
                  type="button"
                  onClick={() => onStart(true)}
                  disabled={isStarting || !consentChecked}
                  aria-label={t.voiceAria}
                  className="w-full h-11 flex items-center justify-center gap-2 rounded-lg border border-lia-border-subtle text-lia-text-primary text-sm font-medium hover:bg-lia-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 focus:outline-none"
                >
                  <Phone className="w-4 h-4" />
                  {t.voice}
                </button>
              )}
            </div>
          )
        })()}

        <a
          href={config.privacyPolicyUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-1.5 text-xs text-lia-text-disabled hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
          aria-label={t.privacyFooterAria}
        >
          <Shield className="w-3 h-3" />
          {t.privacyFooter}
        </a>
      </div>
    </div>
  )
}
