"use client"

/**
 * InterviewLobby — pre-triagem consent + channel selection screen.
 *
 * Implements Phase 1a LGPD Consent spec (2026-06-11):
 * - Scroll-to-enable consent checkbox
 * - 4 channel cards in 2 groups (async / sync)
 * - LGPD plain-language AI declaration
 * - Mic permission check before voice/phone channels
 * - logConsent() called BEFORE starting any channel (fail-closed RN-04)
 * - Affirmative action second consent block
 * - Expiry banner when < 24h remaining
 *
 * Rules of Hooks: ALL hooks declared before any conditional return.
 */

import React, { useCallback, useRef, useState } from "react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { AlertTriangle, MessageSquare, Mic, Phone } from "lucide-react"
import type { InterviewInfo } from "@/types/interview"
import {
  useAudioConsentLog,
  DISCLAIMER_VERSION,
} from "@/hooks/interview/useAudioConsentLog"

export interface InterviewLobbyProps {
  /** Session token — used by useAudioConsentLog. */
  token: string
  /** InterviewInfo from the backend (GET /triagem/{token}). */
  info: InterviewInfo
  /** Called when candidate picks the "chat web" channel. */
  onStartMessage: () => void
  /** Called when candidate picks the WhatsApp channel. */
  onStartWhatsapp: () => void
  /** Called when candidate picks the online call (voice-in-browser) channel. */
  onStartOnlineCall: () => void
  /** Called when candidate picks the phone call channel. */
  onStartPhone: () => void
  className?: string
}

// ── Scroll-to-enable threshold (px tolerance) ──────────────────────────────
const SCROLL_TOLERANCE = 10

// ── Disclaimer text (canonical — bump DISCLAIMER_VERSION on any change) ────────
// SPEC-CONSENT-AUDIO-v1.1 §4.1 — texto aprovado pelo DPO em 11/06/2026
// v1.1: somente voz (sem câmera/vídeo); \"triagem\" em vez de \"entrevista\"
const DISCLAIMER_FULL = `Ao marcar esta opção, você consente, de forma livre e expressa, com a gravação da sua voz durante esta triagem de pré-seleção, conduzida pela WeDOTalent (Talenses Recrutamento Especializado).

A gravação destina-se exclusivamente à transcrição e análise do conteúdo das suas respostas para fins de seleção — não será utilizada para reconhecimento biométrico ou qualquer outra finalidade.

Seus dados serão armazenados por até 12 meses e, após esse prazo, serão excluídos automaticamente.

Você pode, a qualquer momento, solicitar revisão humana da avaliação, acesso, correção ou exclusão dos seus dados pelo e-mail privacidadededados@wedotalent.cc.

Para mais informações, acesse nossa Política de Privacidade em wedotalent.cc/privacidade.`


// ── Mic permission helper ───────────────────────────────────────────────────
async function requestMicPermission(): Promise<boolean> {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    stream.getTracks().forEach((t) => t.stop())
    return true
  } catch {
    return false
  }
}

// ── Sub-components ──────────────────────────────────────────────────────────

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-xs font-semibold uppercase tracking-wide text-lia-text-tertiary mb-3">
      {children}
    </h2>
  )
}

interface ChannelCardProps {
  icon: React.ReactNode
  label: string
  description: string
  disabled: boolean
  badge?: string
  onClick: () => void
}

function ChannelCard({
  icon,
  label,
  description,
  disabled,
  badge,
  onClick,
}: ChannelCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "w-full flex items-start gap-3 p-4 rounded-lg border text-left transition-colors",
        "border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary",
        "hover:bg-lia-interactive-hover hover:border-lia-border-default",
        "focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        "motion-reduce:transition-none",
      )}
    >
      <span className="flex-shrink-0 w-9 h-9 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated flex items-center justify-center text-lia-text-secondary">
        {icon}
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-lia-text-primary">{label}</span>
          {badge && (
            <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-status-warning/15 text-status-warning">
              <AlertTriangle className="w-3 h-3" />
              {badge}
            </span>
          )}
        </div>
        <p className="text-xs text-lia-text-secondary mt-0.5 leading-relaxed">
          {description}
        </p>
      </div>
    </button>
  )
}

// ── Main component ──────────────────────────────────────────────────────────

