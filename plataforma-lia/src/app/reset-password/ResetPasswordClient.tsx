"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { WeDOLogo } from "@/components/wedo-logo"
import { Eye, EyeOff, Loader2, CheckCircle, AlertCircle, KeyRound } from "lucide-react"
import Link from "next/link"

function ResetPasswordContent() {
  const searchParams = useSearchParams()
  const token = searchParams.get("token")

  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState(false)

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
      const response = await fetch("/api/backend-proxy/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || data.details?.detail || "Erro ao redefinir senha")
      }

      setSuccess(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err) || "Erro ao redefinir senha. Tente novamente.")
    } finally {
      setIsLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white font-open-sans p-4">
        <div className="w-full max-w-md bg-lia-bg-primary rounded-xl p-10 text-center">
          <div className="w-16 h-16 bg-status-error/15 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-8 h-8 text-status-error" />
          </div>
          <h2 className="text-2xl font-bold lia-text-950 dark:lia-text-50 mb-3">Link Inválido</h2>
          <p className="lia-text-600 mb-6">
            O link de redefinição de senha é inválido ou expirou. Por favor, solicite um novo link.
          </p>
          <Link href="/forgot-password">
            <Button className="w-full py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-md">
              Solicitar Novo Link
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white font-open-sans p-4">
        <div className="w-full max-w-md bg-lia-bg-primary rounded-xl p-10 text-center">
          <div className="w-16 h-16 bg-status-success/15 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-status-success" />
          </div>
          <h2 className="text-2xl font-bold lia-text-950 dark:lia-text-50 mb-3">Senha Redefinida!</h2>
          <p className="lia-text-600 mb-6">
            Sua senha foi alterada com sucesso. Agora você pode fazer login com sua nova senha.
          </p>
          <Link href="/login">
            <Button className="w-full py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-md">
              Ir para o Login
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-white font-open-sans p-4">
      <div className="w-full max-w-md">
        <div className="bg-lia-bg-primary rounded-xl p-10">
          <div className="flex items-center justify-center mb-6">
            <div className="w-10 h-10 bg-black rounded-md flex items-center justify-center">
              <WeDOLogo className="h-5 text-white" />
            </div>
          </div>

          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <KeyRound className="w-8 h-8 lia-text-600" aria-hidden="true" />
            </div>
            <h2 className="text-2xl font-bold lia-text-950 dark:lia-text-50 mb-3">Nova Senha</h2>
            <p className="lia-text-600 text-base leading-relaxed">
              Digite sua nova senha abaixo.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5" aria-label="Formulário de redefinição de senha">
            <div>
              <label htmlFor="campo-nova-senha" className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-2">
                Nova Senha
              </label>
              <div className="relative">
                <input
                  id="campo-nova-senha"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Mínimo 8 caracteres"
                  className="w-full px-4 py-3 pr-12 border border-lia-border-subtle rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-colors motion-reduce:transition-none"
                  required
                  aria-required="true"
                  aria-describedby={error ? "reset-error" : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 lia-text-600 hover:lia-text-700"
                  aria-label={showPassword ? "Ocultar nova senha" : "Mostrar nova senha"}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="campo-confirmar-senha" className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-2">
                Confirmar Nova Senha
              </label>
              <div className="relative">
                <input
                  id="campo-confirmar-senha"
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Digite a senha novamente"
                  className="w-full px-4 py-3 pr-12 border border-lia-border-subtle rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-colors motion-reduce:transition-none"
                  required
                  aria-required="true"
                  aria-describedby={error ? "reset-error" : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 lia-text-600 hover:lia-text-700"
                  aria-label={showConfirmPassword ? "Ocultar confirmação de senha" : "Mostrar confirmação de senha"}
                >
                  {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {error && (
              <div id="reset-error" role="alert" className="p-3 rounded-md bg-status-error/10 border border-status-error/30">
                <p className="text-status-error text-sm font-medium">
                  <span aria-hidden="true">⚠ </span>
                  {error}
                </p>
              </div>
            )}

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-md transition-colors motion-reduce:transition-none font-medium"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mr-2" aria-hidden="true" />
                  Redefinindo...
                </>
              ) : (
                "Redefinir Senha"
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-white font-open-sans" role="status" aria-live="polite" aria-label="Carregando...">
        <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none lia-text-600" />
      </div>
    }>
      <ResetPasswordContent />
    </Suspense>
  )
}
