"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { WeDOLogo } from "@/components/wedo-logo"
import { Eye, EyeOff, Loader2, CheckCircle, AlertCircle, UserPlus } from "lucide-react"
import Link from "next/link"

function AcceptInvitationContent() {
  const searchParams = useSearchParams()
  const token = searchParams.get("token")

  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingInfo, setIsLoadingInfo] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState(false)
  const [invitationInfo, setInvitationInfo] = useState<{
    email: string
    name: string
    company_name: string
  } | null>(null)

  useEffect(() => {
    const fetchInvitationInfo = async () => {
      if (!token) {
        setIsLoadingInfo(false)
        return
      }

      try {
        const response = await fetch(`/api/backend-proxy/auth/invitation-info/${token}`)
        if (!response.ok) {
          throw new Error("Token inválido ou expirado")
        }
        const data = await response.json()
        setInvitationInfo(data)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : String(err) || "Convite inválido ou expirado")
      } finally {
        setIsLoadingInfo(false)
      }
    }

    fetchInvitationInfo()
  }, [token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (password !== confirmPassword) {
      setError("As senhas não coincidem")
      return
    }

    if (password.length < 8) {
      setError("A senha deve ter pelo menos 8 caracteres")
      return
    }

    if (!token) {
      setError("Token inválido ou expirado")
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch("/api/backend-proxy/auth/accept-invitation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || data.details?.detail || "Erro ao aceitar convite")
      }

      setSuccess(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err) || "Erro ao aceitar convite. Tente novamente.")
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoadingInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary font-open-sans" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="text-center" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-secondary mx-auto mb-4" />
          <p className="text-lia-text-secondary">Carregando informações do convite...</p>
        </div>
      </div>
    )
  }

  if (!token || (!invitationInfo && !isLoadingInfo)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary font-open-sans p-4">
        <div className="w-full max-w-md bg-lia-bg-primary rounded-xl p-10 text-center">
          <div className="w-16 h-16 bg-status-error/15 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-8 h-8 text-status-error" />
          </div>
          <h2 className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-3">Convite Inválido</h2>
          <p className="text-lia-text-secondary mb-6">
            {error || "O link de convite é inválido ou expirou. Por favor, solicite um novo convite ao administrador."}
          </p>
          <Link href="/login">
            <Button className="w-full py-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text rounded-md">
              Ir para o Login
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary font-open-sans p-4">
        <div className="w-full max-w-md bg-lia-bg-primary rounded-xl p-10 text-center">
          <div className="w-16 h-16 bg-status-success/15 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-status-success" />
          </div>
          <h2 className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-3">Conta Ativada!</h2>
          <p className="text-lia-text-secondary mb-6">
            Sua conta foi ativada com sucesso. Agora você pode fazer login e começar a usar a plataforma.
          </p>
          <Link href="/login">
            <Button className="w-full py-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text rounded-md">
              Ir para o Login
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary font-open-sans p-4">
      <div className="w-full max-w-md">
        <div className="bg-lia-bg-primary rounded-xl p-10">
          <div className="flex items-center justify-center mb-6">
            <div className="w-10 h-10 bg-black rounded-md flex items-center justify-center">
              <WeDOLogo className="h-5 text-white" />
            </div>
          </div>

          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-full flex items-center justify-center mx-auto mb-4">
              <UserPlus className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <h2 className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary mb-3">Bem-vindo(a)!</h2>
            <p className="text-lia-text-secondary text-base leading-relaxed">
              Você foi convidado(a) para participar da plataforma WeDoTalent.
            </p>
            {invitationInfo && (
              <div className="mt-4 p-4 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
                <p className="text-sm text-lia-text-secondary">
                  <span className="font-medium text-lia-text-primary dark:text-lia-text-primary">{invitationInfo.name}</span>
                </p>
                <p className="text-sm text-lia-text-secondary">{invitationInfo.email}</p>
                <p className="text-xs text-lia-text-tertiary mt-1">
                  Empresa: {invitationInfo.company_name}
                </p>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                Criar Senha
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Mínimo 8 caracteres"
                  className="w-full px-4 py-3 pr-12 border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-lia-text-secondary hover:text-lia-text-primary"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                Confirmar Senha
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Digite a senha novamente"
                  className="w-full px-4 py-3 pr-12 border border-lia-border-subtle rounded-xl focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg focus:border-lia-btn-primary-bg transition-colors motion-reduce:transition-none"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-lia-text-secondary hover:text-lia-text-primary"
                >
                  {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-status-error/10 border border-status-error/30">
                <p className="text-status-error text-sm font-medium">{error}</p>
              </div>
            )}

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text rounded-md transition-colors motion-reduce:transition-none font-medium"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" />
                  Ativando conta...
                </>
              ) : (
                "Ativar Minha Conta"
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default function AcceptInvitationPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary font-open-sans" role="status" aria-live="polite" aria-label="Carregando...">
        <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
      </div>
    }>
      <AcceptInvitationContent />
    </Suspense>
  )
}
