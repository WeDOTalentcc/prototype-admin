"use client"

import { useState, useEffect, FormEvent } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { useJWTAuth } from "@/contexts/auth-context"
import Link from "next/link"
import Image from "next/image"
import {
  Eye, EyeOff, Mail, Lock, Loader2, AlertCircle, Pencil, Globe, Linkedin
} from "lucide-react"
import CloudsBackground from "@/components/clouds-background"
import { useTranslations } from 'next-intl'

function getSafeRedirectUrl(next: string | null): string {
  if (!next) return "/login/welcome"
  if (next.startsWith("/") && !next.startsWith("//")) return next
  return "/login/welcome"
}

export default function LoginPage() {
  const router = useRouter()
  const { login, isLoading: authLoading, isAuthenticated } = useJWTAuth()
  const t = useTranslations('login')

  useEffect(() => {
    // If the user is already signed in by the time auth bootstrap settles,
    // skip the form and go straight to the app. We rely on the authoritative
    // store state (set after initAuth → getMe succeeds), not on raw cookie
    // sniffing — stale `lia_auth_method` cookies (e.g. expired SSO with
    // `_sso_session_` placeholder, or an invalid JWT) would otherwise trigger
    // the same /login ↔ / redirect loop that motivated this fix.
    //
    // History: the previous heuristic checked for the absence of
    // `lia_logged_out=1` and was dev-only. With LIA_DEV_AUTO_LOGIN off
    // (default since the 2026-04-29 wizard-domain-hint-leak audit) the
    // logout marker is never set on a fresh session, so the dev branch
    // bounced /login → / forever.
    if (!authLoading && isAuthenticated) {
      router.replace('/')
    }
  }, [authLoading, isAuthenticated, router])

  const [step, setStep] = useState<"email" | "password">("email")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [error, setError] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleEmailStep = (e: FormEvent) => {
    e.preventDefault()
    setError("")
    if (!email || !email.includes("@") || !email.includes(".")) {
      setError(t("invalidEmail"))
      return
    }
    setStep("password")
  }

  const handlePasswordSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")
    setIsSubmitting(true)
    try {
      await login(email, password)
      router.push(getSafeRedirectUrl(null))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("wrongPassword"))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleBack = () => {
    setStep("email")
    setPassword("")
    setError("")
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-secondary dark:bg-lia-bg-inverse">
        <Loader2 className="h-8 w-8 animate-spin text-lia-text-secondary dark:text-lia-text-tertiary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex relative overflow-hidden">
      <CloudsBackground />

      <div className="hidden lg:flex lg:w-1/2 relative flex-col z-10">
        <div className="absolute top-10 left-[38px] w-[230px]">
          <Image
            src="/logos/wedo-logo-transparent.png"
            alt="WeDo Talent"
            width={230}
            height={73}
            className="w-[230px] h-auto max-w-[230px]"
            style={{ height: 'auto' }}
            priority
          />
          <span
            className="block text-right text-lia-text-primary dark:text-lia-text-primary font-semibold uppercase tracking-[0.18em] text-[18px] -mt-[5px] pr-[6px]"
          >
            talent
          </span>
        </div>

        <div className="flex-1 flex flex-col justify-center px-14 pr-10">
          <div className="mb-7">
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-wedo-cyan/40 bg-wedo-cyan/10 text-lia-text-secondary dark:text-lia-text-secondary text-sm font-medium">
              <span className="text-lia-text-muted text-base leading-none">»</span>
              {t("tagline")}
            </span>
          </div>
          <h1 className="text-5xl text-lia-text-primary dark:text-lia-text-primary font-light leading-tight mb-7">
            {t.rich("heroTitle", {
              bold: (chunks) => <span className="font-['Source_Serif_4',serif] font-bold">{chunks}</span>,
              br: () => <br />,
            })}
          </h1>
          <p className="text-base text-lia-text-secondary dark:text-lia-text-secondary font-normal leading-relaxed">
            {t("heroSubtitle")}<br />
            {t.rich("heroRecruitment", {
              accent: (chunks) => <span className="text-lia-text-secondary font-semibold">{chunks}</span>,
            })}
          </p>
          <p className="mt-5 text-[13px] text-lia-text-tertiary dark:text-lia-text-tertiary tracking-wide border-l-2 border-wedo-cyan/50 pl-3">
            <span className="font-bold">{t("atsConnect")}</span>&nbsp;&nbsp;·&nbsp;&nbsp;{t("atsOrFull")}
          </p>
        </div>

        <div className="absolute bottom-0 left-0 pb-8 px-12">
          <div className="flex items-center gap-4 mb-1.5">
            <a
              href="https://www.wedotalent.cc"
              target="_blank"
              rel="noopener noreferrer"
              className="text-lia-text-tertiary dark:text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-secondary transition-colors"
              title={t("websiteLink")}
            >
              <Globe className="w-4 h-4" />
            </a>
            <a
              href="https://www.linkedin.com/company/wedotalent/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-lia-text-tertiary dark:text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-secondary transition-colors"
              title={t("linkedinLink")}
            >
              <Linkedin className="w-4 h-4" />
            </a>
            <a
              href="mailto:tech@wedotalent.cc"
              className="text-lia-text-tertiary dark:text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-secondary transition-colors"
              title={t("emailLabel")}
            >
              <Mail className="w-4 h-4" />
            </a>
          </div>
          <p className="text-xs text-lia-text-tertiary dark:text-lia-text-tertiary">{t("copyrightShort")}</p>
        </div>

      </div>

      <div className="w-full lg:w-1/2 flex flex-col relative z-10">
        <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md bg-white/90 dark:bg-lia-bg-inverse/90 backdrop-blur-md rounded-xl shadow-2xl p-8 lg:p-10">

          <div className="lg:hidden flex items-center justify-center mb-8">
            <Image
              src="/logos/wedo-logo-transparent.png"
              alt="WeDo Talent"
              width={120}
              height={40}
              className="w-auto h-auto"
              priority
            />
          </div>

          <div className="mb-6 text-center">
            <h2 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary">
              {t("enterPlatform")}
            </h2>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-status-error-bg border border-red-100 dark:border-status-error-border rounded-xl flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-red-500 dark:text-status-error mt-0.5 flex-shrink-0" />
              <p className="text-xs text-red-600 dark:text-status-error">{error}</p>
            </div>
          )}

          {step === "email" && (
            <form onSubmit={handleEmailStep} className="space-y-4">
              <div>
                <label htmlFor="login-email" className="block text-xs font-medium text-lia-text-primary dark:text-lia-text-secondary mb-1.5">
                  {t("emailLabel")}
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-lia-text-tertiary dark:text-lia-text-tertiary w-4 h-4" aria-hidden="true" />
                  <input
                    id="login-email"
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value)
                      if (error) setError("")
                    }}
                    className="w-full pl-9 pr-3 py-2.5 text-sm border border-lia-border-subtle dark:border-lia-border-default rounded-xl bg-white dark:bg-lia-input-bg text-lia-text-primary dark:text-lia-input-text placeholder:text-lia-text-tertiary dark:placeholder:text-lia-input-placeholder focus:outline-none focus:ring-2 focus:ring-lia-text-primary/20 dark:focus:ring-lia-input-focus-ring focus:border-lia-border-strong dark:focus:border-lia-input-border-focus transition-colors"
                    placeholder={t("emailPlaceholder")}
                    required
                    autoFocus
                    autoComplete="email"
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full h-10 bg-lia-bg-inverse hover:bg-lia-bg-inverse dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover text-white dark:text-lia-btn-primary-text text-sm font-medium"
              >
                {t("enterButton")}
              </Button>
            </form>
          )}

          {step === "password" && (
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div className="flex items-center justify-between px-3 py-2.5 bg-lia-bg-secondary dark:bg-lia-bg-inverse border border-lia-border-subtle dark:border-lia-border-default rounded-xl">
                <div className="flex items-center gap-2 min-w-0">
                  <Mail className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-tertiary shrink-0" />
                  <span className="text-sm text-lia-text-secondary dark:text-lia-text-secondary truncate">{email}</span>
                </div>
                <button
                  type="button"
                  onClick={handleBack}
                  className="flex items-center gap-1 text-xs text-lia-text-tertiary dark:text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-primary transition-colors ml-2 shrink-0"
                >
                  <Pencil className="w-3 h-3" />
                  {t("changeEmail")}
                </button>
              </div>

              <div>
                <label htmlFor="login-password" className="block text-xs font-medium text-lia-text-primary dark:text-lia-text-secondary mb-1.5">
                  {t("passwordLabel")}
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-lia-text-tertiary dark:text-lia-text-tertiary w-4 h-4" aria-hidden="true" />
                  <input
                    id="login-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value)
                      if (error) setError("")
                    }}
                    className="w-full pl-9 pr-10 py-2.5 text-sm border border-lia-border-subtle dark:border-lia-border-default rounded-xl bg-white dark:bg-lia-input-bg text-lia-text-primary dark:text-lia-input-text placeholder:text-lia-text-tertiary dark:placeholder:text-lia-input-placeholder focus:outline-none focus:ring-2 focus:ring-lia-text-primary/20 dark:focus:ring-lia-input-focus-ring focus:border-lia-border-strong dark:focus:border-lia-input-border-focus transition-colors"
                    placeholder={t("passwordPlaceholder")}
                    required
                    autoFocus
                    disabled={isSubmitting}
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-lia-text-tertiary dark:text-lia-text-tertiary hover:text-lia-text-secondary dark:hover:text-lia-text-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan rounded-sm"
                    aria-label={showPassword ? t("hidePassword") : t("showPassword")}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" aria-hidden="true" /> : <Eye className="w-4 h-4" aria-hidden="true" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="rounded border-lia-border-default dark:border-lia-border-default focus:ring-lia-text-primary/20 dark:focus:ring-lia-input-focus-ring"
                  />
                  <span className="text-lia-text-secondary dark:text-lia-text-secondary">{t("rememberMe")}</span>
                </label>
                <Link
                  href="/forgot-password"
                  className="text-lia-text-secondary dark:text-lia-text-secondary hover:text-wedo-cyan font-medium transition-colors"
                >
                  {t("forgotPassword")}
                </Link>
              </div>

              <Button
                type="submit"
                className="w-full h-10 bg-lia-bg-inverse hover:bg-lia-bg-inverse dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover text-white dark:text-lia-btn-primary-text text-sm font-medium"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    {t("submitting")}
                  </span>
                ) : (
                  t("confirmButton")
                )}
              </Button>

              <div className="relative pt-1">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-lia-border-subtle dark:border-lia-border-default" />
                </div>
                <div className="relative flex justify-center text-xs">
                  <span className="px-3 bg-white dark:bg-lia-bg-inverse text-lia-text-tertiary dark:text-lia-text-tertiary">{t("orDivider")}</span>
                </div>
              </div>

              <Button
                type="button"
                variant="outline"
                className="w-full h-10 justify-start gap-3 bg-white dark:bg-lia-bg-secondary hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-tertiary border-lia-border-subtle dark:border-lia-border-default text-lia-text-primary dark:text-lia-text-primary text-sm font-normal"
                onClick={() => {
                  window.location.href = `/api/auth/workos/sso?${email ? `email=${encodeURIComponent(email)}&` : ""}connection=conn_microsoft_entra`
                }}
                disabled={isSubmitting}
              >
                <svg width="16" height="16" viewBox="0 0 21 21" className="shrink-0" aria-hidden="true">
                  <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
                  <rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>
                  <rect x="1" y="11" width="9" height="9" fill="#00A4EF"/>
                  <rect x="11" y="11" width="9" height="9" fill="#FFB900"/>
                </svg>
                {t("continueWithMicrosoft")}
              </Button>
            </form>
          )}

        </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 pb-8 px-12 text-lia-text-tertiary dark:text-lia-text-tertiary text-xs space-y-1 text-center flex flex-col items-center">
          <p className="max-w-md">
            {t("companyDescription")}
          </p>
          <p className="max-w-md">{t("copyright")}</p>
        </div>
      </div>
    </div>
  )
}

export { getSafeRedirectUrl }
