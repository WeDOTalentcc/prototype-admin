"use client"

import { useSearchParams, useRouter } from "next/navigation"
import { Suspense } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useJWTAuth } from "@/contexts/auth-context"
import { loginSchema, type LoginFormData } from "@/lib/schemas/auth.schemas"

/**
 * Valida o parametro ?next= para evitar open redirect.
 * So permite redirects relativos (comecam com / mas nao com //).
 */
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

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

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
      className="min-h-screen flex items-center justify-center bg-gray-50 p-4"
    >
      <div className="w-full max-w-md bg-white rounded-lg shadow p-8 space-y-6">
        <h1 className="text-2xl font-semibold text-center text-gray-900">
          Entrar na plataforma
        </h1>

        {reason === "session_expired" && (
          <div
            role="alert"
            className="text-sm text-yellow-700 bg-yellow-50 border border-yellow-200 rounded p-3"
          >
            Sua sessao expirou por inatividade. Faca login novamente.
          </div>
        )}

        {errors.root && (
          <div role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3">
            {errors.root.message}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              E-mail
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              {...register("email")}
            />
            {errors.email && (
              <p role="alert" className="mt-1 text-xs text-red-600">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Senha
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              {...register("password")}
            />
            {errors.password && (
              <p role="alert" className="mt-1 text-xs text-red-600">{errors.password.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting || authLoading}
            className="w-full bg-blue-600 text-white rounded-md py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? "Entrando..." : "Entrar"}
          </button>
        </form>
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
