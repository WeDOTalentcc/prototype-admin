"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { WeDOLogo } from "@/components/wedo-logo"
import { Loader2, CheckCircle, ArrowLeft, Mail } from "lucide-react"
import Link from "next/link"

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/backend-proxy/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || data.details?.detail || "Erro ao enviar email")
      }

      setSuccess(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err) || "Erro ao enviar email. Tente novamente.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 font-open-sans p-4">
      <div className="w-full max-w-md">
        <div className="bg-lia-bg-primary rounded-xl p-10">
          <div className="flex items-center justify-center mb-6">
            <div className="w-10 h-10 bg-black rounded-md flex items-center justify-center">
              <WeDOLogo className="h-5 text-white" />
            </div>
          </div>

          {success ? (
            <div className="text-center">
              <div className="w-16 h-16 bg-status-success/15 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-8 h-8 text-status-success" />
              </div>
              <h2 className="text-2xl font-bold lia-text-950 dark:lia-text-50 mb-3">Email Enviado!</h2>
              <p className="lia-text-600 mb-6">
                Se existe uma conta com o email <strong>{email}</strong>, você receberá um link para redefinir sua senha.
              </p>
              <p className="lia-text-500 text-sm mb-6">
                Verifique também sua pasta de spam caso não encontre o email.
              </p>
              <Link href="/login">
                <Button className="w-full py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-md">
                  Voltar para o Login
                </Button>
              </Link>
            </div>
          ) : (
            <>
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Mail className="w-8 h-8 lia-text-600" />
                </div>
                <h2 className="text-2xl font-bold lia-text-950 dark:lia-text-50 mb-3">Esqueceu a senha?</h2>
                <p className="lia-text-600 text-base leading-relaxed">
                  Digite seu email e enviaremos um link para você redefinir sua senha.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-sm font-medium lia-text-800 dark:text-lia-text-primary mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Digite seu email"
                    className="w-full px-4 py-3 border border-lia-border-subtle rounded-md focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-colors"
                    required
                  />
                </div>

                {error && (
                  <div className="p-3 rounded-md bg-status-error/10 border border-status-error/30">
                    <p className="text-status-error text-sm font-medium">{error}</p>
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-md transition-colors font-medium"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Enviando...
                    </>
                  ) : (
                    "Enviar Link de Recuperação"
                  )}
                </Button>

                <Link 
                  href="/login" 
                  className="flex items-center justify-center gap-2 lia-text-600 hover:lia-text-900 text-sm transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Voltar para o Login
                </Link>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
