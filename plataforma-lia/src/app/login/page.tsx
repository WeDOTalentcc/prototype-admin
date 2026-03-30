"use client"

import { useSearchParams } from "next/navigation"
import { Suspense } from "react"

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

  return (
    <div data-testid="login-page" data-next={nextUrl}>
      {reason === "session_expired" && (
        <div role="alert" className="text-sm text-yellow-700 bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
          Sua sessao expirou por inatividade. Faca login novamente.
        </div>
      )}
      {/* TODO: inserir o formulario de login aqui e usar nextUrl no router.push pos-login */}
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
