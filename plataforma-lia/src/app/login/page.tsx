"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { useJWTAuth } from "@/contexts/auth-context"
import Link from "next/link"
import Image from "next/image"
import {
  Eye, EyeOff, Mail, Lock, Loader2, AlertCircle, Globe, Linkedin
} from "lucide-react"
import CloudsBackground from "@/components/clouds-background"

const emailStepSchema = z.object({
  email: z
    .string()
    .min(1, "E-mail é obrigatório")
    .email("Insira um email válido."),
})

const passwordStepSchema = z.object({
  password: z
    .string()
    .min(1, "Senha é obrigatória")
    .min(8, "Senha deve ter no mínimo 8 caracteres"),
})

type EmailStepData = z.infer<typeof emailStepSchema>
type PasswordStepData = z.infer<typeof passwordStepSchema>

export default function LoginPage() {
  const router = useRouter()
  const { login, isLoading: authLoading } = useJWTAuth()

  const [step, setStep] = useState<"email" | "password">("email")
  const [confirmedEmail, setConfirmedEmail] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [serverError, setServerError] = useState("")

  const emailForm = useForm<EmailStepData>({
    resolver: zodResolver(emailStepSchema),
  })

  const passwordForm = useForm<PasswordStepData>({
    resolver: zodResolver(passwordStepSchema),
  })

  const handleEmailStep = emailForm.handleSubmit((data) => {
    setServerError("")
    setConfirmedEmail(data.email)
    setStep("password")
  })

  const handlePasswordSubmit = passwordForm.handleSubmit(async (data) => {
    setServerError("")
    try {
      await login(confirmedEmail, data.password)
      router.push("/login/welcome")
    } catch (err: unknown) {
      setServerError(
        err instanceof Error
          ? err.message
          : String(err) || "Senha incorreta. Verifique suas credenciais."
      )
    }
  })

  const handleBack = () => {
    setStep("email")
    passwordForm.reset()
    setServerError("")
  }

  if (authLoading) {
    return (
      <div
        className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-lia-bg-primary"
        role="status"
        aria-live="polite"
        aria-label="Carregando..."
      >
        <Loader2 className="h-8 w-8 animate-spin motion-reduce:animate-none lia-text-600 dark:text-lia-text-tertiary" />
      </div>
    )
  }

  const emailErrors = emailForm.formState.errors
  const passwordErrors = passwordForm.formState.errors
  const isSubmittingPassword = passwordForm.formState.isSubmitting

  return (
    <div className="min-h-screen flex font-['Open_Sans',sans-serif] relative overflow-hidden">
      <CloudsBackground />

      {/* Left Section - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col z-10">
        <div className="absolute top-10 left-[38px]" style={{width: "230px"}}>
          <Image
            src="/logos/wedo-logo-transparent.png"
            alt="WeDo Talent"
            width={230}
            height={73}
            style={{width: "230px", height: "auto", maxWidth: "230px"}}
            priority
          />
          <span
            className="block text-right lia-text-950 font-semibold uppercase tracking-[0.18em] text-lg"
            style={{marginTop: "-5px", paddingRight: "6px"}}
          >
            talent
          </span>
        </div>

        <div className="flex-1 flex flex-col justify-center px-14 pr-10">
          <div className="mb-7">
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-wedo-cyan/40 bg-wedo-cyan/10 lia-text-700 text-sm font-medium">
              <span className="text-wedo-cyan text-base leading-none">»</span>
              IA Agêntica para Recrutamento
            </span>
          </div>
          <h1 className="text-5xl lia-text-950 font-light leading-tight mb-7 font-['Open_Sans',sans-serif]">
            Entre. A <span className="font-['Source_Serif_4',serif] font-bold">LIA</span> já está<br />
            trabalhando por você.
          </h1>
          <p className="text-base lia-text-500 font-light leading-relaxed font-['Open_Sans',sans-serif]">
            Sourcing global&nbsp;·&nbsp;Triagem inteligente&nbsp;·&nbsp;Agendamentos automáticos<br />
            Recrutamento <span className="text-wedo-cyan">simples</span>
          </p>
        </div>

        <div className="absolute bottom-0 left-0 pb-8 px-12">
          <div className="flex items-center gap-4 mb-1.5">
            <a href="https://www.wedotalent.cc" target="_blank" rel="noopener noreferrer" className="lia-text-400 hover:lia-text-600 transition-colors motion-reduce:transition-none" title="Website">
              <Globe className="w-4 h-4" />
            </a>
            <a href="https://www.linkedin.com/company/wedotalent/" target="_blank" rel="noopener noreferrer" className="lia-text-400 hover:lia-text-600 transition-colors motion-reduce:transition-none" title="LinkedIn">
              <Linkedin className="w-4 h-4" />
            </a>
            <a href="mailto:tech@wedotalent.cc" className="lia-text-400 hover:lia-text-600 transition-colors motion-reduce:transition-none" title="Contato">
              <Mail className="w-4 h-4" />
            </a>
          </div>
          <p className="text-xs lia-text-400">© 2025 <span className="font-['Source_Serif_4',serif] font-bold">LIA</span> by WeDoTalent</p>
        </div>
      </div>

      {/* Right Section - Card flutuante */}
      <div className="w-full lg:w-1/2 flex flex-col relative z-10">
        <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
          <div className="w-full max-w-md bg-white/90 dark:bg-lia-bg-secondary/90 backdrop-blur-md rounded-xl shadow-2xl p-8 lg:p-10">

            {/* Mobile Logo */}
            <div className="lg:hidden flex items-center justify-center mb-8">
              <Image src="/logos/wedo-logo-transparent.png" alt="WeDo Talent" width={120} height={40} style={{width: "auto", height: "auto"}} priority />
            </div>

            {/* Header */}
            <div className="mb-6 text-center">
              <h2 className="text-xl font-semibold lia-text-950">Entrar na plataforma</h2>
            </div>

            {/* Server Error */}
            {serverError && (
              <div className="mb-4 p-3 bg-status-error/10 border border-status-error/30 rounded-xl flex items-start gap-2" role="alert">
                <AlertCircle className="h-4 w-4 text-status-error mt-0.5 flex-shrink-0" aria-hidden="true" />
                <p className="text-xs text-status-error">{serverError}</p>
              </div>
            )}

            {/* ETAPA 1: EMAIL */}
            {step === "email" && (
              <form onSubmit={handleEmailStep} className="space-y-4" noValidate>
                <div>
                  <label htmlFor="email" className="block text-xs font-medium lia-text-800 mb-1.5">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 lia-text-400 w-4 h-4" aria-hidden="true" />
                    <input
                      id="email"
                      type="email"
                      {...emailForm.register("email")}
                      aria-invalid={!!emailErrors.email}
                      aria-describedby={emailErrors.email ? "email-error" : undefined}
                      className="w-full pl-9 pr-3 py-2.5 text-sm border border-lia-border-subtle rounded-xl bg-lia-bg-primary lia-text-950 placeholder:lia-text-400 focus:outline-none focus:ring-2 focus:ring-gray-900/20 focus:border-gray-400 transition-colors motion-reduce:transition-none"
                      placeholder="seu@email.com"
                      autoFocus
                    />
                  </div>
                  {emailErrors.email && (
                    <p id="email-error" role="alert" className="mt-1.5 text-xs text-status-error">
                      {emailErrors.email.message}
                    </p>
                  )}
                </div>
                <Button type="submit" className="w-full h-10 bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium">
                  Entrar
                </Button>
              </form>
            )}

            {/* ETAPA 2: SENHA */}
            {step === "password" && (
              <form onSubmit={handlePasswordSubmit} className="space-y-4" noValidate>
                {/* Email confirmado */}
                <div className="flex items-center justify-between p-3 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                  <div className="flex items-center gap-2 min-w-0">
                    <Mail className="h-4 w-4 lia-text-400 flex-shrink-0" aria-hidden="true" />
                    <span className="text-sm lia-text-700 truncate">{confirmedEmail}</span>
                  </div>
                  <button
                    type="button"
                    onClick={handleBack}
                    className="text-xs lia-text-500 hover:lia-text-900 transition-colors motion-reduce:transition-none ml-2 flex-shrink-0"
                    aria-label="Editar email"
                  >
                    Editar
                  </button>
                </div>

                {/* Senha */}
                <div>
                  <label htmlFor="password" className="block text-xs font-medium lia-text-800 mb-1.5">Senha</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 lia-text-400 w-4 h-4" aria-hidden="true" />
                    <input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      {...passwordForm.register("password")}
                      aria-invalid={!!passwordErrors.password}
                      aria-describedby={passwordErrors.password ? "password-error" : undefined}
                      className="w-full pl-9 pr-10 py-2.5 text-sm border border-lia-border-subtle rounded-xl bg-lia-bg-primary lia-text-950 placeholder:lia-text-400 focus:outline-none focus:ring-2 focus:ring-gray-900/20 focus:border-gray-400 transition-colors motion-reduce:transition-none"
                      placeholder="••••••••"
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 lia-text-400 hover:lia-text-700 transition-colors motion-reduce:transition-none"
                      aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" aria-hidden="true" /> : <Eye className="w-4 h-4" aria-hidden="true" />}
                    </button>
                  </div>
                  {passwordErrors.password && (
                    <p id="password-error" role="alert" className="mt-1.5 text-xs text-status-error">
                      {passwordErrors.password.message}
                    </p>
                  )}
                </div>

                {/* Lembrar / Esqueceu */}
                <div className="flex items-center justify-between text-xs">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="rounded-md border-lia-border-default focus:ring-gray-900/20"
                    />
                    <span className="lia-text-600">Lembrar de mim</span>
                  </label>
                  <Link href="/forgot-password" className="lia-text-600 hover:text-wedo-cyan font-medium transition-colors motion-reduce:transition-none">
                    Esqueceu a senha?
                  </Link>
                </div>

                <Button
                  type="submit"
                  className="w-full h-10 bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium"
                  disabled={isSubmittingPassword}
                >
                  {isSubmittingPassword ? (
                    <span className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                      Entrando...
                    </span>
                  ) : (
                    "Confirmar"
                  )}
                </Button>

                <div className="relative pt-1">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-lia-border-subtle" />
                  </div>
                  <div className="relative flex justify-center text-xs">
                    <span className="px-3 bg-lia-bg-primary lia-text-400">ou</span>
                  </div>
                </div>

                <Button
                  type="button"
                  variant="outline"
                  className="w-full h-10 justify-start gap-3 bg-lia-bg-primary hover:bg-gray-50 border-lia-border-subtle lia-text-800 text-sm font-normal"
                  onClick={() => {
                    window.location.href = `/api/auth/workos/sso?${confirmedEmail ? `email=${encodeURIComponent(confirmedEmail)}&` : ""}connection=conn_microsoft_entra`
                  }}
                  disabled={isSubmittingPassword}
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

        <div className="absolute bottom-0 left-0 right-0 pb-8 px-12 lia-text-500 text-xs space-y-1 text-center">
          <p>A WeDoTalent é uma HRTech brasileira que desenvolve soluções avançadas de tecnologia para o RH do futuro.</p>
          <p>© 2025 WeDoTalent. Todos os direitos reservados.</p>
        </div>
      </div>
    </div>
  )
}
