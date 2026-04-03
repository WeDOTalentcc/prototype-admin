"use client"

import { useState, useCallback, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useJWTAuth } from "@/contexts/auth-context"
import { loginSchema, type LoginFormData } from "@/lib/schemas/auth.schemas"
import { Button } from "@/components/ui/button"
import { WeDOLogo } from "@/components/wedo-logo"
import CloudsBackground from "@/components/clouds-background"
import {
  Eye,
  EyeOff,
  Loader2,
  Building2
} from "lucide-react"

interface SSOCheckResult {
  sso_available: boolean
  organization_id?: string
  company_name?: string
}

function getSafeRedirectUrl(next: string | null): string {
  if (!next) return "/admin/dashboard"
  if (next.startsWith("/") && !next.startsWith("//")) return next
  return "/admin/dashboard"
}

function LoginPageContent() {
  const searchParams = useSearchParams()
  const nextUrl = getSafeRedirectUrl(searchParams.get("next"))
  const reason = searchParams.get("reason")
  const router = useRouter()
  const { login, isLoading: authLoading } = useJWTAuth()

  const [showPassword, setShowPassword] = useState(false)
  const [ssoInfo, setSsoInfo] = useState<SSOCheckResult | null>(null)
  const [checkingSSO, setCheckingSSO] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
    watch,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const emailValue = watch("email")

  const checkSSODomain = useCallback(async (emailVal: string) => {
    if (!emailVal || !emailVal.includes("@")) {
      setSsoInfo(null)
      return
    }
    setCheckingSSO(true)
    try {
      const response = await fetch(`/api/backend-proxy/auth/check-sso-domain?email=${encodeURIComponent(emailVal)}`)
      if (response.ok) {
        const data: SSOCheckResult = await response.json()
        setSsoInfo(data)
      } else {
        setSsoInfo(null)
      }
    } catch {
      setSsoInfo(null)
    } finally {
      setCheckingSSO(false)
    }
  }, [])

  const handleEmailBlur = () => {
    if (emailValue) checkSSODomain(emailValue)
  }

  const handleSSOLogin = () => {
    if (ssoInfo?.organization_id) {
      window.location.href = `/api/auth/workos/sso?organization_id=${ssoInfo.organization_id}`
    }
  }

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password)
      router.push(nextUrl)
    } catch (err) {
      setError("root", {
        message: err instanceof Error ? err.message : "Credenciais inválidas. Tente novamente.",
      })
    }
  }

  return (
    <div
      data-testid="login-page"
      data-next={nextUrl}
      className="min-h-screen flex font-open-sans relative overflow-hidden"
    >
      <CloudsBackground />

      <div className="hidden lg:flex lg:w-3/5 flex-col justify-between p-12 relative">
        <div className="relative z-10 flex flex-col justify-center h-full">
          <div className="absolute top-0 left-0">
            <div className="flex items-center space-x-3">
              <WeDOLogo className="text-xl text-lia-text-primary" />
            </div>
          </div>

          <div className="max-w-2xl">
            <div className="mb-6">
              <h1 className="text-8xl font-bold text-lia-text-primary leading-none mb-4">
                Prazer, Lia
              </h1>
              <p className="text-2xl font-bold text-lia-text-primary leading-relaxed">
                Sua assistente de IA de recrutamento.
              </p>
            </div>

            <div className="space-y-3 mt-12">
              <p className="text-lg text-lia-text-secondary leading-relaxed">Automação inteligente, dados organizados e acessíveis, processos como nunca vistos antes.</p>
              <p className="text-lg text-lia-text-secondary leading-relaxed">IA nativa que aprende com você e acelera todo o processo de recrutamento.</p>
              <p className="text-lg text-lia-text-primary leading-relaxed font-semibold">Simples. Inteligente. Revolucionário.</p>
            </div>
          </div>
        </div>

        <div className="relative z-10">
          <div className="space-y-4">
            <p className="text-lia-text-primary text-sm">
              Empresas inovadoras que trabalham com a LIA.
            </p>
            <div className="flex items-center space-x-8">
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Sodexo_logo.svg/2560px-Sodexo_logo.svg.png"
                alt="Sodexo"
                className="h-8 object-contain opacity-60"
              />
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/ArcelorMittal.svg/2560px-ArcelorMittal.svg.png"
                alt="ArcelorMittal"
                className="h-8 object-contain opacity-60"
              />
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/8/8d/Celcoin.png"
                alt="Celcoin"
                className="h-8 object-contain opacity-60"
              />
              <img
                src="https://cdn.prod.website-files.com/6154ac78893abf1d1530f251/665dde0177b7a8e897170acd_Wellhub_Horizontal-Logo_Magenta.webp"
                alt="Wellhub"
                className="h-8 object-contain opacity-60"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="w-full lg:w-2/5 bg-lia-bg-primary flex flex-col shadow-2xl relative z-10">
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="w-full max-w-md p-10">
            <div className="text-center mb-6">
              <h2 className="text-3xl font-bold text-lia-text-primary mb-3">Bem-vindo(a)!</h2>
              <p className="text-lia-text-secondary text-base leading-relaxed">
                Informe suas credenciais para acessar a plataforma LIA.
              </p>
            </div>

            {reason === "session_expired" && (
              <div
                role="alert"
                className="mb-4 text-sm text-yellow-700 bg-yellow-50 border border-yellow-200 rounded-md p-3"
              >
                Sua sessão expirou por inatividade. Faça login novamente.
              </div>
            )}

            {errors.root && (
              <div role="alert" className="mb-4 p-3 rounded-md bg-status-error/10 border border-status-error/30">
                <p className="text-status-error text-sm font-medium">{errors.root.message}</p>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-lia-text-primary mb-2">
                  Email
                </label>
                <div className="relative">
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="Digite seu email"
                    className="w-full px-4 py-3 border border-lia-border-subtle rounded-md focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none"
                    {...register("email", { onBlur: handleEmailBlur })}
                  />
                  {checkingSSO && (
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2" role="status" aria-live="polite" aria-label="Carregando...">
                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-disabled" />
                    </div>
                  )}
                </div>
                {errors.email && (
                  <p role="alert" className="mt-1 text-xs text-status-error">{errors.email.message}</p>
                )}
              </div>

              {ssoInfo?.sso_available && (
                <div className="p-4 rounded-md bg-lia-bg-tertiary border border-lia-border-default">
                  <div className="flex items-start gap-3">
                    <Building2 className="w-5 h-5 text-lia-text-secondary mt-0.5" />
                    <div className="flex-1">
                      <p className="text-wedo-cyan-dark text-sm font-medium">
                        SSO Corporativo Detectado
                      </p>
                      <p className="text-lia-text-secondary text-xs mt-1">
                        {ssoInfo.company_name ? `Sua empresa (${ssoInfo.company_name}) utiliza login corporativo.` : "Sua empresa utiliza login corporativo."}
                      </p>
                    </div>
                  </div>
                  <Button
                    type="button"
                    onClick={handleSSOLogin}
                    className="w-full mt-3 py-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text rounded-md transition-colors motion-reduce:transition-none font-medium flex items-center justify-center gap-2"
                  >
                    <Building2 className="w-4 h-4" />
                    Entrar com SSO Corporativo
                  </Button>
                </div>
              )}

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-lia-text-primary mb-2">
                  Senha
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    placeholder="Digite sua senha"
                    className="w-full px-4 py-3 pr-12 border border-lia-border-subtle rounded-md focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none"
                    {...register("password")}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-lia-text-secondary hover:text-lia-text-primary"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {errors.password && (
                  <p role="alert" className="mt-1 text-xs text-status-error">{errors.password.message}</p>
                )}
              </div>

              <div className="flex items-center justify-between">
                <span />
                <a href="/forgot-password" className="text-sm text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none">
                  Esqueceu a senha?
                </a>
              </div>

              <Button
                type="submit"
                disabled={isSubmitting || authLoading}
                className="w-full py-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text rounded-md transition-colors motion-reduce:transition-none font-medium"
              >
                {isSubmitting || authLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" />
                    Entrando...
                  </>
                ) : (
                  "Entrar"
                )}
              </Button>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-lia-border-subtle"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-lia-bg-primary text-lia-text-secondary">Ou continue com:</span>
                </div>
              </div>

              <div className="space-y-3">
                <Button
                  type="button"
                  variant="outline"
                  className="w-full py-3 border border-lia-border-subtle hover:border-lia-border-default rounded-md transition-colors motion-reduce:transition-none flex items-center justify-center gap-3 bg-lia-bg-primary font-medium"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Continuar com Google
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  className="w-full py-3 border border-lia-border-subtle hover:border-lia-border-default rounded-md transition-colors motion-reduce:transition-none flex items-center justify-center gap-3 bg-lia-bg-primary font-medium"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24">
                    <path fill="#F25022" d="M1 1h10.5v10.5H1z"/>
                    <path fill="#00A4EF" d="M12.5 1H23v10.5H12.5z"/>
                    <path fill="#7FBA00" d="M1 12.5h10.5V23H1z"/>
                    <path fill="#FFB900" d="M12.5 12.5H23V23H12.5z"/>
                  </svg>
                  Continuar com Microsoft
                </Button>
              </div>
            </form>
          </div>
        </div>

        <div className="p-4 text-center text-xs text-lia-text-secondary space-y-1">
          <p>
            Tecnologia avançada para Recursos Humanos do futuro.
            <br />
            Desenvolvida pela WeDOTalent, HRTech do Grupo Talentese.
          </p>
          <p>&copy; 2024 WeDOTalent. Todos os direitos reservados.</p>
        </div>
      </div>

      <div className="lg:hidden w-full bg-transparent absolute inset-0 flex flex-col items-center justify-center p-6 z-10">
        <div className="bg-lia-bg-primary rounded-xl p-8 w-full max-w-md shadow-2xl">
          <div className="text-center mb-5">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <WeDOLogo className="text-xl text-lia-text-primary" />
            </div>
            <h2 className="text-2xl font-bold text-lia-text-primary mb-3">Bem-vindo(a)!</h2>
            <p className="text-lia-text-secondary text-base leading-relaxed">
              Acesse a plataforma LIA com suas credenciais.
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-2">Email</label>
              <input
                type="email"
                autoComplete="email"
                placeholder="Digite seu email"
                className="w-full px-4 py-3 border border-lia-border-subtle rounded-md focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg transition-colors"
                {...register("email")}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-lia-text-primary mb-2">Senha</label>
              <input
                type="password"
                autoComplete="current-password"
                placeholder="Digite sua senha"
                className="w-full px-4 py-3 border border-lia-border-subtle rounded-md focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg transition-colors"
                {...register("password")}
              />
            </div>

            {errors.root && (
              <div role="alert" className="p-3 rounded-md bg-status-error/10 border border-status-error/30">
                <p className="text-status-error text-sm">{errors.root.message}</p>
              </div>
            )}

            <Button
              type="submit"
              disabled={isSubmitting || authLoading}
              className="w-full py-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text rounded-md font-medium"
            >
              {isSubmitting || authLoading ? "Entrando..." : "Entrar"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginPageContent />
    </Suspense>
  )
}

export { getSafeRedirectUrl }
