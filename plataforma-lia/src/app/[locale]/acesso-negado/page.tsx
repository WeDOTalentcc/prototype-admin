"use client"

/**
 * /[locale]/acesso-negado/page.tsx
 *
 * Onda 4-P0-Fase7 (2026-05-24): rota canonical pra denial de acesso.
 *
 * Histórico: onboarding-controller.tsx:135 (handleAccessDenied) faz
 * `window.location.href = "/acesso-negado"` mas a rota nunca foi criada
 * (mesmo padrão Task #712 bug). Descoberto via sensor
 * check_no_broken_window_location.py.
 *
 * Trigger: usuário tenta acessar área restrita (e.g. onboarding sem
 * permissão prévia). Em vez de 404 (UX horrível), mostra mensagem clara
 * + ação (voltar ao login).
 */

import { useRouter } from "next/navigation"
import { Lock } from "lucide-react"

export default function AcessoNegadoPage() {
  const router = useRouter()

  return (
    <main className="min-h-screen flex items-center justify-center bg-lia-bg-primary p-6">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="w-16 h-16 mx-auto rounded-full bg-amber-500/10 flex items-center justify-center">
          <Lock className="w-8 h-8 text-amber-600" />
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-semibold text-lia-text-primary">
            Acesso negado
          </h1>
          <p className="text-sm text-lia-text-secondary">
            Você não tem permissão para acessar esta área. Se acredita
            que isso é um erro, entre em contato com o administrador da
            sua empresa ou faça login com outra conta.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-2 justify-center">
          <button
            onClick={() => router.push("/login")}
            className="px-4 py-2 rounded-md bg-wedo-cyan text-white text-sm font-medium hover:bg-wedo-cyan/90 transition-colors"
          >
            Voltar ao login
          </button>
          <button
            onClick={() => router.push("/")}
            className="px-4 py-2 rounded-md border border-lia-border-subtle text-sm font-medium text-lia-text-primary hover:bg-lia-bg-secondary transition-colors"
          >
            Página inicial
          </button>
        </div>
      </div>
    </main>
  )
}