export function InterviewLobby({
  token,
  info,
  onStartMessage,
  onStartWhatsapp,
  onStartOnlineCall,
  onStartPhone,
  className,
}: InterviewLobbyProps) {
  const t = useTranslations("interview.lobby")
  const { logConsent } = useAudioConsentLog(token)

  // ── All hooks at top — Rules of Hooks ───────────────────────────────────
  const [consentChecked, setConsentChecked] = useState(false)
  const [scrolledToBottom, setScrolledToBottom] = useState(false)
  const [affirmativeChecked, setAffirmativeChecked] = useState(false)
  const [consentError, setConsentError] = useState<string | null>(null)
  const [micDenied, setMicDenied] = useState(false)
  const disclaimerRef = useRef<HTMLDivElement>(null)

  // Scroll-to-enable listener
  const handleDisclaimerScroll = useCallback(() => {
    const el = disclaimerRef.current
    if (!el) return
    const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - SCROLL_TOLERANCE
    if (atBottom) setScrolledToBottom(true)
  }, [])

  // Consent gate — wraps every channel handler
  const withConsent = useCallback(
    async (
      canal: "chat_web" | "whatsapp" | "chamada_online" | "chamada_telefonica",
      proceed: () => void,
    ) => {
      setConsentError(null)
      try {
        await logConsent(canal)
        proceed()
      } catch (err: unknown) {
        setConsentError(
          err instanceof Error ? err.message : t("consentError"),
        )
      }
    },
    [logConsent, t],
  )

  // Mic-check wrapper for voice/phone channels
  const withMicCheck = useCallback(
    async (proceed: () => void) => {
      setMicDenied(false)
      const granted = await requestMicPermission()
      if (!granted) {
        setMicDenied(true)
        return
      }
      proceed()
    },
    [],
  )

  // ── Computed state ──────────────────────────────────────────────────────
  const allConsentGranted =
    consentChecked &&
    scrolledToBottom &&
    (!info.is_affirmative || affirmativeChecked)

  const isExpiringSoon =
    !!info.expires_at &&
    new Date(info.expires_at) < new Date(Date.now() + 24 * 60 * 60 * 1000)

  // ── Handlers ────────────────────────────────────────────────────────────
  const handleMessage = useCallback(() => {
    void withConsent("chat_web", onStartMessage)
  }, [withConsent, onStartMessage])

  const handleWhatsapp = useCallback(() => {
    void withMicCheck(() => {
      void withConsent("whatsapp", onStartWhatsapp)
    })
  }, [withMicCheck, withConsent, onStartWhatsapp])

  const handleOnlineCall = useCallback(() => {
    void withMicCheck(() => {
      void withConsent("chamada_online", onStartOnlineCall)
    })
  }, [withMicCheck, withConsent, onStartOnlineCall])

  const handlePhone = useCallback(() => {
    void withMicCheck(() => {
      void withConsent("chamada_telefonica", onStartPhone)
    })
  }, [withMicCheck, withConsent, onStartPhone])

  const aiName = info.ai_name || "Lia"

  return (
    <div
      className={cn(
        "min-h-screen bg-lia-bg-secondary dark:bg-lia-bg-primary flex flex-col items-center px-4 py-8",
        className,
      )}
    >
      <div className="w-full max-w-md space-y-6">

        {/* ── Expiry banner ──────────────────────────────────────────── */}
        {isExpiringSoon && (
          <div
            role="alert"
            className="flex items-center gap-2 px-4 py-3 rounded-lg bg-status-warning/15 border border-status-warning/30 text-status-warning text-xs font-medium"
          >
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            {t("expiryWarning")}
          </div>
        )}

        {/* ── Header ─────────────────────────────────────────────────── */}
        <div className="text-center space-y-2">
          {info.company_logo_url ? (
            <img
              src={info.company_logo_url}
              alt={t("logoAlt", { name: info.company_name })}
              className="h-10 object-contain mx-auto mb-2"
            />
          ) : (
            <div className="inline-flex h-10 px-4 items-center justify-center bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-lg mb-2">
              <span className="text-sm font-semibold text-lia-text-secondary">
                {info.company_name}
              </span>
            </div>
          )}
          <h1 className="text-lg font-semibold text-lia-text-primary">
            {info.job_title}
          </h1>
          <p className="text-sm text-lia-text-secondary">
            {t("greeting", { name: info.candidate_name })}
          </p>
        </div>

        {/* ── AI Declaration ─────────────────────────────────────────── */}
        <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary p-4 space-y-1">
          <p className="text-xs font-semibold text-lia-text-primary">
            {t("aiDeclarationTitle", { aiName })}
          </p>
          <p className="text-xs text-lia-text-secondary leading-relaxed">
            {t("aiDeclarationBody")}
          </p>
        </div>

        {/* ── Practice question hint ─────────────────────────────────── */}
        {info.has_practice_question && (
          <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-tertiary dark:bg-lia-bg-elevated px-4 py-3">
            <p className="text-xs text-lia-text-secondary">
              {t("practiceQuestionHint")}
            </p>
          </div>
        )}

        {/* ── Preparation tips ──────────────────────────────────────── */}
        <div>
          <SectionHeading>{t("tipsTitle")}</SectionHeading>
          <ul className="space-y-2">
            {([t("tip1"), t("tip2"), t("tip3")] as string[]).map((tip, i) => (
              <li
                key={tip}
                className="flex items-start gap-2 text-xs text-lia-text-secondary leading-relaxed"
              >
                <span className="flex-shrink-0 w-4 h-4 rounded-full bg-lia-btn-primary-bg/10 text-lia-btn-primary-bg flex items-center justify-center text-[10px] font-bold mt-0.5">
                  {i + 1}
                </span>
                {tip}
              </li>
            ))}
          </ul>
        </div>

        {/* ── Consent section ────────────────────────────────────────── */}
        <div>
          <SectionHeading>{t("consentTitle")}</SectionHeading>

          {/* Scrollable disclaimer — scroll-to-enable */}
          <div
            ref={disclaimerRef}
            onScroll={handleDisclaimerScroll}
            role="region"
            aria-label={t("disclaimerAriaLabel")}
            className={cn(
              "h-40 overflow-y-auto rounded-lg border p-4 text-xs text-lia-text-secondary leading-relaxed whitespace-pre-wrap",
              scrolledToBottom
                ? "border-lia-border-default"
                : "border-lia-border-subtle",
            )}
          >
            {DISCLAIMER_FULL}
            <div className="mt-2 text-[10px] text-lia-text-tertiary">
              {t("disclaimerVersion", { version: DISCLAIMER_VERSION })}
            </div>
          </div>

          {!scrolledToBottom && (
            <p className="mt-1.5 text-[11px] text-lia-text-tertiary text-center">
              {t("scrollToEnable")}
            </p>
          )}

          {/* Consent checkbox */}
          <label
            className="flex items-start gap-3 mt-4 cursor-pointer group"
            htmlFor="lgpd-consent-main"
          >
            <Checkbox
              id="lgpd-consent-main"
              checked={consentChecked}
              onCheckedChange={(v) => setConsentChecked(!!v)}
              disabled={!scrolledToBottom}
              className="mt-0.5"
            />
            <span className="text-xs text-lia-text-secondary leading-relaxed select-none">
              {t("consentCheckboxLabel")}{" "}
              <a
                href={info.privacy_policy_url}
                target="_blank"
                rel="noopener noreferrer"
                className="underline text-lia-text-primary hover:text-lia-btn-primary-bg transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                {t("privacyPolicyLink")}
              </a>
              .
            </span>
          </label>
        </div>

        {/* ── Affirmative action second consent ─────────────────────── */}
        {info.is_affirmative && (
          <div className="rounded-lg border border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary p-4 space-y-3">
            <p className="text-xs font-semibold text-lia-text-primary">
              {t("affirmativeTitle", {
                type: info.affirmative_type ?? t("affirmativeGeneric"),
              })}
            </p>
            <p className="text-xs text-lia-text-secondary leading-relaxed">
              {t("affirmativeBody")}
            </p>
            <label
              className="flex items-start gap-3 cursor-pointer"
              htmlFor="lgpd-consent-affirmative"
            >
              <Checkbox
                id="lgpd-consent-affirmative"
                checked={affirmativeChecked}
                onCheckedChange={(v) => setAffirmativeChecked(!!v)}
                disabled={!consentChecked}
                className="mt-0.5"
              />
              <span className="text-xs text-lia-text-secondary leading-relaxed select-none">
                {t("affirmativeCheckboxLabel")}
              </span>
            </label>
          </div>
        )}

        {/* ── Error feedback ─────────────────────────────────────────── */}
        {consentError && (
          <div
            role="alert"
            className="flex items-center gap-2 px-4 py-3 rounded-lg bg-status-error/10 border border-status-error/30 text-status-error text-xs"
          >
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            {consentError}
          </div>
        )}

        {micDenied && (
          <div
            role="alert"
            className="flex items-center gap-2 px-4 py-3 rounded-lg bg-status-warning/10 border border-status-warning/30 text-status-warning text-xs"
          >
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            {t("micDenied")}
          </div>
        )}

        {/* ── Channel cards ──────────────────────────────────────────── */}
        <div className="space-y-4">
          {/* Group 1: Async */}
          <div>
            <SectionHeading>{t("groupAsync")}</SectionHeading>
            <div className="space-y-2">
              <ChannelCard
                icon={<MessageSquare className="w-4 h-4" />}
                label={t("channelChatLabel")}
                description={t("channelChatDesc")}
                disabled={!allConsentGranted}
                onClick={handleMessage}
              />
              <ChannelCard
                icon={
                  <span className="text-[18px] leading-none" aria-hidden="true">
                    📱
                  </span>
                }
                label={t("channelWhatsappLabel")}
                description={t("channelWhatsappDesc")}
                disabled={!allConsentGranted}
                onClick={handleWhatsapp}
              />
            </div>
          </div>

          {/* Group 2: Sync */}
          <div>
            <SectionHeading>{t("groupSync")}</SectionHeading>
            <div className="space-y-2">
              <ChannelCard
                icon={<Mic className="w-4 h-4" />}
                label={t("channelOnlineCallLabel")}
                description={t("channelOnlineCallDesc")}
                badge={t("syncBadge")}
                disabled={!allConsentGranted}
                onClick={handleOnlineCall}
              />
              <ChannelCard
                icon={<Phone className="w-4 h-4" />}
                label={t("channelPhoneLabel")}
                description={t("channelPhoneDesc")}
                badge={t("syncBadge")}
                disabled={!allConsentGranted}
                onClick={handlePhone}
              />
            </div>
          </div>
        </div>

        {/* ── Footer ─────────────────────────────────────────────────── */}
        {info.show_wedotalent_branding !== false && (
          <footer className="text-center pt-2">
            <p className="text-[11px] text-lia-text-disabled">
              Powered by WeDOTalent
            </p>
          </footer>
        )}
      </div>
    </div>
  )
}
