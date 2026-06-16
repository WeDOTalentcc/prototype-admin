"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { WeDOLogo } from "@/components/wedo-logo"
import { Loader2, CheckCircle, AlertCircle, Mail } from "lucide-react"
import Link from "next/link"

function VerifyEmailContent() {
  const searchParams = useSearchParams()
  const token = searchParams.get("token")

  const [isLoading, setIsLoading] = useState(true)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!token) {
      setError("Link inválido ou expirado.")
      setIsLoading(false)
      return
    }

    const verify = async () => {
      try {
        const response = await fetch("/api/backend-proxy/auth/verify-email", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        })

        if (!response.ok) {
          const data = await response.json()
          throw new Error(
            data.error || data.details?.detail || "Erro ao verificar email"
          )
        }

        setSuccess(true)
      } catch (err: unknown) {
        setError(
          err instanceof Error
            ? err.message
            : "Erro ao verificar email. Tente novamente."
        )
      } finally {
        setIsLoading(false)
      }
    }

    verify()
  }, [token])

  if (isLoading) {
    return (
      <div
        className="min-h-screen flex items-center justify-center bg-lia-bg-primary font-open-sans p-4"
        role="status"
        aria-live="polite"
        aria-label="Verificando email..."
      >
        <div className="w-full max-w-md bg-lia-bg-primary rounded-xl p-10 text-center">
          <div className="w-16 h-16 bg-lia-bg-tertiary rounded-full flex items-center justify-center mx-auto mb-6">
            <Loader2
              className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-secondary"
              aria-hidden="true"
            />
          </div>
          <h2 className="text-2xl font-semibold text-lia-text-primary mb-3">
            Verificando...
          </h2>
          <p className="text-lia-text-secondary">
            Aguarde enquanto confirmamos seu email.
          </p>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-lia-bg-primary font-open-sans p-4">
        <div className="w-full max-w-md bg-lia-bg-primary rounded-xl p-10 text-center">
          <div className="flex items-center justify-center mb-6">
            <div className="w-10 h-10 bg-black rounded-md flex items-center justify-center">
              <WeDOLogo className="h-5 text-white" />
            </div>
          </div>
          <div className="w-16 h-16 bg-status-success/15 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-status-success" aria-hidden="true" />
          </div>
          <h2 className="text-2xl font-semibold text-lia-text-primary mb-3">
            Email verificado!
          </h2>
          <p className="text-lia-text-secondary mb-6">
            Sua conta foi ativada com sucesso. Agora você pode acessar a
            plataforma.
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
      <div className="w-full max-w-md bg-lia-bg-primary rounded-xl p-10 text-center">
        <div className="flex items-center justify-center mb-6">
          <div className="w-10 h-10 bg-black rounded-md flex items-center justify-center">
            <WeDOLogo className="h-5 text-white" />
          </div>
        </div>
        <div className="w-16 h-16 bg-status-error/15 rounded-full flex items-center justify-center mx-auto mb-6">
          <AlertCircle className="w-8 h-8 text-status-error" aria-hidden="true" />
        </div>
        <h2 className="text-2xl font-semibold text-lia-text-primary mb-3">
          Verificação falhou
        </h2>
        <p className="text-lia-text-secondary mb-6">{error}</p>
        <div className="space-y-3">
          <Link href="/login">
            <Button className="w-full py-3 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text rounded-md">
              Ir para o Login
            </Button>
          </Link>
          <p className="text-sm text-lia-text-secondary">
            Não recebeu o email?{" "}
            <Link
              href="/login"
              className="text-lia-btn-primary-bg hover:underline font-medium"
            >
              Reenviar verificação
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div
          className="min-h-screen flex items-center justify-center bg-lia-bg-primary font-open-sans"
          role="status"
          aria-live="polite"
          aria-label="Carregando..."
        >
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
        </div>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  )
}
