"use client"

import { useState, FormEvent } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { useJWTAuth } from "@/contexts/auth-context"
import Link from "next/link"
import Image from "next/image"
import {
  Eye, EyeOff, Mail, Lock, Loader2, AlertCircle, Pencil, Globe, Linkedin
} from "lucide-react"
import CloudsBackground from "@/components/clouds-background"

function getSafeRedirectUrl(next: string | null): string {
  if (!next) return "/login/welcome"
  if (next.startsWith("/") && !next.startsWith("//")) return next
  return "/login/welcome"
}

export default function LoginPage() {
  const router = useRouter()
  const { login, isLoading: authLoading } = useJWTAuth()

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
      setError("Insira um email válido.")
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
      router.push("/")
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Senha incorreta. Verifique suas credenciais.")
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
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Loader2 className="h-8 w-8 animate-spin text-gray-600 dark:text-gray-400" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex font-['Open_Sans',sans-serif] relative overflow-hidden">
      <CloudsBackground />

      <div className="hidden lg:flex lg:w-1/2 relative flex-col z-10">
        <div className="absolute top-10 left-[38px]" style={{ width: "230px" }}>
          <Image
            src="/logos/wedo-logo-transparent.png"
            alt="WeDo Talent"
            width={230}
            height={73}
            style={{ width: "230px", height: "auto", maxWidth: "230px" }}
            priority
          />
          <span
            className="block text-right text-gray-950 dark:text-lia-text-primary font-semibold uppercase tracking-[0.18em] text-[18px]"
            style={{ marginTop: "-5px", paddingRight: "6px" }}
          >
            talent
          </span>
        </div>

        <div className="flex-1 flex flex-col justify-center px-14 pr-10">
          <div className="mb-7">
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-wedo-cyan/40 bg-wedo-cyan/10 text-gray-700 dark:text-lia-text-secondary text-sm font-medium">
              <span className="text-wedo-cyan text-base leading-none">»</span>
              IA Agêntica para Recrutamento
            </span>
          </div>
          <h1 className="text-5xl text-gray-950 dark:text-lia-text-primary font-light leading-tight mb-7 font-['Open_Sans',sans-serif]">
            Entre. A <span className="font-['Source_Serif_4',serif] font-bold">LIA</span> já está<br />
            trabalhando por você.
          </h1>
          <p className="text-base text-gray-600 dark:text-lia-text-secondary font-normal leading-relaxed font-['Open_Sans',sans-serif]">
            Sourcing global&nbsp;·&nbsp;Triagem inteligente&nbsp;·&nbsp;Agendamentos automáticos<br />
            Recrutamento <span className="text-wedo-cyan font-semibold">simples</span>
          </p>
        </div>

        <div className="absolute bottom-0 left-0 pb-8 px-12">
          <div className="flex items-center gap-4 mb-1.5">
            <a
              href="https://www.wedotalent.cc"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 dark:text-lia-text-tertiary hover:text-gray-600 dark:hover:text-lia-text-secondary transition-colors"
              title="Website"
            >
              <Globe className="w-4 h-4" />
            </a>
            <a
              href="https://www.linkedin.com/company/wedotalent/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 dark:text-lia-text-tertiary hover:text-gray-600 dark:hover:text-lia-text-secondary transition-colors"
              title="LinkedIn"
            >
              <Linkedin className="w-4 h-4" />
            </a>
            <a
              href="mailto:tech@wedotalent.cc"
              className="text-gray-400 dark:text-lia-text-tertiary hover:text-gray-600 dark:hover:text-lia-text-secondary transition-colors"
              title="Contato"
            >
              <Mail className="w-4 h-4" />
            </a>
          </div>
          <p className="text-xs text-gray-400 dark:text-lia-text-tertiary">© 2025 <span className="font-['Source_Serif_4',serif] font-bold">LIA</span> by WeDoTalent</p>
        </div>

      </div>

      <div className="w-full lg:w-1/2 flex flex-col relative z-10">
        <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md bg-white/90 dark:bg-gray-800/90 backdrop-blur-md rounded-2xl shadow-2xl p-8 lg:p-10">

          <div className="lg:hidden flex items-center justify-center mb-8">
            <Image
              src="/logos/wedo-logo-transparent.png"
              alt="WeDo Talent"
              width={120}
              height={40}
              style={{ width: "auto", height: "auto" }}
              priority
            />
          </div>

          <div className="mb-6 text-center">
            <h2 className="text-xl font-semibold text-gray-950 dark:text-lia-text-primary">
              Entrar na plataforma
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
                <label htmlFor="login-email" className="block text-xs font-medium text-gray-800 dark:text-lia-text-secondary mb-1.5">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-lia-text-tertiary w-4 h-4" aria-hidden="true" />
                  <input
                    id="login-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-200 dark:border-lia-border-default rounded-xl bg-white dark:bg-lia-input-bg text-gray-950 dark:text-lia-input-text placeholder:text-gray-400 dark:placeholder:text-lia-input-placeholder focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-lia-input-focus-ring focus:border-gray-400 dark:focus:border-lia-input-border-focus transition-colors"
                    placeholder="seu@email.com"
                    required
                    autoFocus
                    autoComplete="email"
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full h-10 bg-gray-900 hover:bg-gray-800 dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover text-white dark:text-lia-btn-primary-text text-sm font-medium"
              >
                Entrar
              </Button>
            </form>
          )}

          {step === "password" && (
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div className="flex items-center justify-between px-3 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-lia-border-default rounded-xl">
                <div className="flex items-center gap-2 min-w-0">
                  <Mail className="w-4 h-4 text-gray-400 dark:text-lia-text-tertiary shrink-0" />
                  <span className="text-sm text-gray-700 dark:text-lia-text-secondary truncate">{email}</span>
                </div>
                <button
                  type="button"
                  onClick={handleBack}
                  className="flex items-center gap-1 text-xs text-gray-500 dark:text-lia-text-tertiary hover:text-gray-800 dark:hover:text-lia-text-primary transition-colors ml-2 shrink-0"
                >
                  <Pencil className="w-3 h-3" />
                  Alterar
                </button>
              </div>

              <div>
                <label htmlFor="login-password" className="block text-xs font-medium text-gray-800 dark:text-lia-text-secondary mb-1.5">
                  Senha
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-lia-text-tertiary w-4 h-4" aria-hidden="true" />
                  <input
                    id="login-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-10 py-2.5 text-sm border border-gray-200 dark:border-lia-border-default rounded-xl bg-white dark:bg-lia-input-bg text-gray-950 dark:text-lia-input-text placeholder:text-gray-400 dark:placeholder:text-lia-input-placeholder focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-lia-input-focus-ring focus:border-gray-400 dark:focus:border-lia-input-border-focus transition-colors"
                    placeholder="••••••••"
                    required
                    autoFocus
                    disabled={isSubmitting}
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-lia-text-tertiary hover:text-gray-600 dark:hover:text-lia-text-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan rounded-sm"
                    aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
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
                    className="rounded border-gray-300 dark:border-lia-border-default focus:ring-gray-900/20 dark:focus:ring-lia-input-focus-ring"
                  />
                  <span className="text-gray-600 dark:text-lia-text-secondary">Lembrar de mim</span>
                </label>
                <Link
                  href="/forgot-password"
                  className="text-gray-600 dark:text-lia-text-secondary hover:text-wedo-cyan font-medium transition-colors"
                >
                  Esqueceu a senha?
                </Link>
              </div>

              <Button
                type="submit"
                className="w-full h-10 bg-gray-900 hover:bg-gray-800 dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover text-white dark:text-lia-btn-primary-text text-sm font-medium"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Entrando...
                  </span>
                ) : (
                  "Confirmar"
                )}
              </Button>

              <div className="relative pt-1">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200 dark:border-lia-border-default" />
                </div>
                <div className="relative flex justify-center text-xs">
                  <span className="px-3 bg-white dark:bg-gray-800 text-gray-400 dark:text-lia-text-tertiary">ou</span>
                </div>
              </div>

              <Button
                type="button"
                variant="outline"
                className="w-full h-10 justify-start gap-3 bg-white dark:bg-lia-bg-secondary hover:bg-gray-50 dark:hover:bg-lia-bg-tertiary border-gray-200 dark:border-lia-border-default text-gray-800 dark:text-lia-text-primary text-sm font-normal"
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
                Continuar com Microsoft
              </Button>
            </form>
          )}

        </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 pb-8 px-12 text-gray-500 dark:text-lia-text-tertiary text-xs space-y-1 text-center flex flex-col items-center">
          <p className="max-w-md">
            A WeDoTalent é uma HRTech brasileira que desenvolve soluções avançadas de tecnologia para o RH do futuro.
          </p>
          <p className="max-w-md">© 2025 WeDoTalent. Todos os direitos reservados.</p>
        </div>
      </div>
    </div>
  )
}

export { getSafeRedirectUrl }
